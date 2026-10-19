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
# Commands that run another command given later in their arguments.
WRAPPERS = {"command", "env", "exec", "nohup", "sudo", "doas", "time", "nice", "ionice", "timeout", "stdbuf", "xargs", "caffeinate", "chronic"}
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git global options that consume the following token.
GIT_REPO_OPTIONS = {"-C", "--git-dir", "--work-tree"}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--super-prefix", "--config-env"}
# Config keys that can redirect a push or upstream, matched wherever they appear in `git config` arguments.
SENSITIVE_CONFIG_KEY = re.compile(r"^(remote\..+\.(push|mirror)|branch\..+\.merge|push\.default)$", re.IGNORECASE)
# `git push` options that take a separate value (from `git push -h`).
PUSH_WITH_VALUE = {"--repo", "-o", "--push-option", "--receive-pack", "--exec", "--recurse-submodules"}
# Long options the guard inspects; Git accepts any unique prefix of a long option.
PUSH_LONG = ["--all", "--branches", "--mirror", "--repo", "--push-option", "--receive-pack", "--exec", "--recurse-submodules", "--set-upstream"]
REMOTE_ADD_LONG = ["--mirror", "--master"]
BRANCH_LONG = ["--set-upstream-to", "--track", "--no-track"]
CHECKOUT_LONG = ["--create", "--force-create", "--track", "--no-track"]


def expand_long_options(args: list[str], known: list[str]) -> list[str]:
    """Expand unambiguous abbreviations such as `--mir` to `--mirror` (keeping any `=value`)."""
    expanded: list[str] = []
    for arg in args:
        if arg == "--":
            expanded.extend(args[len(expanded):])
            break
        name, equals, value = arg.partition("=")
        if name.startswith("--") and len(name) > 2 and name not in known:
            matches = [option for option in known if option.startswith(name)]
            if len(matches) == 1:
                arg = matches[0] + equals + value
        expanded.append(arg)
    return expanded


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


