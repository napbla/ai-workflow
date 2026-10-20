# Work Tracking Rules

This file defines when project state must be written to the repository.

## Principle

Use the minimum artifact needed for another human or agent to continue without the current conversation.

The repository is canonical. Git preserves history; active artifacts should describe current target/coordination state rather than historical narration.

## Decision Test

Ask:

> Will another human or agent need this after the current conversation, coding session, branch, or review disappears?

- **No** → keep it temporary.
- **Yes** → materialize it in the appropriate repository surface.

## 1. Exploration

Brainstorming, discarded ideas, and unresolved discussion may stay in Chat.

Materialize repository state when discussion produces:

- an accepted/proposed target Design needing review
- committed implementation work
- a durable requirement/constraint
- a cross-session blocker/open question
- a decision future agents must understand

## 2. Designs

Use `docs/designs/<design-id>/DESIGN.md` when target state itself needs durable review or guidance.

A brand-new project must have an initial Design before implementation.

Use a Design for consequential existing-project work when product intent, architecture, contracts, constraints, or trade-offs need human review. Small/local changes may skip a separate Design when target state is obvious.

Default branch:

```text
design/<design-id>
```

Recommended shape while `Proposed` or `Accepted`:

```md
# Design Title

Status: Proposed | Accepted
Owner: architect

## Goal

## Target Behavior / Architecture

## Constraints

## Trade-offs / Rationale
```

Once implementation starts, switch to `Status: Implementing` and make `## Realization Map` the **first level-two section** after metadata:

```md
# Design Title

Status: Implementing | Realized
Owner: architect

## Realization Map

Changes:
- `change-id` — in progress

Areas:
- `src/**` — Target

Tests:
- `tests/**` — Target

Current-truth docs:
- `docs/architecture/example.md` — Target

## Goal

## Target Behavior / Architecture

## Constraints

## Trade-offs / Rationale
```

While `Proposed`, intent/architecture/scope may evolve freely.

Before final acceptance, fold review outcomes into canonical sections and remove review-provenance/transient summary sections. Human acceptance is bound to the exact final Design PR head.

### Realization Map

Once implementation starts, track:

- derived Changes
- source areas
- tests
- current-truth docs

Each mapped area is:

- `Target` — accepted target, not evidence of implementation
- `Realized` — currently implemented and explained by this Design

A Design can be `Implementing` overall while some areas are already `Realized`.

## 3. Design Traceability Index

Maintain `docs/designs/INDEX.md` as a lightweight reverse-lookup projection of **realized mappings only**.

It is navigation, not canonical implementation truth and not history.

If the index disagrees with a Design's Realization Map, the Design file wins and the index must be corrected.

Whenever any source change moves/replaces/removes/materially changes a mapped area, update all affected Design maps and index entries before final review — even if the source change came from a different Design, direct Change, or small fix.

## 4. Active Changes

Use `docs/changes/<change-id>/CHANGE.md` for non-trivial committed implementation work needing cross-session/cross-agent coordination.

Default branch:

```text
feature/<change-id>
```

Recommended shape:

```md
# Change Title

Status: Planned | In Progress | Blocked | Verifying
Owner: <role-id>

Design: docs/designs/<design-id>/DESIGN.md
Design-Revision: <accepted-design-commit-sha>

## Goal

## Constraints

## Acceptance Criteria

- [ ] ...

## Notes
```

The Design fields are required when the Change derives from an accepted Design; direct Changes may omit them.

Change identity is:

> accepted intent + acceptance criteria + explicit non-negotiable constraints

Implementation plan is not identity.

If a Design revision changes, the architect revalidates every incomplete Change mapped to it. A continuing Change must update `Design-Revision` to the newly accepted revision before work resumes.

## 5. Small Fixes

A small local fix may omit a Change artifact when:

- scope is obvious
- risk is low
- one session/agent can complete it
- no persistent coordination context is needed

Code/tests/commit/PR may be enough, but affected current truth and Design realization mappings still must be updated.

## 6. Feedback and Implementation Pivots

PR comments/reviews are coordination surfaces.

Feedback stays in the same Change when accepted Change identity remains unchanged.

Examples:

- library A → library B
- webhook → polling
- API permission forces another mechanism
- internal module boundaries change without changing accepted behavior/constraints

Restart the Change when accepted intent, acceptance criteria, or explicit non-negotiable constraints materially change.

If feedback changes the accepted target Design, revise and accept the Design first, then revalidate/rebind or replace affected Changes.

Do not copy every review comment into durable docs.

## 7. ADRs

Default decision rationale belongs in the relevant Design.

Create/update an ADR only when rationale:

- cuts across multiple Designs
- must live independently of one Design
- remains important after a Design is superseded

Do not use ADRs as a changelog.

## 8. Partial Supersession

An accepted/implementing replacement Design does not supersede current realized mapping by itself.

When replacement source for one area becomes real, update atomically in the same final reviewed head:

1. implement replacement source
2. mark replacement Design area `Realized`
3. remove/update/split that area from the old Design's realized map
4. switch `docs/designs/INDEX.md`

This keeps reverse lookup truthful throughout multi-Change replacement.

## 9. Completing a Change

Before final review/merge:

1. verify acceptance criteria
2. fold durable truth into code/tests/module docs/specs/architecture
3. update every affected Design Realization Map
4. update `docs/designs/INDEX.md`
5. set Design status appropriately (`Implementing` or `Realized`)
6. update cross-cutting ADR only if needed
7. make `docs/status/CURRENT.md` merge-safe
8. remove `docs/changes/<change-id>/`
9. push final head
10. run independent review/CI on that exact final head

Any later push makes the clean verdict stale.

## 10. Design Retention

A `Realized` Design remains while it is useful as a current conceptual map of implemented code.

Remove it only when fully superseded or no longer useful. Before removal, move still-relevant knowledge into replacement Design/current architecture/spec/module docs.

Do not archive it separately; Git preserves history.

## 11. Current-State Rule

A replacement agent should not need completed Change files or old chats.

If removing `CHANGE.md` would remove knowledge needed to operate/modify the system, fold that knowledge first.

A realized Design may remain because it is current conceptual/traceability state, not historical bookkeeping.
