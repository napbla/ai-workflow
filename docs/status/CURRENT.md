# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Release protocol v3 as stable and use it to bootstrap the first consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle, exact-head CI enforcement, and deterministic canonical-grammar validation.

## Active Changes

- `protocol-validator` — closing final canonical identity/projection invariants from review.

## Human Attention

- None.

## Blockers / Risks

- Semantic migration tooling for existing v1/v2 projects remains planned but does not block new v3 projects.
- `check/branch_protection.py` still does not verify required status checks; ai-workflow's GitHub ruleset currently enforces `core-tests` separately.

## Next

- Release protocol v3 from `develop` to `main`.
- Bootstrap the first consumer project with the stable v3 initializer.
- Create and accept that project's initial Design before implementation begins.
- Build migration tooling later for existing v1/v2 repositories.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Work tracking: `docs/WORK_TRACKING.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- Protocol validator: `check/protocol.py`
- CI workflow: `.github/workflows/ci.yml`
- Branch protection checker: `check/branch_protection.py`
