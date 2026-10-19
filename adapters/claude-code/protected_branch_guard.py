#!/usr/bin/env python3
"""Claude Code PreToolUse hook enforcing the ai-workflow protected branch policy.

Blocks Bash commands that would push to `main`/`develop`, push all/mirror refs,
or make `main`/`develop` an upstream or push target. Normal feature-branch
pushes are allowed. This is a best-effort runtime adapter; repository-host
branch protection remains the authoritative layer.

Approach: every `git` word in a command is analyzed wherever it appears
(after keywords, wrappers, `!`, `{`, ...), nested scripts (`sh -c`, here-strings
fed to a shell, `eval`, `env -S`) are checked recursively, options are
normalized the way Git parses them, refs are resolved with Git itself, and
unrecognized git global options fail closed.

Exit code 2 blocks the tool call and returns the reason to Claude.
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys

PROTECTED = {"main", "develop"}
SEPARATOR_CHARS = set(";&|()\n")
REDIRECT_CHARS = set("<>&|")
HEREDOC = re.compile(r"(?<!<)<<(?!<)(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
SHELLS = {"sh", "bash", "zsh"}
SHELL_COMMAND_FLAG = re.compile(r"^-[a-zA-Z]*c[a-zA-Z]*$")
# Git subcommands the guard inspects; arguments appended by xargs cannot be checked for these.
INSPECTED = {"push", "branch", "checkout", "switch", "config", "remote", "worktree"}

# Git global options (from `git -h`). Anything else before the subcommand fails closed.
GIT_GLOBAL_NO_VALUE = {
    "-v", "--version", "-h", "--help", "-p", "--paginate", "-P", "--no-pager", "--no-replace-objects",
    "--no-lazy-fetch", "--no-optional-locks", "--no-advice", "--bare", "--html-path", "--man-path",
    "--info-path", "--exec-path", "--literal-pathspecs", "--glob-pathspecs", "--noglob-pathspecs",
    "--icase-pathspecs",
}
GIT_GLOBAL_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix", "--attr-source", "--list-cmds"}
# Global options replayed in the guard's own git lookups so they see the same repository and config.
GIT_CONTEXT_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--config-env"}

# `git config` actions that read or remove rather than write.
CONFIG_READ_SUBCOMMANDS = {"get", "list", "unset", "remove-section", "rename-section", "edit"}
CONFIG_READ_OPTIONS = {
    "--get", "--get-all", "--get-regexp", "--get-urlmatch", "--get-color", "--get-colorbool", "-l", "--list",
    "--unset", "--unset-all", "--remove-section", "--rename-section", "-e", "--edit",
}
# Config keys that can redirect a push or upstream, matched wherever they appear in `git config` arguments.
SENSITIVE_CONFIG_KEY = re.compile(r"^(remote\..+\.(push|mirror)|branch\..+\.merge|push\.default)$", re.IGNORECASE)

# Per-subcommand option tables: long options the guard inspects (Git accepts unique prefixes)
# and short options that take a value (a short-option cluster stops at the first of these).
PUSH_LONG = ["--all", "--branches", "--mirror", "--repo", "--push-option", "--receive-pack", "--exec", "--recurse-submodules", "--set-upstream"]
PUSH_WITH_VALUE = {"--repo", "-o", "--push-option", "--receive-pack", "--exec", "--recurse-submodules"}
BRANCH_LONG = ["--set-upstream-to", "--track", "--no-track"]
BRANCH_WITH_VALUE = {"-u", "--set-upstream-to"}
CHECKOUT_LONG = ["--create", "--force-create", "--track", "--no-track", "--orphan", "--unified", "--conflict"]
CHECKOUT_WITH_VALUE = {"-b", "-B", "-c", "-C", "-U", "--create", "--force-create", "--orphan", "--unified"}
WORKTREE_ADD_LONG = ["--track", "--no-track", "--reason"]
WORKTREE_ADD_WITH_VALUE = {"-b", "-B", "--reason"}
REMOTE_ADD_LONG = ["--mirror", "--master"]


def expand_options(args: list[str], known_long: list[str], with_value: set[str]) -> list[str]:
    """Normalize options the way Git parses them.

    Expands unique long-option prefixes (`--mir` → `--mirror`), splits short clusters
    (`-qb name` → `-q -b name`, `-uorigin/x` → `-u origin/x`), and splits `--opt=value`
    for value-taking options. Everything after `--` is left untouched.
    """
    expanded: list[str] = []
    for index, arg in enumerate(args):
        if arg == "--":
            expanded.extend(args[index:])
            break
        if arg.startswith("--") and len(arg) > 2:
            name, equals, value = arg.partition("=")
            if name not in known_long:
                matches = [option for option in known_long if option.startswith(name)]
                if len(matches) == 1:
                    name = matches[0]
            if equals and name in with_value:
                expanded.extend([name, value])
            else:
                expanded.append(name + equals + value)
        elif arg.startswith("-") and len(arg) > 2 and arg[1].isalpha():
            for position, char in enumerate(arg[1:], start=1):
                expanded.append(f"-{char}")
                if f"-{char}" in with_value:
                    if position + 1 < len(arg):
                        expanded.append(arg[position + 1:])
                    break
        else:
            expanded.append(arg)
    return expanded


def positionals_of(args: list[str], with_value: set[str]) -> list[str]:
    """Non-option arguments before `--`, skipping the values of value-taking options."""
    positionals: list[str] = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg == "--":
            break
        elif arg in with_value:
            skip = True
        elif not arg.startswith("-") or arg == "-":
            positionals.append(arg)
    return positionals


def option_values(args: list[str], option: str) -> list[str]:
    return [args[index + 1] for index, arg in enumerate(args[:-1]) if arg == option]


def branch_name(ref: str) -> str:
    ref = ref.lstrip("+")
    for prefix in ("refs/heads/", "heads/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def is_protected(name: str) -> bool:
    return name in PROTECTED or "*" in name


def upstream_is_protected(branch: str) -> bool:
    # `<remote>/HEAD` is a symbolic ref to the remote's default branch, normally `main`.
    return is_protected(branch) or branch == "HEAD"


def git_output(repo: list[str], *args: str) -> str | None:
    """Run git against the repository/config selected by `repo` (replayed global options)."""
    try:
        result = subprocess.run(["git", *repo, *args], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def current_branch(repo: list[str]) -> str | None:
    return git_output(repo, "symbolic-ref", "--quiet", "--short", "HEAD") or None


def ref_info(value: str, repo: list[str]) -> tuple[str, bool]:
    """(branch name, is remote-tracking) for a ref expression such as `origin/main`, `main@{u}`, or `-`."""
    expression = "@{-1}" if value == "-" else value
    full = git_output(repo, "rev-parse", "--symbolic-full-name", expression) if not expression.startswith("-") else None
    if full and full.startswith("refs/remotes/"):
        rest = full[len("refs/remotes/"):]
        return (rest.split("/", 1)[1] if "/" in rest else rest), True
    if full and full.startswith("refs/heads/"):
        return full[len("refs/heads/"):], False
    # Unresolvable (e.g. remote not fetched yet): interpret the text.
    for prefix in ("refs/remotes/", "remotes/"):
        if value.startswith(prefix):
            rest = value[len(prefix):]
            return (rest.split("/", 1)[1] if "/" in rest else rest), True
    if value.startswith("refs/heads/"):
        return value[len("refs/heads/"):], False
    if "/" in value:
        return value.split("/", 1)[1], True
    return value, False


# ---------------------------------------------------------------- shell parsing


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
        is_shell = any(os.path.basename(word) in SHELLS for word in line.split())
        pending = [(m.group(3), m.group(1) == "-", is_shell, []) for m in HEREDOC.finditer(line) if m.start() in unquoted]
    return "\n".join(kept), shell_bodies


def tokenize(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
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


def is_redirect(token: str) -> bool:
    return bool(token) and set(token) <= REDIRECT_CHARS and ("<" in token or ">" in token)


def strip_redirections(tokens: list[str]) -> list[str]:
    """Drop redirection operators and their targets (`>/dev/null`, `2>&1`, `<<EOF`)."""
    kept: list[str] = []
    skip = False
    for token in tokens:
        if skip:
            skip = False
        elif is_redirect(token):
            skip = True
        else:
            kept.append(token)
    return kept


def nested_scripts(tokens: list[str]) -> list[str]:
    """Command strings run by `sh/bash/zsh -c`, a shell here-string, `eval`, or `env -S`."""
    scripts: list[str] = []
    for index, token in enumerate(tokens):
        program = os.path.basename(token)
        rest = tokens[index + 1:]
        if program in SHELLS:
            for position, arg in enumerate(rest[:-1]):
                if SHELL_COMMAND_FLAG.match(arg):
                    script_index = position + 2 if rest[position + 1] == "--" else position + 1
                    if script_index < len(rest):
                        scripts.append(rest[script_index])
                    break
            scripts.extend(rest[position + 1] for position, arg in enumerate(rest[:-1]) if arg == "<<<")
        elif program == "eval" and rest:
            scripts.append(" ".join(rest))
        elif program == "env":
            for position, arg in enumerate(rest):
                if arg in {"-S", "--split-string"} and position + 1 < len(rest):
                    scripts.append(rest[position + 1])
                elif arg.startswith("--split-string="):
                    scripts.append(arg.split("=", 1)[1])
                elif arg.startswith("-S") and len(arg) > 2:
                    scripts.append(arg[2:])
    return scripts


# ---------------------------------------------------------------- git checks


def refspec_destination(refspec: str, repo: list[str]) -> str:
    source, colon, destination = refspec.lstrip("+").partition(":")
    if not colon:
        destination = source
    if branch_name(destination) in {"HEAD", "@"}:
        destination = current_branch(repo) or destination
    return branch_name(destination)


def refspec_is_protected(refspec: str, repo: list[str]) -> bool:
    """True for matching refspecs (`:`), wildcards, and destinations main/develop."""
    return refspec.lstrip("+") == ":" or is_protected(refspec_destination(refspec, repo))


def push_remote(branch: str | None, repo: list[str]) -> str:
    """Remote a refspec-less `git push` uses, following Git's lookup order."""
    candidates = [f"branch.{branch}.pushRemote", "remote.pushDefault", f"branch.{branch}.remote"] if branch else ["remote.pushDefault"]
    for key in candidates:
        value = git_output(repo, "config", "--get", key)
        if value:
            return value
    return "origin"


