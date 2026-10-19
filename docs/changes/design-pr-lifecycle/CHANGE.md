# Design PR Lifecycle and Change Identity

Status: Designing
Owner: architect

## Goal

Formalize the lessons learned from the protocol-v2 rollout about design review, implementation identity, reviewer ownership, and implementation pivots.

This change is currently in the **design phase only**. No protocol implementation should begin until the human accepts the design.

## Design Decisions Under Review

1. Every brand-new project must have human-reviewable design before implementation.
2. Design is a phase of the normal `feature/<change-id>` PR, not a separate branch namespace.
3. Human acceptance transitions the same PR from design to implementation; design is not merged separately.
4. Accepted future-state design remains active-change state until its implementation is ready to merge.
5. Implementation identity is accepted intent + acceptance criteria + explicit non-negotiable constraints.
6. Strategy/architecture/scope pivots stay in the same PR when that identity remains unchanged.
7. Identity-changing feedback after acceptance starts a new change/PR.
8. Reviewer, not implementer, owns the clean verdict on the latest head.
9. Runtime-specific PR monitoring/autofix remains optional acceleration, not core protocol semantics.

## Acceptance Criteria for the Design Phase

- [x] The lifecycle is clear enough to apply to a brand-new project.
- [x] Brand-new projects require design before implementation.
- [x] Design review can evolve intent, architecture, scope, constraints, and acceptance criteria before human acceptance.
- [x] Accepted design is preserved canonically on the active feature branch until implementation completes.
- [x] No separate `design/<id>` namespace is required without a distinct operational boundary.
- [x] Future-state design does not merge into integration/stable truth ahead of the code that realizes it.
- [x] Implementation identity is explicit and distinct from implementation plan.
- [x] Constraint-driven implementation pivots stay in the same PR when identity is unchanged.
- [x] Identity-changing feedback after implementation starts requires a new change/PR.
- [x] Reviewer owns the clean-review verdict on the latest head.
- [x] Runtime-specific PR monitoring/autofix remains outside core semantics.
- [x] The proposal identifies the protocol/operator files to update after acceptance.

## Non-Goals

- Implementing CI required checks.
- Implementing migration tooling.
- Adding vendor-specific Claude or Codex configuration to the core protocol.
- Changing protocol version during the design phase.
