# Proposal: Design Phase in the Feature PR Lifecycle

## Problem

The v2 rollout exposed two different phases that should not share the same mutation rules:

1. **Design phase** exists to converge on what should be built.
2. **Implementation phase** exists to realize an already accepted change identity.

Treating them identically creates two opposite failures:

- freezing intent too early makes design review unnecessarily expensive;
- allowing an implementation PR to continuously redefine its goal makes it impossible to review coherently.

The workflow should model the phase transition explicitly without creating a second branch namespace or merging future-state design ahead of implementation.

## Decision Summary

- Every brand-new project starts with a human-reviewable design before implementation.
- Consequential changes to an existing project also begin with a design phase when architecture, contracts, or product behavior need human review.
- The normal branch remains `feature/<change-id>`; there is no `design/<id>` namespace by default.
- The PR opens during the design phase and remains the same PR through implementation.
- Human acceptance freezes the implementation change identity and transitions the PR from design to implementation.
- The design is **not merged separately** into `develop` before implementation.
- Active design artifacts stay under `docs/changes/<change-id>/` while implementation is in progress.
- Before final merge, durable accepted design is folded into current truth (`docs/architecture/`, `docs/specs/`, ADRs, code/tests/module docs as appropriate) and the active change artifacts are removed.

This preserves one coherent change while still giving the human a concrete PR surface for design review.

## Lifecycle

### Brand-new project

A brand-new project must have an initial design as the guide before implementation begins.

```text
Human ↔ Architect exploration
        ↓
feature/<change-id>
        ↓
CHANGE.md + DESIGN.md
        ↓
PR opens in DESIGNING phase
        ↓
Human comments / questions
        ↓
Architect explains + revises design
        ↓
Human accepts design
        ↓
same PR transitions to IMPLEMENTING
        ↓
Implementer builds against accepted design
        ↓
Reviewer / CI loop
        ↓
fold durable design into current truth
        ↓
remove active change artifacts
        ↓
ready-for-human-merge
        ↓
Human merges → develop
```

The design is the guide for implementation, but it remains active-change state until the implementation that realizes it is ready to merge.

### Existing project

For an existing project, use the same design phase when the change is consequential enough that the human should review architecture, contracts, product behavior, or other durable decisions before implementation.

Small/local changes may skip a separate `DESIGN.md` and move directly from accepted intent to implementation.

## What May Change During Design

A PR in the design phase is a proposal surface. The following may evolve in the same PR:

- product intent;
- acceptance criteria;
- architecture;
- scope;
- contracts;
- explicit constraints;
- milestones;
- trade-offs.

The architect answers review comments and updates the proposal until the human accepts it.

Acceptance is a lifecycle transition, not a merge:

```text
DESIGNING
   ↓ human accepts
IMPLEMENTING
```

After that transition, the accepted change identity is frozen unless the human explicitly changes it.

## Implementation Change Identity

The implementation change identity is defined by:

> accepted intent + acceptance criteria + explicit non-negotiable constraints

It is **not** defined by the original implementation plan, internal structure, library choice, or mechanism.

Therefore implementation strategy may evolve freely inside the same PR when the accepted change identity remains unchanged.

Examples that stay in the same PR:

- library A is unavailable, use library B;
- webhook is unavailable, use polling;
- an API permission prevents one approach, use another;
- internal module boundaries change while preserving the accepted behavior and constraints;
- reviewer asks for a safer or simpler implementation of the same requirement.

Architecture or scope changing during implementation is **not by itself** a restart trigger. It requires a new change only when it changes the accepted intent, acceptance criteria, or explicit non-negotiable constraints.

If an implementation pivot creates a durable architectural or operational decision, fold that consequence into the appropriate current-truth surface before merge. Otherwise Git/PR history is sufficient.

## When to Restart the Change

After design acceptance, close the current PR/change and start a new one when human feedback materially changes the accepted change identity:

- intent changes;
- acceptance criteria change materially;
- an explicit non-negotiable constraint is added, removed, or changed such that the accepted job is different.

A replacement change may carry forward still-valid artifacts such as:

- end-to-end/regression tests;
- verified findings;
- reusable implementation fragments;
- research evidence.

