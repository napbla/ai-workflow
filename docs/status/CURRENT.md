# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Protocol v2 is integrated on `develop`: role-based agent identities with runtimes assigned at invocation, the `main` / `develop` / feature branch lifecycle, and autonomous change execution up to `ready-for-human-merge`. `main` still carries stable protocol v1 until v2 is released through a reviewed PR from `develop`.

## Active Changes

- None.

## Human Attention

- Configure repository-host branch protection or rulesets for `main` and `develop` (require PR, block force push and deletion). Repository policy and the Claude Code hook cannot enforce server permissions.
- Confirm the implementer-proposed decisions recorded in `docs/adr/0001-protocol-v2-roles-and-branch-model.md` (fixed protected branch names; `adapters/` module).
- Decide when to release protocol v2 from `develop` to `main`.

## Blockers / Risks

- The Claude Code protected-branch hook (`adapters/claude-code/`) is best-effort shell parsing; host branch protection is the authoritative layer.

## Next

- Release `develop` → `main` through a reviewed PR when ready.
- Set the next objective as a new active change on a feature branch from `develop`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
