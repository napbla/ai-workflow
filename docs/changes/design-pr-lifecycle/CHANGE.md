# Design PR Lifecycle and Change Identity

Status: Designing
Owner: architect

## Goal

Formalize the lessons learned from the protocol-v2 rollout about how design work, implementation work, review, and implementation pivots should be represented.

This change is currently in the **design phase only**. No protocol implementation should be changed until this design is accepted.

## Design Questions

1. When should a project or consequential change get a Design PR before implementation?
2. What is allowed to change inside a Design PR?
3. What defines the identity of an implementation change/PR?
4. When does implementation feedback stay in the same PR versus require a new change?
5. How should implementation constraints that force a different strategy be handled?
6. Who owns the final review verdict on the latest implementation head?
7. How should vendor-specific automation such as Claude PR watchers/autofix loops fit without entering core protocol semantics?

## Acceptance Criteria for the Design Phase

- [ ] The Design PR lifecycle is clear enough to apply to a brand-new project.
- [ ] Design PRs explicitly allow the proposed intent, architecture, scope, and acceptance criteria to evolve during review.
- [ ] Accepted design is separated from implementation work.
- [ ] Implementation change identity is defined by accepted intent + acceptance criteria, not by the original implementation plan.
- [ ] Implementation pivots caused by discovered constraints stay in the same implementation PR when intent and acceptance criteria are unchanged.
- [ ] Material changes to accepted intent/acceptance criteria after implementation starts require a new change/PR.
- [ ] The reviewer, not the implementer, owns the clean-review verdict on the latest head.
- [ ] Runtime-specific PR monitoring/autofix features remain optional adapters, not core protocol requirements.
- [ ] The design identifies what should be implemented in WORKFLOW/HUMAN_SETUP/templates if accepted.

## Non-Goals

- Implementing CI required checks.
- Implementing migration tooling.
- Adding vendor-specific Claude or Codex configuration to the core protocol.
- Changing protocol version during the design phase.
