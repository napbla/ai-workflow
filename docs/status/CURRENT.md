# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Fix protocol-v2 status semantics so `docs/status/CURRENT.md` contains merge-safe current truth and does not become stale merely because a PR is merged.

## Active Changes

- `docs/changes/fix-current-status-semantics/CHANGE.md` — Planned, owned by the `implementer` role.

## Human Attention

- None.

## Blockers / Risks

- Keep this change narrowly scoped to status semantics.
- Do not mix in CI, migration tooling, or unrelated protocol changes.

## Next

- Update workflow and generated templates with merge-safe `CURRENT.md` rules.
- Replace stale release-relative status with durable protocol-v2 current truth.
- Open a PR from this feature branch to `develop`, then run independent review until the latest head is ready for human merge.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
