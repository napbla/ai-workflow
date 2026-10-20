# ai-workflow — Current Project State

Updated: 2026-10-20

## Current Objective

Stabilize protocol v3 with exact-head CI enforcement before starting a consumer project.

## Designs

- `docs/designs/design-change-source-lifecycle/DESIGN.md` — Realized; maps the protocol-v3 lifecycle and its ai-workflow CI realization.

## Active Changes

- `ci-required-checks` — adding GitHub Actions `core-tests` and required-check enforcement for protected branches.

## Human Attention

- After `core-tests` has run on this repository, configure GitHub protection for both `main` and `develop` to require that check. The connected runtime can edit repository files but cannot mutate GitHub rulesets/branch-protection settings.

## Blockers / Risks

- CI workflow exists on this feature branch, but required-check enforcement is not yet verified.
- `check/branch_protection.py` currently verifies PR/force-push/deletion protection only; it does not verify required status checks.
- Semantic migration tooling for existing v1/v2 projects remains planned.

## Next

- Run `core-tests` on the CI Change PR.
- Require `core-tests` on `main` and `develop`.
- Verify enforcement, final-fold the Change, and obtain reviewer/CI verdict on the exact final head.

## Current Truth References

- Protocol contract: `spec/SPEC.md`
- Workflow: `WORKFLOW.md`
- Design traceability: `docs/designs/INDEX.md`
- Designs: `docs/designs/`
- Active changes: `docs/changes/`
- CI workflow: `.github/workflows/ci.yml`
- Branch protection checker: `check/branch_protection.py`
- Cross-cutting decisions: `docs/adr/`
