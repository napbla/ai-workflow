# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Finish internal consistency of the protocol-v3 canonical validator, then release v3 as stable and bootstrap the first consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle, exact-head CI enforcement, and deterministic canonical-grammar validation.

## Active Changes

- `protocol-validator` — reconciling canonical grammar with generated guidance and final review findings.

## Human Attention

- None.

## Blockers / Risks

- Semantic migration tooling for existing v1/v2 projects remains planned but does not block new v3 projects.

## Next

- Pass required `core-tests` on the consistency fixes.
- Final-fold and obtain latest-head Codex review.
- Release protocol v3 from `develop` to `main`.
- Bootstrap the first consumer project with stable v3.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Work tracking: `docs/WORK_TRACKING.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- Protocol validator: `check/protocol.py`
- CI workflow: `.github/workflows/ci.yml`
