# Claude Code adapter

`protected_branch_guard.py` is a Claude Code `PreToolUse` hook that enforces the protected branch policy from `WORKFLOW.md` on Bash tool calls.

It blocks (exit code 2, reason returned to Claude):

- pushes whose destination is `main` or `develop`, including `HEAD:main`, `+develop`, `:develop` (delete), and wildcard refspecs;
- `git push --all`, `--branches`, `--mirror`, matching pushes (`git push origin :`), and `push.default=matching` (via `-c` or `git config`, or already configured for a refspec-less push);
- refspec-less `git push` from `main`/`develop`, from a branch whose upstream is `main`/`develop`, or to a remote whose configured `remote.<name>.push` targets them or that is configured to mirror;
- setting `main`/`develop` as upstream: `git branch -u/--set-upstream-to`, `git config branch.<b>.merge`, `git config remote.<r>.push`, and creating a branch from `origin/main`/`origin/develop` without `--no-track` (including attached forms such as `-bname` and `--create=name`).

The repository checked is the one Git would use, including `-C`, `--git-dir`, and `--work-tree`.

Normal feature-branch pushes such as `git push -u origin feature/<change-id>` are allowed. Commands are checked through `&&`, `;`, pipes, newlines, and `sh/bash/zsh -c`. Quoted strings and heredoc bodies are treated as data, so commit messages and PR bodies that mention `main` or `develop` are not blocked.

Inline `git -c` settings that redirect a push (`remote.*.push`, `branch.*.merge`, `push.default=matching`, `remote.*.mirror`) are checked like `git config`. Heredocs fed to a shell (`bash <<EOF`) are checked as commands.

This is best-effort parsing of shell text, not a security boundary: variables (including `GIT_DIR=...` prefixes), aliases, scripts, and backtick substitutions can evade it. Repository-host branch protection is the authoritative layer.

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
