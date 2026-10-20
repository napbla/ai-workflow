# Add Deterministic Protocol Validator

Status: In Progress
Owner: implementer

## Goal

Add a generic deterministic validator for ai-workflow protocol v3 repositories so structural protocol drift is caught automatically before merge and the same validator can be used on the first consumer project.

## Constraints

- Validate only machine-checkable invariants; semantic/product judgment remains with agents/humans.
- Keep the validator standard-library-only.
- Default target is the current working directory; support an explicit target repository path.
- Validate against the protocol version shipped by this ai-workflow checkout.
- Do not add migration behavior or mutate target repositories.

## Acceptance Criteria

- [ ] `python check/protocol.py --target <repo>` validates a protocol-v3 repository deterministically.
- [ ] It checks protocol marker/version and required repository paths.
- [ ] It checks WORKFLOW protocol version consistency.
- [ ] It validates Design status and actual Realization Map shape for Implementing/Realized Designs.
- [ ] It validates INDEX as an exact projection of per-Design realized source Areas.
- [ ] It detects duplicate realized source-area ownership across Designs.
- [ ] It validates Design-derived active Changes have an existing Design and a Design-Revision.
- [ ] Unit tests cover valid initialized repos and representative invalid states.
- [ ] `core-tests` runs the protocol validator against ai-workflow itself.
- [ ] Documentation explains scope, exit codes, and limitations.
- [ ] Affected Design realization map/index are updated.
- [ ] Completed Change state is removed before final review.

## Non-Goals

- GitHub ruleset/branch-protection validation.
- Semantic Design quality review.
- Git commit reachability/acceptance verification for Design-Revision.
- v1/v2 migration.
