# ai-workflow — AI-Native Project Workflow

Protocol: `ai-workflow v3`

This repository is the transferable shared state for one human operator working with multiple AI agents.

## North Star

The project should remain operable by:

- one human operator coordinating multiple AI agents
- a replacement human who has not seen prior conversations
- progressively more autonomous agents as capabilities improve
- bounded projects with zero human intervention when authority and reliability permit it

Human involvement is driven by **risk, uncertainty, and authority**, not ceremony.

## Source of Truth

The Git repository is the canonical transferable project state.

Canonical state is branch-sensitive:

- `main` — stable/releasable current truth
- `develop` — reviewed integration truth
- `design/<design-id>` — a proposed target Design under human review
- `feature/<change-id>` — one active implementation Change

Conversation history, PR comments, CI messages, and external tools are coordination surfaces. They are not durable project truth.

## State Model

The repository intentionally separates three kinds of state.

### Current implemented truth

- source code
- tests
- module documentation
- `docs/specs/`
- `docs/architecture/`

These answer:

> What is implemented now?

### Design registry

- `docs/designs/<design-id>/DESIGN.md`
- `docs/designs/INDEX.md`

A Design describes target/conceptual structure. Its aggregate status is:

- `Proposed` — under design review
- `Accepted` — target accepted, implementation not started
- `Implementing` — one or more required Changes remain incomplete
- `Realized` — all required mapped areas are realized

Realization is tracked **per mapped area**:

- `Target` — accepted target scope, not evidence that behavior exists
- `Realized` — mapped source/test/doc currently implements that part of the Design

Only per-area `Realized` entries are evidence that a Design currently explains an area.

`docs/designs/INDEX.md` is a disposable navigation projection of current realized mappings. It is not a second source of truth. If it disagrees with a Design's Realization Map, the Design file wins and the index must be fixed.

### Active transformation state

- `docs/changes/<change-id>/CHANGE.md`

A Change describes one coherent transformation of current truth. Completed Change artifacts are removed after folding.

### Other durable state

- `docs/adr/` — rare cross-cutting rationale that must live independently of one Design
- `docs/status/CURRENT.md` — merge-safe operator-facing current snapshot
- Git history — historical record

Do not maintain archive folders for completed Changes or superseded Designs merely to preserve history. Git is the history.

## Core Lifecycle: Design → Change → Source

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

Design, Change, and source diff are separate primitives.

### Design

A Design answers:

> What target state do we want, and why?

Every brand-new project starts with a human-reviewable Design before implementation.

For an existing project, use a Design when a consequential feature/redesign needs review of product intent, architecture, contracts, constraints, or trade-offs. Small/local work may go directly to a Change when the target state is already obvious.

A Design PR:

- uses `design/<design-id>`
- targets `develop`
- owns `docs/designs/<design-id>/DESIGN.md`
- is intentionally mutable while `Proposed`
- may evolve intent, architecture, scope, constraints, and target acceptance conditions
- is accepted only by human confirmation of the exact final Design PR head

The architect may stage `Status: Accepted` during final fold, but human approval/merge of that exact head is the effective acceptance boundary. Any later semantic push makes acceptance stale and requires human reconfirmation.

One accepted Design may produce one or many Changes.

### Change

A Change answers:

> What coherent transformation of current truth are we implementing now?

A non-trivial Change:

- uses `feature/<change-id>`
- targets `develop`
- owns `docs/changes/<change-id>/CHANGE.md`
- has one coherent identity: **accepted intent + acceptance criteria + explicit non-negotiable constraints**

A Change derived from a Design must bind to both:

```text
Design: docs/designs/<design-id>/DESIGN.md
Design-Revision: <accepted-design-commit-sha>
```

Use the merged Git commit containing the accepted Design as the revision binding.

Implementation strategy is not Change identity. Library choices, APIs, internal boundaries, polling vs webhook, and similar tactics may change inside the same PR while the accepted identity remains unchanged.

If an accepted Design is revised, the architect must revalidate every incomplete Change mapped to it. Any continuing Change must durably rebind its `Design-Revision` to the newly accepted revision before work resumes. Restart a Change when its accepted identity is materially different.

A small/local low-risk fix may omit `CHANGE.md` when no persistent coordination context is needed, but it must still preserve all affected current truth and Design mappings.

### Source change

Source changes are concrete modifications justified by a Change:

- code
- tests
- migrations
- configuration
- module docs
- current specs/architecture
- Design realization mappings/index when affected

