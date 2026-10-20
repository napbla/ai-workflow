# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Reject dangling symlinks returned by Realized glob mappings.

## Constraints

- Every glob match must exist after symlink resolution.
- Every glob match must remain within the resolved repository root.
- Keep the validator standard-library-only and canonical-grammar-focused.

## Acceptance Criteria

- [ ] Dangling symlink matched by a Realized glob is rejected.
- [ ] Exact-head core-tests/self-validation pass.
- [ ] Change is final-folded before latest-head Codex review.