def configured_push_problem(remote: str, repo: list[str]) -> str | None:
    if (git_output(repo, "config", "--type=bool", "--get", f"remote.{remote}.mirror") or "") == "true":
        return f"remote `{remote}` is configured to mirror, which pushes every ref including protected branches"
    for configured in (git_output(repo, "config", "--get-all", f"remote.{remote}.push") or "").splitlines():
        if refspec_is_protected(configured, repo):
            return f"configured refspec `remote.{remote}.push={configured}` targets a protected branch"
    return None


def full_ref(name: str, repo: list[str]) -> str:
    resolved = git_output(repo, "rev-parse", "--symbolic-full-name", name) if not name.startswith("-") else None
    return resolved or (name if name.startswith("refs/") else f"refs/heads/{name}")


def configured_mapping_problem(remote: str, refspec: str, repo: list[str]) -> str | None:
    """Git maps a source-only refspec through a `remote.<name>.push` entry whose source names the same ref."""
    source = full_ref(refspec.lstrip("+"), repo)
    for configured in (git_output(repo, "config", "--get-all", f"remote.{remote}.push") or "").splitlines():
        configured_source, _, configured_destination = configured.lstrip("+").partition(":")
        if configured_source in {"HEAD", "@"}:
            matches = False  # Git does not map an explicit source through a HEAD entry
        elif not configured_source or "*" in configured_source:
            matches = "*" in configured_source and fnmatch.fnmatchcase(source, full_ref(configured_source, repo))
        else:
            matches = full_ref(configured_source, repo) == source
        if matches and refspec_is_protected(configured, repo):
            return f"`{refspec}` maps through `remote.{remote}.push={configured}` to a protected branch"
    return None


