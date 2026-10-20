# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Close the remaining canonical-validator invariants without reintroducing general Markdown parsing.

## Constraints

- Duplicate mapped paths within one Realization Map section are invalid.
- `docs/designs/INDEX.md` is a dedicated machine-readable projection file with exactly one canonical table header occurrence; examples that repeat that header are noncanonical in this file.
- Do not add fenced-code/HTML/CommonMark interpretation.

## Acceptance Criteria

- [ ] Conflicting/duplicate mapped paths are rejected.
- [ ] INDEX contract/docs explicitly forbid repeated canonical table headers anywhere in the file.
- [ ] Regression tests cover both findings.
- [ ] Exact-head CI/self-validation pass.
- [ ] Change is final-folded before latest-head Codex review.
