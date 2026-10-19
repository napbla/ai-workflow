# Design → Change → Source Lifecycle

Status: Proposed
Owner: architect

## Goal

Define three separate primitives in ai-workflow:

1. **Design** — describes an accepted target state: what the system should become.
2. **Change** — describes one coherent transformation from current truth toward an accepted design.
3. **Source change** — the actual code/tests/docs modifications that implement a Change.

The protocol must not collapse these into one artifact or lifecycle.

## Core Model

```text
current system
      ↓
DESIGN
what should the system become?
      ↓
one or more CHANGES
what coherent transformations get us there?
      ↓
SOURCE CHANGES
code + tests + current-truth docs
      ↓
implemented system
```

A Design may map to one Change, but it may also decompose into many Changes.

Example:

```text
Design: Data Provider Architecture
        │
        ├── Change: provider contract
        ├── Change: Apple provider
        ├── Change: Google Play provider
        └── Change: provider analytics integration
```

This is why Design and Change must have separate identity and storage semantics.

## Design Semantics

A Design answers:

> What target state do we want, and why?

A Design may include:

- product intent;
- target behavior;
- architecture;
- contracts;
- constraints;
- trade-offs;
- acceptance conditions for the target state;
- decomposition guidance.

A Design is not evidence that the target state is already implemented.

### Canonical storage

Accepted target designs live under:

```text
docs/designs/<design-id>/DESIGN.md
```

This directory has explicit semantics:

> `docs/designs/` contains accepted or proposed target-state designs that may be partially or not yet implemented. It is planning truth, not current implemented truth.

Agents must not interpret `docs/designs/` as evidence of current source behavior. Current implemented truth continues to live in code, tests, module docs, `docs/specs/`, and `docs/architecture/`.

A Design file should carry at least:

```text
Status: Proposed | Accepted | Implementing
Owner: architect
```

and, once implementation starts, an implementation map that identifies the Changes realizing it.

### Design lifecycle

```text
Human ↔ Architect exploration
        ↓
design/<design-id>
        ↓
docs/designs/<design-id>/DESIGN.md
        ↓
Design PR → develop
        ↓
Human comments / Architect explains + revises
        ↓
Human accepts target design
        ↓
Status: Accepted
        ↓
merge Design PR
        ↓
Architect decomposes accepted design into Change(s)
```

A Design PR is intentionally mutable. During review, intent, architecture, scope, constraints, and target acceptance conditions may evolve freely.

Human acceptance is the authority boundary for the target design.

### Brand-new projects

Every brand-new project must have an initial Design before implementation begins. The Design is the guide from which the first Change(s) are derived.

### Existing projects

Consequential new features or redesigns should use a Design when the human should review target architecture, contracts, product behavior, or trade-offs before implementation.

Small/local fixes do not need a Design when the desired target state is already obvious.

## Why `design/<design-id>` Now Has a Purpose

When Design was treated merely as a phase inside a feature Change, a separate branch namespace added no value.

Under this model, Design is a distinct primitive:

- it may exist before any source change;
- it may create multiple Changes;
- it has a different mutation rule from implementation;
- it has a different artifact root;
- it is human-accepted before implementation decomposition.

Therefore the default branch names become:

```text
design/<design-id>     # target-state proposal
feature/<change-id>    # one implementation transformation
```

This is a semantic distinction, not cosmetic naming.

## Change Semantics

A Change answers:

> What coherent transformation of current truth are we implementing now?

A Change is created only after there is enough accepted intent to implement. It may derive from:

- an accepted Design; or
- a small/direct human requirement that does not need a separate Design.

Normal storage remains:

```text
docs/changes/<change-id>/CHANGE.md
```

on:

```text
feature/<change-id>
```

A Change derived from a Design must reference it explicitly.

Example:

```md
Design: docs/designs/data-provider/DESIGN.md

## Goal
Implement the provider contract defined by the accepted design.

## Acceptance Criteria
...
```

## Change Identity

Implementation Change identity is:

> accepted intent + acceptance criteria + explicit non-negotiable constraints

It is not the initial implementation plan.

Therefore implementation strategy may change freely inside the same Change when that identity remains unchanged.

Examples that stay in the same Change:

- library A → library B because A is unavailable;
- webhook → polling because the runtime cannot receive webhooks;
- one API → another API because of permission constraints;
- internal module boundaries change while accepted behavior remains the same;
- reviewer requests a safer/simpler implementation of the same requirement.

Architecture or internal scope changing is not, by itself, a reason to restart.

## When a Change Must Restart

After implementation starts, close the current Change/PR and create a new one when feedback materially changes:

- accepted intent;
- acceptance criteria;
- an explicit non-negotiable constraint such that the job is now different.

If the new requirement also changes the accepted target Design, revise the Design first through a Design PR, then derive the replacement Change from the updated accepted Design.

A replacement Change may reuse still-valid tests, findings, research, and implementation fragments.

Invariant:

> One implementation PR represents one coherent Change identity.

