# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Ensure realized mappings cannot escape the target repository through symlinks.

## Constraints

- Resolve both direct realized mappings and glob matches against the resolved repository root.
- Reject mappings whose resolved target is outside the repository.
- Keep the validator standard-library-only and canonical-grammar-focused.

## Acceptance Criteria

- [ ] Direct symlink escape is rejected.
- [ ] Glob matches that resolve outside the repository are rejected.
- [ ] Exact-head core-tests/self-validation pass.
- [ ] Change is final-folded before latest-head Codex review.