The new change must state its new identity explicitly.

Invariant:

> One implementation phase represents one coherent accepted change identity.

## Why There Is No `design/<id>` Namespace

A separate branch namespace would be useful only if design branches had materially different repository permissions, tooling, retention, or merge behavior.

They do not.

The branch is carrying one change through multiple phases, so `feature/<change-id>` remains the simplest accurate name. Phase belongs in the active change/PR state, not in the branch namespace.

If a future runtime or repository policy gives design work a genuinely distinct operational boundary, a dedicated namespace can be introduced then.

## Why Design Is Not Merged Early

For an existing project, merging a future-state design before the implementation exists can make canonical repository documentation disagree with current code. Agents may then correctly read the repository but infer behavior that has not been implemented yet.

Therefore the default is:

> accepted future-state design stays on the active feature branch until the implementation that realizes it is ready to merge.

This also resolves retention cleanly:

- `docs/changes/` continues to contain active work only;
- accepted `DESIGN.md` remains active because implementation is still active;
- before final merge, durable design is folded into architecture/specs/ADRs/code/tests as appropriate;
- `CHANGE.md` and `DESIGN.md` are then removed.

For a brand-new project with no existing implementation, the design is still reviewed first, but the same branch/PR continues into implementation rather than merging design alone into stable/integration truth.

## Reviewer Ownership

The implementer may never self-certify that review is complete.

```text
implementer pushes latest head
        ↓
reviewer evaluates latest head
        ↓
clean verdict
        ↓
ready-for-human-merge
```

If the head changes after a clean review, the verdict is stale and the latest head must be reviewed again.

Reviewer transport may vary, but lifecycle responsibility does not.

## Runtime Automation

Runtime-specific automation can accelerate the loop:

- an implementation runtime may watch its PR and react to comments/CI;
- Codex or another reviewer may be triggered automatically or by PR comment;
- future runtimes may provide equivalent capabilities.

Core protocol specifies only the contract:

1. implementer consumes actionable feedback;
2. implementer pushes fixes;
3. reviewer independently evaluates the new head;
4. repeat until clean;
5. human merges unless configured authority explicitly says otherwise.

Vendor commands, hooks, polling, or hosted sessions belong in runtime/operator guidance rather than core semantics.

## Project Status During the Lifecycle

Feature-branch `CURRENT.md` may identify the active change and its durable phase, for example:

- design is active and implementation has not begun;
- implementation is active against an accepted design;
- a durable blocker requires human attention.

It should not be used to record transient PR coordination such as “waiting for review”, “merge this PR next”, or “release after approval”.

Before final merge, status is rewritten to merge-safe integrated truth according to the existing v2 rule.

## Proposed Repository Changes After Design Acceptance

If this proposal is accepted, the implementation phase should update:

- `WORKFLOW.md`
  - add the design → implementation phase transition;
  - require initial design for brand-new projects;
  - describe when consequential existing-project changes need design review;
  - define implementation change identity;
  - state that implementation pivots stay in the same PR when identity is unchanged;
  - make reviewer ownership of the latest-head verdict explicit.

- `spec/templates/WORKFLOW.md`
  - mirror the same protocol semantics.

- `docs/WORK_TRACKING.md` and template
  - describe design materialization and the acceptance transition;
  - retain `DESIGN.md` as active state until implementation completes;
  - distinguish implementation pivots from identity-changing feedback.

- `HUMAN_SETUP.md`
  - explain the new-project flow: chat → design phase in feature PR → human acceptance → implementation in the same PR;
  - note that runtime-specific autofix/watch features are optional accelerators.

- `spec/SPEC.md`
  - summarize the lifecycle distinction if useful for protocol consumers.

No protocol version bump is proposed unless implementation review concludes this clarification is breaking.

## Resolved Human Review Questions

1. **Brand-new project:** design is mandatory before implementation.
2. **Branch naming:** keep `feature/<change-id>`; a separate `design/<id>` namespace adds no useful boundary today.
3. **Design acceptance:** acceptance transitions the same PR into implementation; design is not merged separately.
4. **Reaching `main`:** future-state design does not reach `develop` or `main` ahead of the implementation that realizes it. This avoids canonical docs disagreeing with current code.
