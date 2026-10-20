# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Provide a generic deterministic validator for ai-workflow protocol v3 repositories using a narrow canonical protocol grammar, not general Markdown/CommonMark rendering semantics.

## Constraints

- Validate only machine-checkable protocol invariants.
- Protocol structural fields use exact canonical syntax; equivalent Markdown renderings are not accepted automatically.
- Do not parse HTML comments, fenced-code semantics, indentation variants, or other general Markdown constructs to infer protocol state.
- Keep the validator standard-library-only and read-only.
- Default target is the current working directory; support an explicit target repository path.

## Acceptance Criteria

- [ ] Canonical Design/Change metadata cannot be satisfied by body examples.
- [ ] Implementing/Realized Designs require `## Realization Map` as the first section after canonical metadata.
- [ ] Realization Map labels/order and mapped path entries use one documented exact syntax.
- [ ] INDEX uses one documented exact table syntax and remains an exact projection of realized source Areas.
- [ ] Version/required-path/Design-Revision checks remain deterministic.
- [ ] Validator docs explicitly state that general Markdown/HTML equivalence is out of scope.
- [ ] Core tests and self-validation pass on exact PR head.
- [ ] Completed Change state is folded/removed before final review.

## Non-Goals

- General Markdown/CommonMark parsing.
- HTML rendering/comment semantics.
- Semantic Design quality review.
- Git commit reachability/acceptance verification for Design-Revision.
- v1/v2 migration.
