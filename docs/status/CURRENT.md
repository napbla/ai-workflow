# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Implement protocol v2 with runtime-neutral roles, the `main` / `develop` / feature lifecycle, autonomous PR execution, and simplified GitHub-enforced branch protection.

## Active Changes

- `docs/changes/protocol-v2-simplified-branch-protection/CHANGE.md` — Planned, owned by the `implementer` role.

## Human Attention

- Configure GitHub branch protection/rulesets for `main` and `develop` if verification reports they are missing or unverifiable.

## Blockers / Risks

- Do not reintroduce local shell/Git semantic parsing as a protection mechanism.
- GitHub repository-host protection is the authoritative enforcement boundary.
- The replacement implementation should selectively reuse valid work from closed PR #2 without carrying forward its complex Claude guard.

## Next

- Implementer reads the active change and implements the smallest coherent protocol-v2 design.
- Reuse valid PR #2 work selectively.
- Add a simple GitHub branch-protection verification path.
- Open a PR from this feature branch to `develop`; do not target `main`.
- Iterate with an independent reviewer until the latest head is `ready-for-human-merge`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
