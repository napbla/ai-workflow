from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import branch_protection as bp  # noqa: E402

REPO = "owner/repo"
NOT_PROTECTED = (404, {"message": "Branch not protected"})
FORBIDDEN = (403, {"message": "Resource not accessible by integration"})

FULL_CLASSIC = {
    "required_pull_request_reviews": {"required_approving_review_count": 1},
    "enforce_admins": {"enabled": True},
    "allow_force_pushes": {"enabled": False},
    "allow_deletions": {"enabled": False},
}
FULL_RULES = [
    {"type": "pull_request", "ruleset_id": 7},
    {"type": "non_fast_forward", "ruleset_id": 7},
    {"type": "deletion", "ruleset_id": 7},
]


def fake_fetch(
    branches: dict[str, dict[str, Any]],
    rulesets: dict[int, tuple[int, Any]] | None = None,
    repo: tuple[int, Any] = (200, {"full_name": REPO}),
):
    """Build a fetch over per-branch responses: keys `branch`, `rules` (one response or a list of pages), `classic`."""
    calls: list[str] = []

    def fetch(path: str) -> tuple[int, Any]:
        calls.append(path)
        path, _, query = path.partition("?")
        if path == f"/repos/{REPO}":
            return repo
        prefix = f"/repos/{REPO}/"
        assert path.startswith(prefix), path
        rest = path[len(prefix):]
        if rest.startswith("rulesets/"):
            return (rulesets or {}).get(int(rest.split("/")[1]), (200, {"current_user_can_bypass": "never"}))
        kind, _, tail = rest.partition("/")
        if kind == "rules":
            rules = branches[tail.split("/", 1)[1]].get("rules", (200, []))
            if isinstance(rules, list):
                page = int(dict(part.split("=") for part in query.split("&"))["page"])
                return rules[page - 1]
            return rules
        branch, _, sub = tail.partition("/")
        responses = branches[branch]
        if sub == "protection":
            return responses.get("classic", NOT_PROTECTED)
        return responses.get("branch", (200, {"name": branch}))

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def both(**responses: tuple[int, Any]) -> dict[str, dict[str, tuple[int, Any]]]:
    return {"main": dict(responses), "develop": dict(responses)}


class CheckBranchTest(unittest.TestCase):
    def check(self, responses: dict[str, tuple[int, Any]], rulesets: dict[int, tuple[int, Any]] | None = None) -> bp.BranchResult:
        return bp.check_branch(REPO, "main", fake_fetch({"main": responses}, rulesets))

    def test_rulesets_alone_protect(self) -> None:
        result = self.check({"rules": (200, FULL_RULES), "classic": FORBIDDEN})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_classic_protection_alone_protects(self) -> None:
        result = self.check({"classic": (200, FULL_CLASSIC)})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_requirements_combine_across_sources(self) -> None:
        classic = {**FULL_CLASSIC, "allow_deletions": {"enabled": True}}
        result = self.check({"rules": (200, [{"type": "deletion", "ruleset_id": 1}]), "classic": (200, classic)})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_no_protection_is_unprotected(self) -> None:
        result = self.check({})
        self.assertEqual(result.state, bp.UNPROTECTED)
        self.assertEqual(result.missing, list(bp.REQUIREMENTS))

    def test_partial_protection_lists_missing_requirements(self) -> None:
        result = self.check({"rules": (200, [{"type": "pull_request", "ruleset_id": 1}])})
        self.assertEqual(result.state, bp.UNPROTECTED)
        self.assertEqual(result.missing, [bp.NO_FORCE_PUSH, bp.NO_DELETION])

    def test_classic_protection_must_apply_to_administrators(self) -> None:
        classic = {**FULL_CLASSIC, "enforce_admins": {"enabled": False}}
        result = self.check({"classic": (200, classic)})
        self.assertEqual(result.state, bp.UNPROTECTED)
        self.assertIn("classic branch protection does not apply to administrators", result.notes)

    def test_ruleset_bypassable_by_checking_credential_does_not_count(self) -> None:
        for bypass in ("always", "exempt"):
            result = self.check({"rules": (200, FULL_RULES)}, {7: (200, {"current_user_can_bypass": bypass})})
            self.assertEqual(result.state, bp.UNPROTECTED, bypass)
            self.assertIn("ruleset 7 can be bypassed by the checking credential", result.notes)

    def test_pull_request_only_bypass_still_counts_as_protected(self) -> None:
        result = self.check({"rules": (200, FULL_RULES)}, {7: (200, {"current_user_can_bypass": "pull_requests_only"})})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_unknown_ruleset_bypass_status_is_unverifiable(self) -> None:
        for response in ((403, {"message": "Forbidden"}), (500, None), (200, {}), (200, {"current_user_can_bypass": "new-value"})):
            result = self.check({"rules": (200, FULL_RULES), "classic": NOT_PROTECTED}, {7: response})
            self.assertEqual(result.state, bp.UNVERIFIABLE, response)
            self.assertIn(f"ruleset 7 bypass status unknown (HTTP {response[0]})", result.notes)

    def test_unknown_ruleset_bypass_does_not_hide_full_classic_protection(self) -> None:
        result = self.check({"rules": (200, FULL_RULES), "classic": (200, FULL_CLASSIC)}, {7: (403, None)})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_classic_pull_request_bypass_allowances_do_not_count(self) -> None:
        for kind in ("users", "teams", "apps"):
            reviews = {"required_approving_review_count": 1, "bypass_pull_request_allowances": {kind: [{"login": "someone"}]}}
            result = self.check({"classic": (200, {**FULL_CLASSIC, "required_pull_request_reviews": reviews})})
            self.assertEqual(result.state, bp.UNPROTECTED, kind)
            self.assertEqual(result.missing, [bp.PULL_REQUEST])
            self.assertIn("classic branch protection lets some actors bypass the pull request requirement", result.notes)

    def test_empty_bypass_allowances_still_count(self) -> None:
        reviews = {"bypass_pull_request_allowances": {"users": [], "teams": [], "apps": []}}
        result = self.check({"classic": (200, {**FULL_CLASSIC, "required_pull_request_reviews": reviews})})
        self.assertEqual(result.state, bp.PROTECTED)

    def test_rules_are_read_across_pages(self) -> None:
        filler = [{"type": "required_signatures", "ruleset_id": 1}] * bp.PAGE_SIZE
        pages = [(200, filler), (200, FULL_RULES)]
        fetch = fake_fetch({"main": {"rules": pages}})
        result = bp.check_branch(REPO, "main", fetch)
        self.assertEqual(result.state, bp.PROTECTED)
        self.assertTrue(any("page=2" in call for call in fetch.calls))

    def test_unreadable_later_page_is_unverifiable(self) -> None:
        filler = [{"type": "required_signatures", "ruleset_id": 1}] * bp.PAGE_SIZE
        result = self.check({"rules": [(200, filler), (502, None)]})
        self.assertEqual(result.state, bp.UNVERIFIABLE)

    def test_unreadable_classic_protection_is_unverifiable(self) -> None:
        result = self.check({"classic": FORBIDDEN})
        self.assertEqual(result.state, bp.UNVERIFIABLE)
        self.assertIn("classic branch protection unreadable (HTTP 403)", result.notes)

    def test_unreadable_rulesets_are_unverifiable(self) -> None:
        result = self.check({"rules": (401, {"message": "Bad credentials"})})
        self.assertEqual(result.state, bp.UNVERIFIABLE)

    def test_missing_branch_is_unprotected(self) -> None:
        result = self.check({"branch": (404, {"message": "Branch not found"})})
        self.assertEqual(result.state, bp.UNPROTECTED)
        self.assertIn("branch does not exist on the repository host", result.notes)


