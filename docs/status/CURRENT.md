# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Finish the protocol-v3 validator with a narrow canonical grammar, then release v3 as stable and bootstrap the first consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle, exact-head CI enforcement, and deterministic protocol validation.

## Active Changes

- `protocol-validator` — simplifying validation from Markdown-aware parsing to canonical protocol syntax.

## Human Attention

- None.

## Blockers / Risks

- Semantic migration tooling for existing v1/v2 projects remains planned but does not block new v3 projects.

## Next

- Validate the simplified canonical grammar in required `core-tests`.
- Final-fold the validator Change and obtain latest-head Codex review.
- Release protocol v3 from `develop` to `main`.
- Bootstrap the first consumer project with stable v3.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- Protocol validator: `check/protocol.py`
- CI workflow: `.github/workflows/ci.yml`