def git_output(repo: list[str], *args: str) -> str | None:
    """Run git against the repository selected by `repo` (git global options such as -C/--git-dir)."""
    try:
        result = subprocess.run(["git", *repo, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def current_branch(repo: list[str]) -> str | None:
    name = git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    return name or None


def unquoted_positions(line: str, quote: str | None) -> tuple[set[int], str | None]:
    """Indexes of `line` outside shell quotes, and the quote still open at its end."""
    positions: set[int] = set()
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
        elif quote == "'":
            quote = None if char == "'" else quote
        elif quote == '"':
            if char == "\\":
                escaped = True
            elif char == '"':
                quote = None
        elif char == "\\":
            escaped = True
        elif char in "'\"":
            quote = char
        else:
            positions.add(index)
    return positions, quote


def strip_heredoc_bodies(command: str) -> tuple[str, list[str]]:
    """Drop heredoc bodies (data such as commit messages), keeping the command lines.

    Returns the remaining text and the bodies fed to a shell (`bash <<EOF`), which are commands.
    """
    kept: list[str] = []
    shell_bodies: list[str] = []
    pending: list[tuple[str, bool, bool, list[str]]] = []
    quote: str | None = None
    for line in command.split("\n"):
        if pending:
            delimiter, strip_tabs, is_shell, body = pending[0]
            if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                pending.pop(0)
                if is_shell:
                    shell_bodies.append("\n".join(body))
            else:
                body.append(line)
            continue
        kept.append(line)
        unquoted, quote = unquoted_positions(line, quote)
        words = line.split()
        is_shell = bool(words) and os.path.basename(words[0]) in SHELLS
        pending = [(m.group(3), m.group(1) == "-", is_shell, []) for m in HEREDOC.finditer(line) if m.start() in unquoted]
    return "\n".join(kept), shell_bodies


def tokenize(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    return list(lexer)


def split_commands(command: str) -> list[list[str]]:
    """Split a shell string into simple commands (token lists)."""
    text, shell_bodies = strip_heredoc_bodies(command.replace("\\\n", " "))
    commands: list[list[str]] = []
    for body in shell_bodies:
        commands.extend(split_commands(body))
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
    """Drop leading variable assignments and wrapper commands (`env -i`, `timeout 5`, ...)."""
    index = 0
    while index < len(tokens) and ASSIGNMENT.match(tokens[index]):
        index += 1
    if index < len(tokens) and os.path.basename(tokens[index]) in WRAPPERS:
        for position in range(index + 1, len(tokens)):
            if os.path.basename(tokens[position]) in SHELLS | {"git"}:
                return tokens[position:]
        return []
    return tokens[index:]


def refspec_destination(refspec: str, repo: list[str]) -> str:
    source, colon, destination = refspec.lstrip("+").partition(":")
    if not colon:
        destination = source
    if branch_name(destination) in {"HEAD", "@"}:
        destination = current_branch(repo) or destination
    return branch_name(destination)


def push_remote(branch: str | None, repo: list[str]) -> str:
    """Remote a refspec-less `git push` uses, following Git's lookup order."""
    candidates = [f"branch.{branch}.pushRemote", "remote.pushDefault", f"branch.{branch}.remote"] if branch else ["remote.pushDefault"]
    for key in candidates:
        value = git_output(repo, "config", "--get", key)
        if value:
            return value
    return "origin"


def check_push(args: list[str], repo: list[str]) -> str | None:
    args = expand_long_options(args, PUSH_LONG)
    positionals: list[str] = []
    repo_option: str | None = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            positionals.extend(args[index + 1:])
            break
        if arg in {"--all", "--branches", "--mirror"}:
            return f"`git push {arg}` would push protected branches"
        if arg.startswith("--repo="):
            repo_option = arg.split("=", 1)[1]
        if arg in PUSH_WITH_VALUE:
            if arg == "--repo" and index + 1 < len(args):
                repo_option = args[index + 1]
            index += 2
            continue
        if not arg.startswith("-"):
            positionals.append(arg)
        index += 1

    refspecs = positionals[1:]
    if not refspecs:
        branch = current_branch(repo)
        remote = positionals[0] if positionals else repo_option or push_remote(branch, repo)
        if (git_output(repo, "config", "--type=bool", "--get", f"remote.{remote}.mirror") or "") == "true":
            return f"remote `{remote}` is configured to mirror, which pushes every ref including protected branches"
        for configured in (git_output(repo, "config", "--get-all", f"remote.{remote}.push") or "").splitlines():
            if is_protected(refspec_destination(configured, repo)):
                return f"configured refspec `remote.{remote}.push={configured}` targets a protected branch"
        if git_output(repo, "config", "--get", "push.default") == "matching":
            return "`git push` with push.default=matching would push every matching branch, including protected ones"
        if branch in PROTECTED:
            return f"`git push` without a refspec would push the protected branch `{branch}`"
        if branch:
            merge = git_output(repo, "config", "--get", f"branch.{branch}.merge")
            if merge and is_protected(branch_name(merge)):
                return f"`git push` without a refspec would push `{branch}` to its protected upstream `{branch_name(merge)}`"
        return None

    for refspec in refspecs:
        if refspec.lstrip("+") == ":":
            return f"matching refspec `{refspec}` would push every branch that exists on the remote, including protected ones"
        destination = refspec_destination(refspec, repo)
        if is_protected(destination):
            return f"refspec `{refspec}` targets protected branch `{destination}`"
    return None


def upstream_is_protected(branch: str) -> bool:
    # `<remote>/HEAD` is a symbolic ref to the remote's default branch, normally `main`.
    return is_protected(branch) or branch == "HEAD"


def check_upstream_value(value: str) -> str | None:
    branch = upstream_branch(value)
    if upstream_is_protected(branch):
        return f"`{value}` would make protected branch `{branch}` an upstream"
    return None


def check_branch(args: list[str]) -> str | None:
    args = expand_long_options(args, BRANCH_LONG)
    for index, arg in enumerate(args):
        if arg.startswith("--set-upstream-to="):
            return check_upstream_value(arg.split("=", 1)[1])
        if arg in {"-u", "--set-upstream-to"} and index + 1 < len(args):
            return check_upstream_value(args[index + 1])
        if arg.startswith("-u") and len(arg) > 2:
            return check_upstream_value(arg[2:])
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
    if (explicit_track or remote_tracking) and upstream_is_protected(upstream_branch(start_point)):
        return f"creating a branch from `{start_point}` would track protected branch `{upstream_branch(start_point)}`; add --no-track"
    return None


def split_attached(args: list[str], create_flags: set[str]) -> list[str]:
    """Normalize `-bname` and `--create=name` into separate flag and value tokens."""
    normalized: list[str] = []
    for arg in args:
        long_flag = arg.split("=", 1)[0]
        if arg.startswith("--") and "=" in arg and long_flag in create_flags:
            normalized.extend([long_flag, arg.split("=", 1)[1]])
        elif not arg.startswith("--") and len(arg) > 2 and arg[:2] in create_flags:
            normalized.extend([arg[:2], arg[2:]])
        else:
            normalized.append(arg)
    return normalized


def check_checkout(args: list[str], create_flags: set[str]) -> str | None:
    args = split_attached(expand_long_options(args, CHECKOUT_LONG), create_flags)
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
    """Check `git config` arguments; sensitive keys are found by name so option layout does not matter."""
    for index, arg in enumerate(args[:-1]):
        if SENSITIVE_CONFIG_KEY.match(arg):
            reason = check_config_value(arg, args[index + 1])
            if reason:
                return reason
    return None


def check_config_value(key: str, value: str) -> str | None:
    key = key.lower()
    if key.startswith("remote.") and key.endswith(".mirror") and value.lower() in {"true", "yes", "on", "1"}:
        return "remote mirroring would push every ref, including protected branches"
    if key == "push.default" and value == "matching":
        return "push.default=matching would let a plain `git push` update protected branches"
    if key.startswith("branch.") and key.endswith(".merge"):
        return check_upstream_value(value)
    if key.startswith("remote.") and key.endswith(".push"):
        destination = branch_name(value.partition(":")[2] or value)
        if is_protected(destination):
            return f"`remote.*.push` refspec `{value}` targets protected branch `{destination}`"
    return None


def check_remote(args: list[str]) -> str | None:
    if args[:1] != ["add"]:
        return None
    for arg in expand_long_options(args[1:], REMOTE_ADD_LONG):
        if arg in {"--mirror", "--mirror=push"}:
            return "`git remote add --mirror` would make plain pushes to that remote update every ref, including protected branches"
    return None


def check_git(args: list[str], cwd: str | None) -> str | None:
    index = 0
    # Git global options that change which repository or configuration is used; replayed in lookups.
    repo = ["-C", cwd] if cwd else []
    while index < len(args) and args[index].startswith("-"):
        option = args[index]
        name, attached, attached_value = option.partition("=")
        if name in GIT_REPO_OPTIONS and attached:
            repo += [name, attached_value]
            index += 1
            continue
        if option in GIT_REPO_OPTIONS and index + 1 < len(args):
            repo += [option, args[index + 1]]
        if option in {"-c", "--config-env"} and index + 1 < len(args):
            repo += [option, args[index + 1]]
            if option == "-c":
                # Inline config (e.g. remote.origin.push=HEAD:main) can redirect a push.
                key, _, value = args[index + 1].partition("=")
                reason = check_config_value(key, value)
                if reason:
                    return f"inline config: {reason}"
        elif name == "--config-env" and attached:
            repo.append(option)
        index += 2 if option in GIT_GLOBAL_WITH_VALUE else 1
    if index >= len(args):
        return None
    subcommand, rest = args[index], args[index + 1:]
    if subcommand == "push":
        return check_push(rest, repo)
    if subcommand == "branch":
        return check_branch(rest)
    if subcommand == "checkout":
        return check_checkout(rest, {"-b", "-B"})
    if subcommand == "switch":
        return check_checkout(rest, {"-c", "-C", "--create", "--force-create"})
    if subcommand == "config":
        return check_config(rest)
    if subcommand == "remote":
        return check_remote(rest)
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
            script = tokens[flag + 2] if tokens[flag + 1] == "--" and flag + 2 < len(tokens) else tokens[flag + 1]
            reason = check_command(script, cwd)
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
