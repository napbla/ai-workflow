# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Close the remaining canonical validator invariants found in latest-head review.

## Constraints

- Keep the validator protocol-aware, not Markdown-aware.
- Reject duplicate Change identifiers in Realization Maps.
- Require INDEX row labels to match their linked Design directory IDs.
- Reject duplicate realized-area entries in an INDEX row before set projection.

## Acceptance Criteria

- [ ] Regression tests cover all three findings.
- [ ] Exact-head core-tests/self-validation pass.
- [ ] Change is final-folded before latest-head Codex review.