def protected_upstream(branch: str, repo: list[str]) -> str | None:
    merge = git_output(repo, "config", "--get", f"branch.{branch}.merge")
    return branch_name(merge) if merge and is_protected(branch_name(merge)) else None


def check_push(args: list[str], repo: list[str]) -> str | None:
    args = expand_options(args, PUSH_LONG, PUSH_WITH_VALUE)
    for flag in ("--all", "--branches", "--mirror"):
        if flag in args[: args.index("--") if "--" in args else len(args)]:
            return f"`git push {flag}` would push protected branches"
    positionals = positionals_of(args, PUSH_WITH_VALUE)
    if "--" in args:
        positionals += args[args.index("--") + 1:]
    repo_option = (option_values(args, "--repo") or [None])[-1]
    push_default = git_output(repo, "config", "--get", "push.default") or "simple"

    refspecs = positionals[1:]
    if not refspecs:
        branch = current_branch(repo)
        remote = positionals[0] if positionals else repo_option or push_remote(branch, repo)
        problem = configured_push_problem(remote, repo)
        if problem:
            return problem
        if push_default == "matching":
            return "`git push` with push.default=matching would push every matching branch, including protected ones"
        if branch in PROTECTED:
            return f"`git push` without a refspec would push the protected branch `{branch}`"
        upstream = protected_upstream(branch, repo) if branch else None
        if upstream:
            return f"`git push` without a refspec would push `{branch}` to its protected upstream `{upstream}`"
        return None

    remote = positionals[0]
    for refspec in refspecs:
        if refspec_is_protected(refspec, repo):
            return f"refspec `{refspec}` targets a protected branch"
        if ":" not in refspec:
            # A source-only refspec is mapped through remote.<name>.push or push.default=upstream.
            problem = configured_mapping_problem(remote, refspec, repo)
            if problem:
                return problem
            source = refspec_destination(refspec, repo)
            upstream = protected_upstream(source, repo) if push_default in {"upstream", "tracking"} else None
            if upstream:
                return f"refspec `{refspec}` would push to its protected upstream `{upstream}` (push.default={push_default})"
    return None


