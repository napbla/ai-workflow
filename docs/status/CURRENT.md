# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Stabilize protocol v3 after implementing the accepted Design → Change → Source lifecycle, then add CI/required-check automation before starting a consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle implementation.

## Active Changes

- None.

## Human Attention

- None.

## Blockers / Risks

- CI required checks are not yet implemented, so latest-head test/review evidence is not yet enforced automatically by GitHub checks.
- Semantic migration tooling for existing v1/v2 projects is still planned.

## Next

- Implement CI / required checks for core tests and final-head merge readiness.
- Implement semantic migration tooling after CI is established.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- Current specs: `docs/specs/`
- Current architecture: `docs/architecture/`
- Cross-cutting decisions: `docs/adr/`
