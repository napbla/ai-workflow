#!/usr/bin/env python3
"""Verify that GitHub protects the ai-workflow integration branches.

GitHub branch protection or rulesets are the authoritative enforcement of the
protected branch policy. This tool only reads repository-host state; it never
changes settings and never inspects local commands.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

PROTECTED_BRANCHES = ("main", "develop")
DEFAULT_API_URL = "https://api.github.com"
TOKEN_ENV_VARS = ("GH_TOKEN", "GITHUB_TOKEN")

PULL_REQUEST = "pull request required"
NO_FORCE_PUSH = "force pushes blocked"
NO_DELETION = "deletion blocked"
REQUIREMENTS = (PULL_REQUEST, NO_FORCE_PUSH, NO_DELETION)

# `pull_requests_only` still forces changes through a PR, so only these count as a bypass.
BYPASS_ALWAYS = {"always", "exempt"}
RULESET_RULES = {"pull_request": PULL_REQUEST, "non_fast_forward": NO_FORCE_PUSH, "deletion": NO_DELETION}

PROTECTED, UNPROTECTED, UNVERIFIABLE = "protected", "not protected", "unverifiable"
EXIT_CODES = {PROTECTED: 0, UNPROTECTED: 1, UNVERIFIABLE: 2}

REMEDIATION = """\
HUMAN SETUP BLOCKER: repository-host protection for `main` and `develop` is missing or unverifiable.
In GitHub (Settings → Rules → Rulesets, or Settings → Branches), protect both `main` and `develop`:
  - require a pull request before merging;
  - block force pushes;
  - restrict deletions;
  - do not let agent credentials bypass the rules (rulesets: keep them out of the bypass list;
    classic branch protection: enable "Do not allow bypassing the above settings").