def check_upstream_value(value: str, repo: list[str]) -> str | None:
    branch, _ = ref_info(value, repo)
    if upstream_is_protected(branch):
        return f"`{value}` would make protected branch `{branch}` an upstream"
    return None


def track_mode(args: list[str]) -> str | None:
    """The effective --track/--no-track setting; the last one given wins."""
    mode = None
    for arg in args:
        if arg == "--":
            break
        if arg in {"-t", "--track"} or arg.startswith("--track="):
            mode = "track"
        elif arg == "--no-track":
            mode = "no-track"
    return mode


def check_start_point(start_point: str | None, args: list[str], repo: list[str]) -> str | None:
    """A new branch from a remote-tracking start point (or with --track) gets that branch as upstream."""
    mode = track_mode(args)
    if start_point is None or mode == "no-track":
        return None
    branch, remote_tracking = ref_info(start_point, repo)
    if (mode == "track" or remote_tracking) and upstream_is_protected(branch):
        return f"creating a branch from `{start_point}` would track protected branch `{branch}`; add --no-track"
    return None


def check_branch(args: list[str], repo: list[str]) -> str | None:
    args = expand_options(args, BRANCH_LONG, BRANCH_WITH_VALUE)
    for option in ("-u", "--set-upstream-to"):
        for value in option_values(args, option):
            reason = check_upstream_value(value, repo)
            if reason:
                return reason
    positionals = positionals_of(args, BRANCH_WITH_VALUE)
    return check_start_point(positionals[-1] if len(positionals) >= 2 else None, args, repo)


def check_create(args: list[str], create_flags: set[str], start_index: int, repo: list[str], known_long: list[str], with_value: set[str]) -> str | None:
    """Branch creation by checkout/switch/worktree add: check the start point that follows the new branch name."""
    args = expand_options(args, known_long, with_value)
    if not create_flags & set(args[: args.index("--") if "--" in args else len(args)]):
        return None
    positionals = positionals_of(args, with_value)
    start_point = positionals[start_index] if len(positionals) > start_index else None
    return check_start_point(start_point, args, repo)


