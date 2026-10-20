# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Add deterministic protocol validation so protocol v3 can be safely released and used by the first consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle and ai-workflow CI enforcement.

## Active Changes

- `protocol-validator` — implementing generic deterministic v3 repository validation in `check/`.

## Human Attention

- None.

## Blockers / Risks

- Protocol validation intentionally covers structural/machine-checkable invariants only; semantic Design quality and acceptance authority remain outside deterministic validation.
- Semantic migration tooling for existing v1/v2 projects remains planned.

## Next

- Verify the protocol validator and its tests in required `core-tests`.
- Final-fold the validator Change and obtain latest-head Codex review.
- Release protocol v3 from `develop` to `main`.
- Bootstrap the first consumer project from stable v3.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- Protocol validator: `check/protocol.py`
- CI workflow: `.github/workflows/ci.yml`
- Branch protection checker: `check/branch_protection.py`
