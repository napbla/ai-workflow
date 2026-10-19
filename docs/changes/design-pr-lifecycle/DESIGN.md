# Proposal: Design PR Lifecycle

## Problem

The v2 rollout exposed two different kinds of PRs that should not share the same mutation rules:

1. **Design PRs** exist to converge on what should be built.
2. **Implementation PRs** exist to realize an already accepted change identity.

Treating both the same creates two opposite failures:

- closing a Design PR whenever human feedback changes architecture or scope makes design review unnecessarily expensive;
- allowing an Implementation PR to continuously change its intent makes the PR impossible to reason about and review coherently.

The workflow should model these phases explicitly.

## Proposed Lifecycle

### New project / consequential design

```text
Human ↔ Architect exploration
        ↓
Architect materializes design proposal
        ↓
Design PR → develop
        ↓
Human comments / questions
        ↓
Architect explains + revises design
        ↓
Design accepted
        ↓
merge Design PR
        ↓
create implementation change
        ↓
Implementation PR
```

A Design PR is a proposal surface. Its purpose is convergence, so the following may evolve in the same PR:

- product intent;
- acceptance criteria;
- architecture;
- scope;
- contracts;
- milestones;
- trade-offs.

The architect should answer comments directly on the PR and update repository design artifacts when the proposal changes.

### Implementation

Once a design or change intent is accepted:

```text
accepted intent + acceptance criteria
        ↓
implementation change
        ↓
implement → test → push
        ↓
review latest head
        ↓
findings? → fix → review again
        ↓
ready-for-human-merge
```

The identity of an implementation change is:

> accepted intent + acceptance criteria

It is **not** the original implementation plan.

Therefore, implementation details may evolve freely within the same PR when they still satisfy the same accepted change identity.

Examples that stay in the same PR:

- library A is unavailable, use library B;
- webhook is unavailable, use polling;
- an API permission prevents one approach, use another;
- internal module boundaries are adjusted without changing the accepted external behavior;
- reviewer asks for a safer or simpler implementation of the same requirement.

If such a pivot creates a durable architectural or operational decision, record that consequence in the appropriate current-truth surface. Otherwise Git/PR history is enough.

## When to Restart an Implementation Change

After implementation has started, close the current PR/change and start a new one when human feedback materially changes the accepted:

- intent;
- acceptance criteria;
- architecture boundary that defines the work;
- scope.

A replacement change may carry forward still-valid artifacts such as:

- end-to-end/regression tests;
- verified findings;
- reusable implementation fragments;
- research evidence.

But it must restate the new intent and acceptance criteria explicitly.

This keeps the invariant:

> One implementation PR represents one coherent change identity.

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

If the head changes after a clean review, the review verdict is stale and the latest head must be reviewed again.

Reviewer transport may vary, but the lifecycle responsibility does not.

## Runtime Automation

Runtime-specific automation can accelerate the loop:

- Claude Code may watch a PR and react to comments/CI;
- Codex may be triggered to review a PR;
- other runtimes may provide equivalent features later.

Core protocol should only specify the contract:

1. implementer consumes actionable feedback;
2. implementer pushes fixes;
3. reviewer independently evaluates the new head;
4. repeat until clean;
5. human merges unless authority explicitly says otherwise.

Vendor commands, hooks, polling, or hosted sessions belong in runtime/operator guidance rather than core semantics.

## Proposed Repository Changes After Design Acceptance

If this design is accepted, the implementation change should update:

- `WORKFLOW.md`
  - add Design PR phase;
  - distinguish Design PR mutation rules from Implementation PR rules;
  - define implementation change identity;
  - state that implementation pivots do not require a new PR when intent/acceptance criteria are unchanged;
  - make reviewer ownership of latest-head verdict explicit.

- `spec/templates/WORKFLOW.md`
  - mirror the same protocol semantics.

- `docs/WORK_TRACKING.md` and template
  - describe when design state should be materialized;
  - distinguish design evolution from implementation scope changes.

- `HUMAN_SETUP.md`
  - explain the new-project flow: chat → Design PR → accepted design → implementation change;
  - note that runtime-specific autofix/watch features are optional accelerators.

- possibly `spec/SPEC.md`
  - record the semantic distinction if needed for protocol documentation.

No protocol version bump is proposed unless implementation review concludes this is breaking rather than a v2 clarification.

## Open Questions for Human Review

1. Should every brand-new project require a Design PR, or only when there is consequential design to review?
2. Should the default branch name for design proposals remain `feature/<change-id>`, or introduce `design/<id>`?
3. Should an accepted Design PR always be merged before implementation begins, or may implementation branch from the design branch before merge for speed?
4. Should Design PRs ever reach `main` directly, or always flow through `develop` like all other integration work?
