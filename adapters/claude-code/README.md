# Claude Code adapter

`protected_branch_guard.py` is a Claude Code `PreToolUse` hook that enforces the protected branch policy from `WORKFLOW.md` on Bash tool calls.

It blocks (exit code 2, reason returned to Claude):

- pushes whose destination is `main` or `develop`, including `HEAD:main`, `+develop`, `:develop` (delete), matching (`:`), and wildcard refspecs;
- `git push --all`, `--branches`, `--mirror`;
- pushes redirected to `main`/`develop` by configuration: `push.default=matching`, `push.default=upstream` with a protected upstream, a remote's `remote.<name>.push` mapping or mirror setting, and refspec-less pushes from `main`/`develop`;
- making `main`/`develop` an upstream or push target: `git branch -u/--set-upstream-to`, copying or renaming a branch that tracks them, writes to `branch.<b>.merge`, `remote.<r>.push`, `remote.<r>.mirror`, `push.default=matching`, or `branch.autoSetupMerge=always|inherit`, `git remote add --mirror[=push]`, and creating a branch (`checkout -b`, `switch -c`, `branch`, `worktree add -b`) from a protected remote-tracking start point without `--no-track`.

Normal feature-branch work is allowed, including `git push -u origin feature/<change-id>` and commit messages or PR bodies that mention `main` or `develop`.

## How it checks

- Git invocations are found in command position: the first word of each simple command, after assignments, shell keywords (`if`, `!`, `{`, `do`, ...), and wrapper commands with their options (`env -u X`, `sudo -u user`, `timeout 30`, `nice -n 5`, `xargs -n1`), and the target of `find -exec`. A word `git` used as an argument (`grep -rn git`, `brew install git`) is not a command. As a backstop for wrappers the guard does not model (e.g. `arch`, custom scripts), a `git` word followed by an inspected subcommand (`push`, `branch`, `checkout`, `switch`, `config`, `remote`, `worktree`) anywhere in the arguments is checked too, so quote prose such as `echo 'git push origin main'`.
- Nested command strings are checked recursively: `sh/bash/zsh/dash/ksh -c`, heredocs and here-strings fed to a shell, `echo`/`printf` output piped into a shell (including `bash -s`, `bash -`, `bash /dev/stdin`), `eval`, `trap`, and `env -S`. Input the guard cannot reconstruct — `printf` formats with `%`, backslash escapes other than `\n`, or any other command piped into a shell (`cat x | bash`, `curl ... | sh`) — is denied.
- Quoted strings and heredoc bodies that are not fed to a shell are treated as data. Redirections (`>/dev/null`, `2>&1`) are ignored.
- Options are normalized the way Git parses them: unique long-option prefixes, short-option clusters, attached values, and last-wins `--track`/`--no-track`.
- Ref expressions (`@{u}`, `main@{upstream}`, `-`, abbreviations) are resolved with `git rev-parse` in the same repository and with the same `-C`, `--git-dir`, `--work-tree`, `-c`, and `--config-env` options as the command, so inline config is judged by its real effect.
- New branches follow Git's tracking rules: explicit `--track`/`--track=inherit`/`--no-track`, otherwise `branch.autoSetupMerge`; with no start point, the start is `HEAD`. Renaming a config section into `branch.*`/`remote.*` is allowed only for same-kind renames in the repository's own config whose settings do not involve protected branches. Copying or renaming a branch (`git branch -c/-m`) is checked against the source branch's upstream.
- The working directory is tracked through `cd`, `pushd`, `popd`, `env -C`, and `sudo -D`, scoped to subshells and nested scripts, so repository state is read from the repository the command actually runs in.
- It fails closed on unrecognized git global options, on `xargs`-supplied arguments to inspected git subcommands, and on inspected git subcommands after a directory change it cannot resolve literally (`cd "$VAR"`, `cd -` without a known previous directory).
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