To verify, run this check with a token that can read repository administration settings
(fine-grained: Administration read-only) in GH_TOKEN or GITHUB_TOKEN. Never commit the token."""

# Fetch returns (HTTP status, decoded JSON body or None).
Fetch = Callable[[str], "tuple[int, Any]"]


@dataclass
class BranchResult:
    branch: str
    state: str
    missing: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def github_fetch(api_url: str, token: str | None) -> Fetch:
    def fetch(path: str) -> tuple[int, Any]:
        request = urllib.request.Request(f"{api_url.rstrip('/')}{path}")
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, json.load(exc)
            except ValueError:
                return exc.code, None

    return fetch


def ruleset_requirements(repo: str, branch: str, fetch: Fetch, notes: list[str]) -> set[str] | None:
    """Requirements met by active rulesets, or None when the rules cannot be read."""
    status, rules = fetch(f"/repos/{repo}/rules/branches/{branch}")
    if status != 200 or not isinstance(rules, list):
        notes.append(f"rulesets unreadable (HTTP {status})")
        return None

    bypassable: dict[int, bool] = {}
    met: set[str] = set()
    for rule in rules:
        requirement = RULESET_RULES.get(rule.get("type"))
        if requirement is None:
            continue
        ruleset_id = rule.get("ruleset_id")
        if ruleset_id not in bypassable:
            ruleset_status, ruleset = fetch(f"/repos/{repo}/rulesets/{ruleset_id}")
            bypassable[ruleset_id] = ruleset_status == 200 and isinstance(ruleset, dict) and ruleset.get("current_user_can_bypass") in BYPASS_ALWAYS
            if bypassable[ruleset_id]:
                notes.append(f"ruleset {ruleset_id} can be bypassed by the checking credential")
        if not bypassable[ruleset_id]:
            met.add(requirement)
    return met


def classic_requirements(repo: str, branch: str, fetch: Fetch, notes: list[str]) -> set[str] | None:
    """Requirements met by classic branch protection, or None when it cannot be read."""
    status, protection = fetch(f"/repos/{repo}/branches/{branch}/protection")
    if status == 404 and isinstance(protection, dict) and protection.get("message") == "Branch not protected":
        return set()
    if status != 200 or not isinstance(protection, dict):
        notes.append(f"classic branch protection unreadable (HTTP {status})")
        return None

    if not (protection.get("enforce_admins") or {}).get("enabled"):
        notes.append("classic branch protection does not apply to administrators")
        return set()

    met: set[str] = set()
    if protection.get("required_pull_request_reviews"):
        met.add(PULL_REQUEST)
    if not (protection.get("allow_force_pushes") or {}).get("enabled"):
        met.add(NO_FORCE_PUSH)
    if not (protection.get("allow_deletions") or {}).get("enabled"):
        met.add(NO_DELETION)
    return met


def check_branch(repo: str, branch: str, fetch: Fetch) -> BranchResult:
    status, _ = fetch(f"/repos/{repo}/branches/{branch}")
    if status == 404:
        return BranchResult(branch, UNPROTECTED, list(REQUIREMENTS), ["branch does not exist on the repository host"])
    if status != 200:
        return BranchResult(branch, UNVERIFIABLE, list(REQUIREMENTS), [f"branch unreadable (HTTP {status})"])

    notes: list[str] = []
    sources = [ruleset_requirements(repo, branch, fetch, notes), classic_requirements(repo, branch, fetch, notes)]
    met = set().union(*(source for source in sources if source is not None))
    missing = [requirement for requirement in REQUIREMENTS if requirement not in met]
    if not missing:
        return BranchResult(branch, PROTECTED, [], notes)
    return BranchResult(branch, UNVERIFIABLE if None in sources else UNPROTECTED, missing, notes)


def require_credential(result: BranchResult) -> BranchResult:
    """An anonymous check cannot tell whether an agent credential may bypass the rules."""
    if result.state != PROTECTED:
        return result
    note = "checked without a credential; rerun with the agent runtime's token to confirm it cannot bypass the rules"
    return BranchResult(result.branch, UNVERIFIABLE, [], [*result.notes, note])


def overall_state(results: list[BranchResult]) -> str:
    states = {result.state for result in results}
    if UNPROTECTED in states:
        return UNPROTECTED
    if UNVERIFIABLE in states:
        return UNVERIFIABLE
    return PROTECTED


def repo_from_remote_url(url: str) -> str | None:
    match = re.search(r"[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    return f"{match.group(1)}/{match.group(2)}" if match else None


def detect_repo(remote: str) -> str | None:
    try:
        url = subprocess.run(["git", "remote", "get-url", remote], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return repo_from_remote_url(url)


def report(repo: str, results: list[BranchResult]) -> str:
    lines = [f"Branch protection for {repo}:"]
    for result in results:
        line = f"  {result.branch}: {result.state}"
        if result.missing:
            line += f" — missing: {', '.join(result.missing)}"
        lines.append(line)
        lines.extend(f"      {note}" for note in result.notes)
    if overall_state(results) != PROTECTED:
        lines += ["", REMEDIATION]
    return "\n".join(lines)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify GitHub protection of the main and develop branches (read-only).")
    parser.add_argument("--repo", help="GitHub repository as OWNER/NAME (default: derived from the git remote)")
    parser.add_argument("--remote", default="origin", help="Git remote used to derive --repo (default: origin)")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help=f"GitHub API base URL (default: {DEFAULT_API_URL})")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, fetch: Fetch | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo or detect_repo(args.remote)
    if not repo:
        print(f"Cannot determine the GitHub repository; pass --repo OWNER/NAME.\n\n{REMEDIATION}", file=sys.stderr)
        return EXIT_CODES[UNVERIFIABLE]

    token = next((os.environ[name] for name in TOKEN_ENV_VARS if os.environ.get(name)), None)
    fetch = fetch or github_fetch(args.api_url, token)

    try:
        results = [check_branch(repo, branch, fetch) for branch in PROTECTED_BRANCHES]
    except (OSError, ValueError) as exc:
        print(f"GitHub API request failed: {exc}\n\n{REMEDIATION}", file=sys.stderr)
        return EXIT_CODES[UNVERIFIABLE]
    if not token:
        results = [require_credential(result) for result in results]

    print(report(repo, results))
    return EXIT_CODES[overall_state(results)]


if __name__ == "__main__":
    raise SystemExit(main())
