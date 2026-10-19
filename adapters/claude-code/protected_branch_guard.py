#!/usr/bin/env python3
"""Claude Code PreToolUse hook enforcing the ai-workflow protected branch policy.

Blocks Bash commands that would push to `main`/`develop`, push all/mirror refs,
or make `main`/`develop` an upstream or push target. Normal feature-branch
pushes are allowed. This is a best-effort runtime adapter; repository-host
branch protection remains the authoritative layer.

Exit code 2 blocks the tool call and returns the reason to Claude.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "develop"}
SEPARATOR_CHARS = set(";&|()\n")
HEREDOC = re.compile(r"(?<!<)<<(?!<)(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
SHELLS = {"sh", "bash", "zsh"}
SHELL_COMMAND_FLAG = re.compile(r"^-[a-zA-Z]*c[a-zA-Z]*$")
WRAPPERS = {"command", "env", "exec", "nohup", "sudo", "time"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git global options that consume the following token.
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
PUSH_WITH_VALUE = {"--repo", "-o", "--push-option", "--receive-pack", "--exec"}


def branch_name(ref: str) -> str:
    ref = ref.lstrip("+")
    for prefix in ("refs/heads/", "heads/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def upstream_branch(spec: str) -> str:
    """Branch part of an upstream like `origin/main`, `refs/remotes/origin/main`, or `main`."""
    if spec.startswith("refs/remotes/"):
        spec = spec[len("refs/remotes/"):]
    elif spec.startswith("remotes/"):
        spec = spec[len("remotes/"):]
    else:
        spec = branch_name(spec)
        return spec if "/" not in spec else spec.split("/", 1)[1]
    return spec.split("/", 1)[1] if "/" in spec else spec


def is_protected(name: str) -> bool:
    return name in PROTECTED or "*" in name


def git_output(cwd: str | None, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=cwd or None, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def current_branch(cwd: str | None) -> str | None:
    name = git_output(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
    return name or None


def strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc bodies (data such as commit messages), keeping the command lines."""
    kept: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.split("\n"):
        if pending:
            delimiter, strip_tabs = pending[0]
            if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                pending.pop(0)
            continue
        kept.append(line)
        pending = [(m.group(3), m.group(1) == "-") for m in HEREDOC.finditer(line)]
    return "\n".join(kept)


