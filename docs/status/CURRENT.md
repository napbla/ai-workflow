# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Protocol v2 is integrated on `develop`: role-based agent identities with runtimes assigned at invocation, the `main` / `develop` / feature branch lifecycle, autonomous change execution up to `ready-for-human-merge`, and GitHub branch protection as the enforcement boundary for `main` and `develop`, verified by `check/branch_protection.py`. `main` still carries stable protocol v1 until v2 is released through a reviewed PR from `develop`.

## Active Changes

- None.

## Human Attention

- Confirm the implementer-proposed fixed protected branch names (decision 3 in `docs/adr/0001-protocol-v2-roles-and-branch-model.md`).
- Decide when to release protocol v2 from `develop` to `main`.

## Blockers / Risks

- None. `check/branch_protection.py`, run with the implementer's credential on 2026-10-19, exited 0: an active ruleset with no bypass actors requires a PR and blocks force pushes and deletion on both `main` and `develop`. Re-run it whenever agent credentials or rulesets change.

## Next

- Release `develop` → `main` through a reviewed PR when ready.
- Set the next objective as a new active change on a feature branch from `develop`.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