class MainTest(unittest.TestCase):
    def run_main(self, fetch: Any, *argv: str, token: str | None = "test-token") -> tuple[int, str, str]:
        env = {name: "" for name in bp.TOKEN_ENV_VARS}
        if token:
            env["GH_TOKEN"] = token
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = bp.main(["--repo", REPO, *argv], fetch=fetch)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_both_branches_protected_exits_zero_without_blocker(self) -> None:
        fetch = fake_fetch(both(rules=(200, FULL_RULES)))
        code, out, _ = self.run_main(fetch)
        self.assertEqual(code, 0)
        self.assertIn("main: protected", out)
        self.assertIn("develop: protected", out)
        self.assertNotIn("BLOCKER", out)
        self.assertTrue(any("/branches/develop" in call for call in fetch.calls))

    def test_anonymous_check_cannot_confirm_protection(self) -> None:
        code, out, _ = self.run_main(fake_fetch(both(rules=(200, FULL_RULES))), token=None)
        self.assertEqual(code, 2)
        self.assertIn("main: unverifiable", out)
        self.assertIn("checked without a credential", out)
        self.assertIn("HUMAN SETUP BLOCKER", out)

    def test_token_is_never_printed(self) -> None:
        _, out, err = self.run_main(fake_fetch(both(classic=FORBIDDEN)), token="secret-token-value")
        self.assertNotIn("secret-token-value", out + err)

    def test_unprotected_develop_reports_human_setup_blocker(self) -> None:
        branches = both(rules=(200, FULL_RULES))
        branches["develop"] = {}
        code, out, _ = self.run_main(fake_fetch(branches))
        self.assertEqual(code, 1)
        self.assertIn("develop: not protected — missing: pull request required", out)
        self.assertIn("HUMAN SETUP BLOCKER", out)

    def test_unverifiable_reports_blocker_with_distinct_exit_code(self) -> None:
        code, out, _ = self.run_main(fake_fetch(both(classic=FORBIDDEN)))
        self.assertEqual(code, 2)
        self.assertIn("main: unverifiable", out)
        self.assertIn("HUMAN SETUP BLOCKER", out)

    def test_unprotected_takes_precedence_over_unverifiable(self) -> None:
        branches = {"main": {"classic": FORBIDDEN}, "develop": {}}
        code, _, _ = self.run_main(fake_fetch(branches))
        self.assertEqual(code, 1)

    def test_inaccessible_repository_is_unverifiable_not_unprotected(self) -> None:
        fetch = fake_fetch(both(branch=(404, {"message": "Not Found"})), repo=(404, {"message": "Not Found"}))
        code, out, err = self.run_main(fetch)
        self.assertEqual(code, 2)
        self.assertIn("not found or not accessible", err)
        self.assertIn("HUMAN SETUP BLOCKER", err)
        self.assertEqual(out, "")

    def test_network_failure_is_unverifiable(self) -> None:
        def fetch(path: str) -> tuple[int, Any]:
            raise OSError("network unreachable")

        code, _, err = self.run_main(fetch)
        self.assertEqual(code, 2)
        self.assertIn("HUMAN SETUP BLOCKER", err)


class RepoFromRemoteTest(unittest.TestCase):
    def test_parses_common_remote_forms(self) -> None:
        for url in (
            "git@github.com:owner/repo.git",
            "git@github-alias:owner/repo.git",
            "https://github.com/owner/repo.git",
            "https://github.com/owner/repo",
            "ssh://git@github.com/owner/repo.git\n",
        ):
            self.assertEqual(bp.repo_from_remote_url(url), "owner/repo", url)

    def test_rejects_unparseable_remote(self) -> None:
        self.assertIsNone(bp.repo_from_remote_url("not-a-remote"))


if __name__ == "__main__":
    unittest.main()
