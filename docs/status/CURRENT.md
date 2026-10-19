# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Design and implement protocol v2 on `feature/generalize-agent-runtime-model`, including the stable `main` / integration `develop` / feature-branch lifecycle and runtime-neutral agent roles.

## Active Changes

- `docs/changes/generalize-agent-runtime-model/CHANGE.md` — Verifying, owned by the `implementer` role; PR to `develop` under review.

## Human Attention

- GitHub server-side branch protection/rulesets still require operator configuration because repository policy alone cannot enforce server permissions.

## Blockers / Risks

- This is a semantic protocol change; generated/self-bootstrap state must remain internally consistent.
- Runtime-specific enforcement must not leak vendor assumptions into the core protocol.
- Branch-local status must not become stale when feature work is integrated.

## Next

- Implementer executes the active change on this feature branch.
- Run tests, commit, and push only this feature branch.
- Create/update a PR targeting `develop`, consume review/CI feedback, and iterate until `ready-for-human-merge`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