## Source Change Semantics

Source changes are the concrete modifications made to satisfy a Change:

- code;
- tests;
- migrations;
- configuration;
- module docs;
- current specs/architecture;
- other executable/current-truth artifacts.

Source changes do not have a separate planning identity. They belong to the Change that justifies them.

```text
Design
   ↓
Change
   ↓
source diff
```

This makes traceability one-way and explicit.

## One Design → Many Changes

After a Design is accepted, the architect may decompose it into multiple Changes.

The Design should maintain an implementation map while it is active, for example:

```md
## Implementation Map

- provider-contract — planned
- apple-provider — planned
- google-play-provider — planned
```

Each Change may update that map as durable coordination state when it merges.

The Design remains active planning truth until the target design has been sufficiently realized.

## Design Completion

When all required Changes for a Design are complete:

1. fold implemented durable truth into code/tests/module docs/specs/architecture/ADRs as appropriate;
2. verify that current truth no longer depends on the Design artifact to understand the implemented system;
3. remove `docs/designs/<design-id>/`;
4. let Git preserve the historical Design.

Do not maintain a design archive by default.

If the final implementation Change completes the Design, that Change may perform the fold and remove the Design artifact.

Crucially, all final fold/removal mutations happen **before the final reviewer/CI verdict**.

```text
implement source changes
        ↓
fold durable current truth
        ↓
remove completed CHANGE.md
        ↓
remove completed DESIGN.md if this is the final Change
        ↓
push final HEAD
        ↓
reviewer + CI evaluate final HEAD
        ↓
clean
        ↓
ready-for-human-merge
```

Any HEAD change after a clean review makes that verdict stale and requires re-review.

## Design vs Current Truth

The repository now contains two intentionally different truths:

### Current implemented truth

- source code;
- tests;
- module docs;
- `docs/specs/`;
- `docs/architecture/`.

These answer:

> What is implemented now?

### Accepted target/planning truth

- `docs/designs/`;
- active `docs/changes/`.

These answer:

> What have we accepted to build, and what transformation is active?

This distinction must be explicit in agent bootstrap and operator guidance so future-state design is never confused with current behavior.

## Pull Request Semantics

### Design PR

Purpose: converge on target state.

- branch: `design/<design-id>`;
- primary artifact: `docs/designs/<design-id>/DESIGN.md`;
- human-led review;
- intent/architecture/scope may evolve;
- ends when human accepts and the accepted Design is merged into `develop`.

### Change PR

Purpose: implement one coherent transformation.

- branch: `feature/<change-id>`;
- primary coordination artifact: `docs/changes/<change-id>/CHANGE.md`;
- references accepted Design when applicable;
- implementation plan may evolve while Change identity remains stable;
- implementer + independent reviewer/CI iterate on the latest HEAD;
- ends at `ready-for-human-merge`, then human merges.

## Reviewer Ownership

The implementer may never self-certify that review is complete.

```text
implementer pushes final HEAD
        ↓
reviewer evaluates final HEAD
        ↓
clean verdict
        ↓
ready-for-human-merge
```

Any push after the clean verdict invalidates it.

## Runtime Automation

Vendor/runtime-specific capabilities may automate the loop:

- PR monitoring;
- reacting to review feedback;
- triggering independent review;
- consuming CI failures.

Core protocol defines only the lifecycle contract. Claude/Codex-specific commands, hooks, polling, or hosted sessions remain operator/runtime guidance rather than protocol requirements.

## Proposed Protocol Changes After Design Acceptance

Implementation of this Design should update:

- `WORKFLOW.md`
  - introduce Design → Change → Source semantics;
  - define Design PR and Change PR separately;
  - define change identity and restart rules;
  - enforce final-head review after all cleanup/folding.

- `spec/templates/WORKFLOW.md`
  - mirror those semantics.

- `docs/WORK_TRACKING.md` and template
  - add `docs/designs/` lifecycle;
  - distinguish Design completion from Change completion;
  - describe 1→N implementation maps.

- `AGENTS.md` / role guidance if needed
  - architect decomposes accepted Designs into Changes;
  - implementer works from a Change, not directly from an unaccepted Design.

- `HUMAN_SETUP.md`
  - brand-new project flow starts with Design PR;
  - human accepts design before implementation decomposition.

- `spec/SPEC.md`
  - add `docs/designs/` to project state and define it as target/planning truth.

- initializer/templates/tests
  - generate the required Design directory/guidance if protocol review concludes it is part of the repository contract.

Because this adds a new canonical artifact class and branch lifecycle, implementation review should explicitly decide whether it is a protocol-v2 clarification or requires the next protocol version.

## Decisions Captured From Human Review

1. A brand-new project must have a Design before implementation.
2. Design and Change are separate primitives.
3. The relationship is `Design → Change → Source change`.
4. A Design may produce multiple Changes.
5. Future-state Design must not be mistaken for current implemented truth.
6. With Design now a separate primitive, `design/<design-id>` has a real semantic purpose.
