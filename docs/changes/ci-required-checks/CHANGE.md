# Add CI and Required Checks

Status: In Progress
Owner: implementer

Design: docs/designs/design-change-source-lifecycle/DESIGN.md
Design-Revision: 305121fb9b24bb31c753044a8262b0380882bc71

## Goal

Make exact-head automated verification real for ai-workflow pull requests by adding GitHub Actions CI for the core test suites and documenting/configuring the corresponding required check boundary.

## Constraints

- Keep CI small and deterministic.
- Run on pull requests targeting `develop` or `main`.
- Do not add deployment, release, migration, or protocol validation work here.
- Repository-host protection remains the authoritative merge enforcement boundary.
- If the connected runtime cannot mutate GitHub protection/rulesets, record the exact human setup action instead of claiming enforcement exists.

## Acceptance Criteria

- [ ] A GitHub Actions workflow runs the init and check unit tests on PRs targeting `develop` or `main`.
- [ ] The workflow uses a stable, explicit job/check name suitable for branch protection.
- [ ] CI installs only the dependencies required by the current tests.
- [ ] Human setup documentation states which check must be required on both protected branches.
- [ ] The lifecycle Design realization map/index include the CI implementation if it is part of current realization.
- [ ] `docs/status/CURRENT.md` accurately distinguishes CI availability from required-check enforcement.
- [ ] Completed Change state is folded/removed before final review.
- [ ] Codex reviews the exact final head after the workflow and fold are complete.

## Non-Goals

- Protocol structure validator.
- Semantic migration tooling.
- Release automation.
- Consumer-project CI templates.
