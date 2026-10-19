# Claude Code adapter

`protected_branch_guard.py` is a Claude Code `PreToolUse` hook that enforces the protected branch policy from `WORKFLOW.md` on Bash tool calls.

It blocks (exit code 2, reason returned to Claude):

- pushes whose destination is `main` or `develop`, including `HEAD:main`, `+develop`, `:develop` (delete), and wildcard refspecs;
- `git push --all`, `--branches`, and `--mirror`;
- refspec-less `git push` from `main`/`develop`, or from a branch whose upstream is `main`/`develop`;
- setting `main`/`develop` as upstream: `git branch -u/--set-upstream-to`, `git config branch.<b>.merge`, `git config remote.<r>.push`, and creating a branch from `origin/main`/`origin/develop` without `--no-track`.

Normal feature-branch pushes such as `git push -u origin feature/<change-id>` are allowed. Commands are checked through `&&`, `;`, pipes, newlines, and `sh/bash/zsh -c`.

This is best-effort parsing of shell text, not a security boundary: variables, aliases, or scripts can evade it. Repository-host branch protection is the authoritative layer.

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