def check_config(args: list[str]) -> str | None:
    """Check `git config` writes; sensitive keys are found by name so option layout does not matter."""
    if args[:1] and args[0] in CONFIG_READ_SUBCOMMANDS or any(arg.split("=", 1)[0] in CONFIG_READ_OPTIONS for arg in args):
        return None  # queries and removals take a value *pattern*, not a value being written
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
        branch = branch_name(value)
        if upstream_is_protected(branch.split("/", 1)[1] if value.startswith("refs/remotes/") and "/" in branch else branch):
            return f"`{value}` would make a protected branch an upstream"
    if key.startswith("remote.") and key.endswith(".push") and refspec_is_protected(value, []):
        return f"`remote.*.push` refspec `{value}` targets a protected branch"
    return None


def check_remote(args: list[str]) -> str | None:
    if args[:1] != ["add"]:
        return None
    for arg in expand_options(args[1:], REMOTE_ADD_LONG, set()):
        if arg in {"--mirror", "--mirror=push"}:
            return "`git remote add --mirror` would make plain pushes to that remote update every ref, including protected branches"
    return None


def check_git(args: list[str], cwd: str | None, via_xargs: bool = False) -> str | None:
    """Check one git invocation (`args` excludes the `git` word itself)."""
    index = 0
    repo = ["-C", cwd] if cwd else []
    while index < len(args) and args[index].startswith("-"):
        option = args[index]
        name, attached, value = option.partition("=")
        if attached and name in GIT_GLOBAL_WITH_VALUE | GIT_GLOBAL_NO_VALUE:
            if name in GIT_CONTEXT_OPTIONS:
                repo += [name, value] if name != "--config-env" else [option]
            index += 1
            continue
        if option in GIT_GLOBAL_NO_VALUE:
            index += 1
            continue
        if option not in GIT_GLOBAL_WITH_VALUE or index + 1 >= len(args):
            return f"unrecognized git global option `{option}` (the guard fails closed; drop the option)"
        value = args[index + 1]
        if option in GIT_CONTEXT_OPTIONS:
            repo += [option, value]
        if option == "-c":
            # Inline config (e.g. remote.origin.push=HEAD:main) can redirect a push.
            key, _, config_value = value.partition("=")
            reason = check_config_value(key, config_value)
            if reason:
                return f"inline config: {reason}"
        index += 2
    if index >= len(args):
        return None
    subcommand, rest = args[index], args[index + 1:]
    if via_xargs and subcommand in INSPECTED:
        return f"`xargs` supplies arguments to `git {subcommand}` that cannot be checked"
    if subcommand == "push":
        return check_push(rest, repo)
    if subcommand == "branch":
        return check_branch(rest, repo)
    if subcommand == "checkout":
        return check_create(rest, {"-b", "-B"}, 0, repo, CHECKOUT_LONG, CHECKOUT_WITH_VALUE)
    if subcommand == "switch":
        return check_create(rest, {"-c", "-C", "--create", "--force-create"}, 0, repo, CHECKOUT_LONG, CHECKOUT_WITH_VALUE)
    if subcommand == "worktree" and rest[:1] == ["add"]:
        return check_create(rest[1:], {"-b", "-B"}, 1, repo, WORKTREE_ADD_LONG, WORKTREE_ADD_WITH_VALUE)
    if subcommand == "config":
        return check_config(rest)
    if subcommand == "remote":
        return check_remote(rest)
    return None


def check_command(command: str, cwd: str | None = None) -> str | None:
    """Return a denial reason, or None if the command is allowed."""
    for tokens in split_commands(command):
        for script in nested_scripts(tokens):
            reason = check_command(script, cwd)
            if reason:
                return reason
        tokens = strip_redirections(tokens)
        for index, token in enumerate(tokens):
            if os.path.basename(token) != "git":
                continue
            via_xargs = any(os.path.basename(previous) == "xargs" for previous in tokens[:index])
            reason = check_git(tokens[index + 1:], cwd, via_xargs)
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
