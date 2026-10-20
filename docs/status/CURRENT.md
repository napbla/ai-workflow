# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Stabilize protocol v3 with enforced exact-head CI, then add deterministic protocol validation before starting a consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle and ai-workflow CI enforcement.

## Active Changes

- None.

## Human Attention

- None.

## Blockers / Risks

- `check/branch_protection.py` verifies PR/force-push/deletion protection but does not yet verify required status checks.
- Semantic migration tooling for existing v1/v2 projects remains planned.

## Next

- Add deterministic protocol validation in `check/`.
- Release protocol v3 from `develop` to `main` after validation is integrated.
- Start the first consumer project with the stable v3 initializer and initial Design PR.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- CI workflow: `.github/workflows/ci.yml`
- Branch protection checker: `check/branch_protection.py`
- Cross-cutting decisions: `docs/adr/`
