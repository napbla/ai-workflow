# Claude Code adapter

`protected_branch_guard.py` is a Claude Code `PreToolUse` hook that enforces the protected branch policy from `WORKFLOW.md` on Bash tool calls.

It blocks (exit code 2, reason returned to Claude):

- pushes whose destination is `main` or `develop`, including `HEAD:main`, `+develop`, `:develop` (delete), matching (`:`), and wildcard refspecs;
- `git push --all`, `--branches`, `--mirror`;
- pushes redirected to `main`/`develop` by configuration: `push.default=matching`, `push.default=upstream` with a protected upstream, a remote's `remote.<name>.push` mapping or mirror setting, and refspec-less pushes from `main`/`develop`;
- making `main`/`develop` an upstream or push target: `git branch -u/--set-upstream-to`, writes to `branch.<b>.merge`, `remote.<r>.push`, `remote.<r>.mirror`, or `push.default=matching`, `git remote add --mirror[=push]`, and creating a branch (`checkout -b`, `switch -c`, `branch`, `worktree add -b`) from a protected remote-tracking start point without `--no-track`.

Normal feature-branch work is allowed, including `git push -u origin feature/<change-id>` and commit messages or PR bodies that mention `main` or `develop`.

## How it checks

- Every `git` word in the command is analyzed wherever it appears, including after shell keywords (`if`, `!`, `{`, `do`), wrappers (`env`, `sudo`, `timeout`, `nice`), and pipes. An unquoted phrase such as `echo git push origin main` is therefore treated as a git command; quote it.
- Nested command strings are checked recursively: `sh/bash/zsh -c`, heredocs and here-strings fed to a shell, `eval`, and `env -S`.
- Quoted strings and heredoc bodies that are not fed to a shell are treated as data. Redirections (`>/dev/null`, `2>&1`) are ignored.
- Options are normalized the way Git parses them: unique long-option prefixes, short-option clusters, attached values, and last-wins `--track`/`--no-track`.
- Ref expressions (`@{u}`, `main@{upstream}`, `-`, abbreviations) are resolved with `git rev-parse` in the same repository and with the same `-C`, `--git-dir`, `--work-tree`, `-c`, and `--config-env` options as the command.
- It fails closed on unrecognized git global options and on `xargs`-supplied arguments to inspected git subcommands.
- Config reads and removals (`--get`, `--unset`, `git config get`, ...) are allowed; only writes are checked.

This is best-effort parsing of shell text, not a security boundary. Shell variables and expansions, aliases, scripts, backtick substitutions, and `GIT_*` environment variables can evade it. Repository-host branch protection is the authoritative layer.

## Install

Copy `protected_branch_guard.py` into the project (this monorepo uses it in place) and register it in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/adapters/claude-code/protected_branch_guard.py" }
        ]
      }
    ]
  }
}
```

## Test

```bash
python -m unittest discover -s adapters/claude-code/tests
```