def tokenize(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def split_commands(command: str) -> list[list[str]]:
    """Split a shell string into simple commands (token lists)."""
    text = strip_heredoc_bodies(command.replace("\\\n", " "))
    try:
        chunks = [tokenize(text)]
    except ValueError:
        # Unbalanced quoting: check each line on its own and skip lines that do not parse.
        chunks = []
        for line in text.split("\n"):
            try:
                chunks.append(tokenize(line))
            except ValueError:
                continue
    commands: list[list[str]] = []
    for tokens in chunks:
        current: list[str] = []
        for token in tokens:
            if set(token) <= SEPARATOR_CHARS:
                if current:
                    commands.append(current)
                current = []
            else:
                current.append(token)
        if current:
            commands.append(current)
    return commands


def strip_prefix(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and (ASSIGNMENT.match(tokens[index]) or os.path.basename(tokens[index]) in WRAPPERS):
        index += 1
    return tokens[index:]


def check_push(args: list[str], cwd: str | None, push_default: str | None = None) -> str | None:
    positionals: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            positionals.extend(args[index + 1:])
            break
        if arg in {"--all", "--branches", "--mirror"}:
            return f"`git push {arg}` would push protected branches"
        if arg in PUSH_WITH_VALUE:
            index += 2
            continue
        if not arg.startswith("-"):
            positionals.append(arg)
        index += 1

    refspecs = positionals[1:]
    if not refspecs:
        if (push_default or git_output(cwd, "config", "--get", "push.default")) == "matching":
            return "`git push` with push.default=matching would push every matching branch, including protected ones"
        branch = current_branch(cwd)
        if branch in PROTECTED:
            return f"`git push` without a refspec would push the protected branch `{branch}`"
        if branch:
            merge = git_output(cwd, "config", "--get", f"branch.{branch}.merge")
            if merge and is_protected(branch_name(merge)):
                return f"`git push` without a refspec would push `{branch}` to its protected upstream `{branch_name(merge)}`"
        return None

    for refspec in refspecs:
        if refspec.lstrip("+") == ":":
            return f"matching refspec `{refspec}` would push every branch that exists on the remote, including protected ones"
        source, _, destination = refspec.partition(":")
        if not _:
            destination = source
        if branch_name(destination) in {"HEAD", "@"}:
            destination = current_branch(cwd) or destination
        destination = branch_name(destination)
        if is_protected(destination):
            return f"refspec `{refspec}` targets protected branch `{destination}`"
    return None


def check_upstream_value(value: str) -> str | None:
    branch = upstream_branch(value)
    if is_protected(branch):
        return f"`{value}` would make protected branch `{branch}` an upstream"
    return None


def check_branch(args: list[str]) -> str | None:
    for index, arg in enumerate(args):
        if arg.startswith("--set-upstream-to="):
            return check_upstream_value(arg.split("=", 1)[1])
        if arg in {"-u", "--set-upstream-to"} and index + 1 < len(args):
            return check_upstream_value(args[index + 1])
    return check_tracking_start_point(args, {"-t", "--track"})


def check_tracking_start_point(args: list[str], create_flags: set[str]) -> str | None:
    """Creating a branch from a protected remote-tracking start point sets it as upstream unless --no-track is given."""
    if "--no-track" in args:
        return None
    explicit_track = any(arg in {"-t", "--track"} or arg.startswith("--track=") for arg in args)
    positionals = [arg for arg in args if not arg.startswith("-")]
    if not positionals:
        return None
    start_point = positionals[-1] if len(positionals) >= 2 or create_flags & set(args) else None
    if start_point is None:
        return None
    remote_tracking = start_point.startswith(("refs/remotes/", "remotes/")) or ("/" in start_point and not start_point.startswith("refs/heads/"))
    if (explicit_track or remote_tracking) and is_protected(upstream_branch(start_point)):
        return f"creating a branch from `{start_point}` would track protected branch `{upstream_branch(start_point)}`; add --no-track"
    return None


def check_checkout(args: list[str], create_flags: set[str]) -> str | None:
    if not create_flags & set(args):
        return None
    # Drop the new branch name that follows the create flag; what remains is the start point.
    filtered: list[str] = []
    skip = False
    for arg in args:
        if not skip:
            filtered.append(arg)
        skip = arg in create_flags
    return check_tracking_start_point(filtered, create_flags)


def check_config(args: list[str]) -> str | None:
    positionals = [arg for arg in args if not arg.startswith("-")]
    if len(positionals) < 2:
        return None
    key, value = positionals[0].lower(), positionals[1]
    if key == "push.default" and value == "matching":
        return "push.default=matching would let a plain `git push` update protected branches"
    if key.startswith("branch.") and key.endswith(".merge"):
        return check_upstream_value(value)
    if key.startswith("remote.") and key.endswith(".push"):
        destination = branch_name(value.partition(":")[2] or value)
        if is_protected(destination):
            return f"`remote.*.push` refspec `{value}` targets protected branch `{destination}`"
    return None


def check_git(args: list[str], cwd: str | None) -> str | None:
    index = 0
    push_default = None
    while index < len(args) and args[index].startswith("-"):
        option = args[index]
        if option == "-C" and index + 1 < len(args):
            cwd = os.path.join(cwd or os.getcwd(), args[index + 1])
        if option == "-c" and index + 1 < len(args) and args[index + 1].lower().startswith("push.default="):
            push_default = args[index + 1].split("=", 1)[1]
        index += 2 if option in GIT_GLOBAL_WITH_VALUE else 1
    if index >= len(args):
        return None
    subcommand, rest = args[index], args[index + 1:]
    if subcommand == "push":
        return check_push(rest, cwd, push_default)
    if subcommand == "branch":
        return check_branch(rest)
    if subcommand == "checkout":
        return check_checkout(rest, {"-b", "-B"})
    if subcommand == "switch":
        return check_checkout(rest, {"-c", "-C", "--create", "--force-create"})
    if subcommand == "config":
        return check_config(rest)
    return None


def check_command(command: str, cwd: str | None = None) -> str | None:
    """Return a denial reason, or None if the command is allowed."""
    for tokens in split_commands(command):
        tokens = strip_prefix(tokens)
        if not tokens:
            continue
        program = os.path.basename(tokens[0])
        flag = next((i for i, token in enumerate(tokens[1:-1], start=1) if SHELL_COMMAND_FLAG.match(token)), None)
        if program in SHELLS and flag is not None:
            reason = check_command(tokens[flag + 1], cwd)
        elif program == "git":
            reason = check_git(tokens[1:], cwd)
        else:
            reason = None
        if reason:
            return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = check_command(command, payload.get("cwd"))
    if reason:
        print(
            f"Blocked by ai-workflow protected branch policy: {reason}. "
            "Push only your feature branch (e.g. `git push -u origin feature/<change-id>`); "
            "main and develop change only through reviewed PRs.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
