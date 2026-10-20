# AI Workflow Protocol

This directory defines the canonical repository protocol used by the `ai-workflow` ecosystem.

## Ownership

`spec/` owns:

- protocol version
- generated repository structure
- workflow semantics
- default roles
- branch model/protected branch policy
- generated templates

Tools consume this protocol and must not redefine it independently.

## Project Marker

A compliant v3 project declares:

```yaml
# .ai-workflow.yml
protocol: 3
```

## Required Project State

```text
.ai-workflow.yml
WORKFLOW.md
AGENTS.md
.agents/

docs/
  WORK_TRACKING.md
  architecture/
  specs/
  adr/
  designs/
    INDEX.md
  changes/
  status/CURRENT.md
```

Semantics:

- `specs/` — current product/system behavior
- `architecture/` — current technical truth/contracts
- `designs/<design-id>/DESIGN.md` — target/conceptual Design state
- `designs/INDEX.md` — navigation projection of realized Design mappings
- `changes/` — active implementation transformation state only
- `adr/` — rare durable cross-cutting rationale
- `status/CURRENT.md` — merge-safe operator-facing snapshot
- code/tests/module docs — executable/current implementation truth
- Git — history

## Core Model

v3 separates:

```text
Design → one or more Changes → source changes
```

### Design

A Design answers what the system should become.

- branch: `design/<design-id>`
- artifact: `docs/designs/<design-id>/DESIGN.md`
- brand-new projects require an initial Design
- consequential existing-project redesigns use a Design when target state needs human review
- exact final Design PR head is the human acceptance boundary

Aggregate Design status:

`Proposed | Accepted | Implementing | Realized`

Per mapped area realization:

`Target | Realized`

Only per-area `Realized` entries indicate that current source/test/doc behavior is explained by that Design.

### Change

A Change answers what coherent transformation is being implemented now.

- branch: `feature/<change-id>`
- artifact: `docs/changes/<change-id>/CHANGE.md`
- identity: accepted intent + acceptance criteria + explicit non-negotiable constraints
- implementation strategy may pivot without creating a new Change while identity remains stable

A Design-derived Change records:

```text
Design: docs/designs/<design-id>/DESIGN.md
Design-Revision: <accepted-design-commit-sha>
```

If the Design is revised, all incomplete mapped Changes are revalidated; continuing Changes durably rebind to the new accepted revision before work resumes.

### Source change

Concrete code/tests/docs/config/migrations implement a Change. They have no separate planning identity.

Every source change that affects mapped areas must update all affected Design maps and the traceability index before final review.

## Canonical Machine-Readable Syntax

Protocol-v3 structural fields use one exact repository grammar rather than general Markdown/CommonMark equivalence.

- top metadata is column-zero `Key: value` before the first `## ` section;
- an `Implementing` or `Realized` Design uses `## Realization Map` as its first level-two section;
- Realization Map labels are exactly `Changes:`, `Areas:`, `Tests:`, `Current-truth docs:` in that order;
- mapped paths use exact `- \`<path>\` — Target|Realized` syntax;
- `docs/designs/INDEX.md` is a dedicated projection file with exactly one literal canonical table header occurrence in the entire file;
- Markdown/HTML-equivalent alternate spellings are not alternate protocol syntax; noncanonical forms are invalid where machine-readable structure is expected.

Tooling may reject noncanonical syntax even when a Markdown renderer would display it similarly. This keeps the repository format a small deterministic API.

## Design Traceability

`docs/designs/INDEX.md` contains realized mappings only and is a disposable navigation projection.

A realized Design remains while useful as a current conceptual map. It is not an archive.

Partial supersession switches realized mapping only when replacement source is actually realized; old/new Design maps and index update atomically in the same final reviewed head.

## Branch Model

- `main` — stable/releasable current truth
- `develop` — reviewed integration truth
- `design/<design-id>` — one Design proposal
- `feature/<change-id>` — one implementation Change

`main` and `develop` are protected. Repository-host rulesets/branch protection are authoritative; both require PRs and block force pushes/deletion for agent credentials.

## Completion and Review

Completed Change coordination artifacts are removed after folding.

Before final implementation review:

1. satisfy acceptance criteria
2. fold code/tests/current docs
3. update affected Design realization maps/index/status
4. make CURRENT merge-safe
5. remove completed CHANGE.md
6. push final head
7. run independent reviewer/CI on that exact final head

Any later push invalidates the clean verdict.

## Roles and Runtimes

`.agents/<role-id>.md` describes roles. Runtime/model/vendor is invocation state, not repository identity.

Architect owns Design convergence/decomposition/revalidation. Implementer owns Change implementation/folding. Reviewer owns independent latest-head verdict.

## Compatibility

Protocol changes are explicit and versioned. Structural or semantic breaking changes increment the protocol version.

### v1 → v2

v2 introduced runtime-neutral roles, `main`/`develop`/feature lifecycle, protected branch verification, and current-truth folding semantics.

### v2 → v3

v3 is a semantic and structural change:

- adds canonical `docs/designs/` and `docs/designs/INDEX.md`
- separates Design, Change, and source diff
- adds `design/<design-id>` branches/Design PR lifecycle
- requires initial Design for brand-new projects
- binds Design-derived Changes to exact accepted Design revisions
- adds per-area Target/Realized traceability and supersession rules
- narrows ADRs to cross-cutting rationale independent of one Design
- requires Design map/index folding before final latest-head review

Existing v2 projects remain v2 until semantically migrated. Do not merely change the version marker without adopting v3 repository semantics.

`init/` creates projects at the protocol version shipped with the checkout.
`migrate/` is responsible for future semantic migration to a target version.
`check/` validates targeted protocol/repository properties.

## Design Principle

Keep the protocol small, current-state-first, vendor-neutral, Git-backed, and optimized for one human coordinating multiple AI agents.
