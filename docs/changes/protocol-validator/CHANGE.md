# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Finish the protocol-v3 canonical validator so its documented grammar, generated guidance, and deterministic checks are internally consistent.

## Constraints

- Canonical protocol grammar remains narrow; no general Markdown/CommonMark/HTML parsing.
- Metadata syntax is open to additional canonical `Key: value` fields; validator extracts only fields it needs.
- Design INDEX has one canonical projection table.
- Implementing/Realized Designs use Realization Map as their first level-two section.

## Acceptance Criteria

- [ ] WORK_TRACKING guidance and generated template align with the map-first rule.
- [ ] Additional canonical metadata fields do not fail validation.
- [ ] Multiple canonical INDEX tables fail validation.
- [ ] Regression tests cover all three review findings.
- [ ] Exact-head core-tests/self-validation pass.
- [ ] Change is final-folded before latest-head Codex review.
