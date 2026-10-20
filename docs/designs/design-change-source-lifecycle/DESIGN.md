# Design → Change → Source Lifecycle

Status: Realized
Owner: architect

## Realization Map

Changes:
- `implement-design-lifecycle-v3` — Realized
- `ci-required-checks` — Realized

Areas:
- `WORKFLOW.md` — Realized
- `docs/WORK_TRACKING.md` — Realized
- `docs/designs/INDEX.md` — Realized
- `spec/**` — Realized
- `init/**` — Realized
- `HUMAN_SETUP.md` — Realized
- `.agents/**` — Realized
- `.ai-workflow.yml` — Realized
- `.github/workflows/ci.yml` — Realized

Tests:
- `init/tests/test_init.py` — Realized

Current-truth docs:
- `spec/SPEC.md` — Realized
- `README.md` — Realized
- `HUMAN_SETUP.md` — Realized
- `check/README.md` — Realized

This Design is the current conceptual map for protocol-v3 Design/Change/source semantics. The implementation Change was derived from accepted Design revision `305121fb9b24bb31c753044a8262b0380882bc71`.

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
Status: Proposed | Accepted | Implementing | Realized
Owner: architect
```

Once implementation starts, the Design also carries a **Realization Map**. Realization is tracked per mapped area, not only by the Design's aggregate status.

Example:

```md
## Realization Map

Changes:
- provider-contract — merged
- apple-provider — merged
- google-play-provider — in progress

Areas:
- providers/contracts/** — Realized
- providers/apple/** — Realized
- providers/google-play/** — Target

Tests:
- tests/providers/contracts/** — Realized
- tests/providers/apple/** — Realized
- tests/providers/google-play/** — Target

Current-truth docs:
- docs/architecture/data-provider.md — Realized
```

Per-area states are:

- `Target` — accepted target scope, not evidence that source behavior exists yet;
- `Realized` — the mapped source/test/doc currently implements that part of the Design.

This map exists so a new agent can answer "which design explains this code?" without reconstructing the design from the whole codebase.

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

Acceptance is bound to the **exact final Design PR head**. The architect may stage `Status: Accepted` during the final fold, but the human's approval/merge of that exact head is the effective confirmation. Any later push that changes Design semantics makes the prior acceptance stale and requires human reconfirmation before merge. Non-semantic repository-host metadata does not alter the Design head and therefore does not affect acceptance.

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

A Change derived from a Design must reference both the Design path and the accepted Design revision it implements. Use the merged Git commit that contains the accepted Design as the revision binding.

Example:

```md
Design: docs/designs/data-provider/DESIGN.md
Design-Revision: <accepted-design-commit-sha>

## Goal
Implement the provider contract defined by that accepted design revision.

## Acceptance Criteria
...
```

If an accepted Design is later revised, the architect must revalidate **every incomplete Change** mapped to that Design. A Change may continue only when its identity and implementation remain valid against the new accepted revision; otherwise close/restart it or revise it according to the normal identity rules.

Every continuing Change must durably rebind its `Design-Revision` to the newly accepted Design revision before implementation resumes. The revalidation is therefore visible to replacement implementers and reviewers and cannot exist only in PR discussion.

This prevents sibling Changes from silently implementing different Design revisions.

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

The Design maintains a Realization Map containing:

- the Changes derived from it and their state;
- the source areas currently realizing it;
- the tests protecting those areas;
- the current architecture/spec/module docs that describe the implemented behavior.

Every source change that moves, replaces, removes, or materially changes a source area referenced by a Design must update all affected Design Realization Maps and any `docs/designs/INDEX.md` entries before final review — even when that source change is a small fix, a direct Change, or a Change derived from another Design.

The map is current traceability, not a changelog. It should describe what implements the Design now, not every path that ever did.

## Design Realization and Retention

When all required Changes for a Design are complete:

1. fold implemented durable truth into code/tests/module docs/specs/architecture/ADRs as appropriate;
2. update the Design's Realization Map to the source areas/tests/current docs that now realize it;
3. set `Status: Realized`;
4. remove the completed active `CHANGE.md`;
5. keep the Design while it remains a useful current conceptual map of the implemented system.

A realized Design is **not an archive**. It remains because it answers a current question: "what design does this code implement?" and gives agents an entry point into the relevant source instead of forcing repo-wide rediscovery.

When a later Design supersedes only part of a realized Design, the old Design continues to map the currently implemented source until replacement source is actually realized.

The trim/split is atomic with realization of the replacement source:

1. implement the replacement source;
2. mark the corresponding replacement Design area `Realized` (the Design may still remain `Implementing` overall);
3. update or split the old Design so it no longer marks that area `Realized`;
4. update `docs/designs/INDEX.md` so reverse lookup switches from old Design to replacement Design for that area;
5. include all of those mutations in the same final reviewed HEAD.

An `Accepted` or `Implementing` replacement Design does not by itself supersede the current realized mapping.

Remove a Design when it is fully superseded or no longer needed to understand the current system. Before removal, ensure its still-relevant knowledge has moved into the replacement Design/current architecture/spec/module docs. Git preserves the historical artifact.

All final fold, map updates, status transitions, and removals happen **before the final reviewer/CI verdict**.

```text
implement source changes
        ↓
fold durable current truth
        ↓
update Design Realization Map
        ↓
mark Design Realized if complete
        ↓
remove completed CHANGE.md
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

The repository distinguishes implementation evidence from conceptual/target design state.

### Current implemented truth

- source code;
- tests;
- module docs;
- `docs/specs/`;
- `docs/architecture/`.

These answer:

> What is implemented now?

### Design registry

- `docs/designs/`.

A Design's aggregate status describes lifecycle progress, not realization of every mapped area:

- `Proposed` — under design review;
- `Accepted` — target accepted, implementation not yet started;
- `Implementing` — one or more required Changes remain incomplete; some mapped areas may already be `Realized`;
- `Realized` — all required mapped areas are realized.

Only **per-area `Realized` entries** in the Realization Map are evidence that a Design currently explains a source/test/doc area.

### Active transformation state

- `docs/changes/`.

This answers:

> What coherent transformation is being implemented now?

Agents should start from the Design whose Realization Map marks the relevant source area `Realized`, regardless of whether the Design's aggregate status is `Implementing` or `Realized`. They then inspect only the mapped source/tests/current docs needed for the task, rather than rediscovering the architecture from the whole codebase.

## Design Traceability Index

For projects with multiple Designs, maintain:

```text
docs/designs/INDEX.md
```

as a lightweight current lookup table of **realized mappings only**, for example:

```md
| Design | Design status | Realized source areas |
| --- | --- | --- |
| data-provider | Implementing | providers/contracts/**, providers/apple/** |
| analytics-engine | Realized | analytics/** |
```

Target-only areas do not appear in reverse lookup until they are realized.

The index is not a second source of truth and not a history log. It is a navigation projection of current per-area `Realized` entries in Design files. If an entry disagrees with a Design's Realization Map, the Design file wins and the index must be corrected.

This gives reverse navigation:

```text
source path
   ↓
docs/designs/INDEX.md
   ↓
Design
   ↓
Realization Map
   ↓
relevant current docs / tests / source
```

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
