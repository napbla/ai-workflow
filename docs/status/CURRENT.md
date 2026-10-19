# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Design a first-class Design PR lifecycle so consequential design can be reviewed and revised before implementation begins, while implementation PRs preserve one coherent accepted change identity.

## Active Changes

- `docs/changes/design-pr-lifecycle/CHANGE.md` — Designing, owned by the `architect` role.
- `docs/changes/design-pr-lifecycle/DESIGN.md` — current proposal for human review.

## Human Attention

- Review and comment on the Design PR, especially the open questions around when Design PRs are required and whether design branches need their own naming convention.

## Blockers / Risks

- None. This branch is design-only; protocol implementation should not begin until the design is accepted.

## Next

- Human reviews/comments on the Design PR.
- Architect explains trade-offs and revises the proposal in the same PR.
- After acceptance, merge the Design PR and create a separate implementation change.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
