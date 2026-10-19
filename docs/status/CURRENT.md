# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Design and implement protocol v2 on `feature/generalize-agent-runtime-model`, including the stable `main` / integration `develop` / feature-branch lifecycle and runtime-neutral agent roles.

## Active Changes

- `docs/changes/generalize-agent-runtime-model/CHANGE.md` — Planned, owned by the `implementer` role.

## Human Attention

- GitHub server-side branch protection/rulesets still require operator configuration because repository policy alone cannot enforce server permissions.

## Blockers / Risks

- This is a semantic protocol change; generated/self-bootstrap state must remain internally consistent.
- Runtime-specific enforcement must not leak vendor assumptions into the core protocol.
- Branch-local status must not become stale when feature work is integrated.

## Next

- Implementer reads the active change and implements the smallest coherent protocol-v2 design.
- Add modular Claude protected-branch enforcement and tests.
- Open a PR from this feature branch to `develop`; do not target `main`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
