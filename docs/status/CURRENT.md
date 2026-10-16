# ai-workflow — Current Project State

Updated: 2026-10-16

## Current Objective

Add a minimal `--version` flag to the initializer while keeping `spec/VERSION` as the single protocol-version source of truth.

## Active Changes

- `docs/changes/add-init-version-flag/CHANGE.md` — Verifying, owned by `claude-code`. Implemented on branch `add-init-version-flag`; awaiting PR and review.

## Human Attention

- `claude-code` could not reach `origin` (SSH `Permission denied (publickey)` for host `github-personal`) and `gh` is not installed, so the branch is not pushed and no PR exists yet. Operator: load the `GithubPersonal` key into ssh-agent (or push the branch) so the PR can be opened.

## Blockers / Risks

- None.

## Next

- Push `add-init-version-flag` and open a PR; Codex reviews.
- Before merge, remove `docs/changes/add-init-version-flag/`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