Source changes do not have a separate planning identity.

## Roles and Runtimes

Agent identities are roles such as `architect`, `implementer`, and `reviewer`, described in `.agents/<role-id>.md`.

The runtime/model/vendor fulfilling a role is invocation state and is not recorded in the repository. Role responsibility and runtime capability are separate. When a runtime cannot perform a required action, hand that action to a capable human/agent while preserving lifecycle ownership.

## Agent Bootstrap

Agent identity must be explicit in the execution environment or invocation prompt. Do not guess it.

Before working, every agent must read:

1. `WORKFLOW.md`
2. `AGENTS.md`
3. `.agents/<its-role-id>.md`
4. `docs/WORK_TRACKING.md`
5. `docs/status/CURRENT.md`
6. relevant current specs/architecture/code/tests
7. relevant Design(s), using `docs/designs/INDEX.md` for reverse lookup when useful
8. the relevant active Change, if one exists

For a Design-derived Change, verify its `Design-Revision` before implementation/review.

Do not rely on previous conversation history when repository artifacts exist.

## Context Refresh

Conversation context may be stale.

A request such as `sync repo` means:

1. refresh relevant repository state using available repository access
2. re-read workflow/role/tracking rules when relevant
3. inspect current status, relevant Designs, active Changes, and affected current truth
4. continue from repository state, not remembered conversation state

If repository access is unavailable, say so rather than silently using stale context.

## Branch Model

### `main` — stable

- stable/releasable current truth
- updated through reviewed PRs from `develop`
- no active Change coordination artifacts are introduced directly

### `develop` — integration

- reviewed integration truth
- Design and feature branches start from latest `develop`
- Design and Change PRs merge back through review

### `design/<design-id>`

- carries one target Design proposal
- may evolve freely while under human design review
- does not imply the proposed behavior exists
- ends when the exact accepted Design head is merged into `develop`

### `feature/<change-id>`

- carries one implementation Change
- includes implementation/tests/folded current-truth updates
- if Design-derived, binds to an accepted Design revision

### Protected Branch Policy

`main` and `develop` are protected integration branches. Agents may push their own Design/feature branches and update their PRs, but must not:

- push directly to `main` or `develop`
- target either branch with a push refspec
- set either as a push/upstream target
- bypass protection via force/mirror/all pushes

Repository-host branch protection/rulesets are authoritative. Both branches must require pull requests and block force pushes/deletion for agent credentials. Agents verify protection; local hooks are convenience only.

Missing or unverifiable protection is a human setup blocker.

## Design Realization and Traceability

Each Design that has implementation underway maintains a **Realization Map** containing:

- derived Changes and their durable state
- source areas
- tests
- current-truth docs

Mapped source/test/doc areas are labeled `Target` or `Realized`.

Every source change that moves, replaces, removes, or materially changes a mapped area must update **all affected Design Realization Maps** and `docs/designs/INDEX.md` before final review, regardless of whether the source change came from that Design, another Design, a direct Change, or a small fix.

### Partial supersession

A replacement Design does not supersede current realized mappings merely by becoming `Accepted` or `Implementing`.

When replacement source for one area becomes real, update atomically in the same final reviewed head:

1. implement replacement source
2. mark replacement Design area `Realized`
3. remove that realized area from/update/split the old Design
4. switch the index mapping to the replacement Design

A Design may remain `Implementing` overall while some areas are already `Realized`.

### Design retention

A fully implemented Design becomes `Status: Realized` and remains while it is useful as a current conceptual map.

Remove it only when fully superseded or no longer needed to understand the current system. Before removal, move still-relevant knowledge into replacement Design/current architecture/spec/module docs. Do not create an archive copy.

## Work Tracking and Folding

Use the lightest artifact that preserves transferable state.

### Exploration

Exploration may stay in conversation until it creates accepted target intent, committed work, durable constraints, or cross-session follow-up.

### Design fold

Before a Design PR is ready for final human acceptance:

1. fold accepted review outcomes into the appropriate Design sections
2. remove review-provenance/transient consolidation sections
3. create/update an ADR only for cross-cutting rationale that must live independently
4. stage final status/metadata
5. push final Design head
6. obtain human acceptance of that exact head

### Change fold

Before an implementation Change is ready for final review:

