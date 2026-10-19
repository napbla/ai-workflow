# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

No objective is in progress. The project uses protocol v2: role-based agent identities with runtimes assigned at invocation, `main` as the stable branch and `develop` as the integration branch with work on `feature/<change-id>` branches, autonomous change execution up to `ready-for-human-merge`, merge-safe current status, and GitHub branch protection of `main` and `develop` as the enforcement boundary, verified by `check/branch_protection.py`.

## Active Changes

- None.

## Human Attention

- None.

## Blockers / Risks

- None. `check/branch_protection.py`, run with the implementer's credential on 2026-10-19, exited 0: an active ruleset with no bypass actors requires a PR and blocks force pushes and deletion on both `main` and `develop`. Re-run it whenever agent credentials or rulesets change.

## Next

- Define the next objective as an active change on a feature branch from `develop`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