1. satisfy acceptance criteria
2. fold durable implemented truth into code/tests/module docs/specs/architecture
3. update every affected Design Realization Map and index
4. mark Design areas/status appropriately
5. update an ADR only when cross-cutting rationale must survive independently
6. make `docs/status/CURRENT.md` merge-safe
7. remove completed `docs/changes/<change-id>/`
8. push the final head
9. run independent review/CI on that final head

Any push after a clean review makes the verdict stale and requires re-review.

## Durable Decisions and ADRs

Default rationale belongs in the relevant Design.

Use an ADR only when a decision is cross-cutting, affects multiple Designs, or must live independently longer than the Design containing it.

ADR is not a changelog. Git is the changelog.

## Implementation Rules

- Make the smallest source change that satisfies the Change identity.
- Preserve current contracts unless the accepted Design/Change modifies them.
- Avoid unrelated refactoring.
- Follow current repository patterns.
- Add/update tests when behavior changes.
- Update current-state documentation when implementation changes behavior/architecture.
- Update every affected Design mapping/index when mapped areas change.
- Surface uncertainty instead of inventing requirements.
- Do not create process artifacts solely to compensate for temporary model limitations.

## Pull Request Ownership

### Design PR

The architect owns Design convergence until accepted/merged:

- answers design comments
- revises the Design
- folds accepted decisions
- ensures final head represents exactly what the human accepts

### Change PR

The implementer owns the Change PR until handoff/merge:

- keeps the PR scoped to one Change identity
- implements/tests/pushes
- consumes actionable reviewer/CI/human feedback
- updates current truth and Design mappings
- performs final fold before requesting final review

PR ownership is lifecycle responsibility, not a guarantee of repository-host permissions.

## Autonomous Change Execution

Once a Change identity is accepted and materialized:

```text
implementer owns Change
        ↓
implement → test → push
        ↓
reviewer / CI
        ↓
findings? ── yes → fix → test → push ─┐
        │ no                            │
        ↓                               │
fold all durable truth + mappings       │
        ↓                               │
remove CHANGE.md                        │
        ↓                               │
push final HEAD                         │
        ↓                               │
reviewer / CI on final HEAD ←───────────┘
        ↓
ready-for-human-merge
```

The implementer never self-certifies clean review. The reviewer owns the latest-head verdict.

Human feedback that preserves Change identity stays in the same PR. Feedback that changes the accepted identity requires a replacement Change. If it also changes accepted target Design, revise/accept the Design first, then derive/revalidate Changes.

Runtime-specific PR watchers/autofix/review triggers are optional accelerators, not protocol semantics.

## Review Rules

### Design review

Review whether the target state is coherent, understandable, decomposable, and acceptable. Intent/architecture/scope may evolve until exact-head human acceptance.

### Change review

Review the final head against:

1. Change goal, acceptance criteria, and constraints
2. bound accepted Design revision, when applicable
3. current implemented truth and compatibility
4. relevant cross-cutting ADRs
5. correctness/security
6. tests
7. Design Realization Map/index correctness
8. unnecessary complexity

If the head changes after a clean verdict, re-review.

## Risk and Authority

Escalate when:

- a decision exceeds role authority
- risk/uncertainty is material
- requirements conflict
- a consequential trade-off needs higher authority
- accepted Design identity must change

Do not add fixed approval gates beyond actual authority boundaries.

## Project Status

`docs/status/CURRENT.md` is the operator dashboard, not a historical report.

It should answer:

- What is the project doing now?
- Which Designs matter and what state are they in?
- What active Changes exist?
- What is blocked/risky?
- What requires human attention?
- What is next?

### Merge-safe status

Content merged into a protected branch must already describe durable truth after the merge and remain valid after the next `develop` → `main` merge.

Do not put transient coordination in `CURRENT.md`:

- pending PR review
- PR readiness
- pending merge/release
- branch ahead/behind
- "main is still on the previous version"

Put those in the PR or active Design/Change.

## Human Handoff Requirement

A replacement human/agent should be able to reconstruct the project by reading the repository alone.

If handoff requires old chats, project state is incomplete.

## Conflict Priority

When instructions conflict, use:

`Human explicit decision → accepted Design revision for target behavior → current specs/architecture/code for implemented behavior → cross-cutting ADR → active Change → WORKFLOW.md → agent judgment`

A Design describes target intent; current implementation evidence describes what exists now. Do not confuse them.

## Core Principle

Keep the repository optimized for answering three questions quickly:

1. **What exists now?**
2. **What have we accepted to become?**
3. **What coherent transformation is active now?**

Let Git preserve what happened before.
