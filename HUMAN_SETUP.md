# Human Operator Guide

This workflow is designed for **one human operator working with multiple AI agents**. Another human should be able to take over by reading the repository without prior conversations.

## 1. One-time setup

1. Create a Git repository and push it to the repository host.
2. Run `python init/init.py --target <repo>` from an ai-workflow checkout and choose the roles you need.
3. Commit the generated v3 repository state on `main`.
4. Create `develop` from `main` and push it.
5. Protect `main` and `develop`: require PRs, block force pushes and deletion, and do not give agent credentials bypass permission.
6. For the ai-workflow repository, require the GitHub Actions check named `core-tests` on both `main` and `develop`. Consumer projects should require their own equivalent CI checks once those checks exist.
7. With the agent runtime token in `GH_TOKEN` or `GITHUB_TOKEN`, run `python <ai-workflow>/check/branch_protection.py`. Any non-zero result is a setup blocker. This script verifies PR/force-push/deletion protection; it does not yet verify required status checks.
8. Connect repository access to the AI runtimes you use.
9. Treat the repository as canonical project state.

### Runtime credentials

Give implementer runtimes repository-scoped credentials with only the permissions required to push their own branches and manage PRs. Keep credentials outside the repository. Server-side branch protection is the enforcement boundary.

### Invoke roles, not vendors

Example:

```text
You are the implementer. Sync the repository and work on feature/<change-id>.
```

Runtime/model/vendor choice is per invocation and is not repository identity.

## 2. Start every brand-new project with a Design

For a new project, do not begin implementation from chat alone.

```text
Human ↔ Architect exploration
        ↓
design/<design-id>
        ↓
docs/designs/<design-id>/DESIGN.md
        ↓
Design PR → develop
        ↓
human comments / architect revises
        ↓
final fold
        ↓
human accepts exact final head
        ↓
merge accepted Design
```

The Design describes target state, not current behavior.

The architect then decomposes it into one or more implementation Changes.

## 3. Consequential redesigns also use Design PRs

Use a Design PR when an existing project needs human review of:

- product intent
- public/internal contracts
- architecture boundaries
- persistence/domain model
- cross-module constraints
- consequential trade-offs

A tiny/local fix can skip a separate Design when target state is already obvious.

## 4. Design review is allowed to change the target

A Design PR is the place to debate and revise intent/architecture/scope.

Before accepting it:

1. fold accepted review decisions into canonical Design sections
2. remove review-provenance/transient summary sections
3. create an ADR only when rationale is cross-cutting and must live independently
4. push the final Design head
5. accept/merge that exact head

Any semantic push after acceptance makes that acceptance stale.

## 5. Derive implementation Changes

Each coherent implementation job gets its own `feature/<change-id>` and normally:

```text
docs/changes/<change-id>/CHANGE.md
```

If derived from a Design, the Change records:

```text
Design: docs/designs/<design-id>/DESIGN.md
Design-Revision: <accepted-design-commit-sha>
```

One Design may create multiple Changes.

The Change identity is accepted intent + acceptance criteria + explicit non-negotiable constraints. The implementation plan may pivot without creating a new Change while that identity stays the same.

If the Design itself changes later, the architect revalidates all incomplete derived Changes. Continuing Changes must update their `Design-Revision` before work resumes.

## 6. Implementation PR loop

```text
implementer owns Change PR
        ↓
implement → test → push
        ↓
reviewer / CI
        ↓
fix/re-review until implementation is sound
        ↓
final fold:
  current docs + Design maps/index + status
  remove completed CHANGE.md
        ↓
push final HEAD
        ↓
reviewer / CI on final HEAD
        ↓
ready-for-human-merge
        ↓
human merge
```

The implementer never self-certifies a clean review. Any push after the clean verdict requires re-review.

Runtime-specific PR watchers/autofix/review triggers are useful accelerators but not shared protocol semantics.

## 7. Use Design traceability instead of rereading the whole repo

`docs/designs/INDEX.md` is a reverse-lookup navigation projection of **realized mappings only**.

A realized Design contains a Realization Map showing which:

- source areas
- tests
- current docs
- implementation Changes

currently realize it.

When a source change touches an area mapped by any Design, update every affected Design map and the index before final review, even if the Change came from somewhere else.

This lets a replacement agent start from the relevant Design and inspect only mapped code/tests/docs.

## 8. Realization and supersession

A Design can be `Implementing` overall while individual areas are already `Realized`.

A replacement Design does not take over reverse lookup merely because it is Accepted/Implementing. Mapping switches only when replacement source is actually realized; old/new maps and the index update atomically in the same final reviewed head.

A fully implemented Design becomes `Realized` and remains while useful as a current conceptual map. Remove it only when fully superseded/no longer useful; Git preserves history.

## 9. ADRs are exceptional

Put rationale in the relevant Design by default.

Use `docs/adr/` only for decisions that cut across multiple Designs or must remain independently understandable after a Design is superseded.

## 10. Refresh repository context

When current state matters, say:

```text
sync repo
```

For focused implementation:

```text
sync repo, then review docs/changes/<change-id>/CHANGE.md and its bound Design revision
```

Agents should continue from repository state, not remembered chat.

## 11. Human involvement is exception-driven

Human attention is primarily for:

- priorities
- target Design acceptance
- ambiguous product intent
- decisions outside agent authority
- consequential trade-offs
- blocked credentials/infrastructure
- final merge decisions

Do not add human gates merely for ceremony.

## 12. Operator dashboard

`docs/status/CURRENT.md` is the current handoff/dashboard view.

It should summarize:

- current objective
- relevant Designs and aggregate state
- active Changes
- human attention
- blockers/risks
- next durable action

It must be merge-safe. Pending PR review/merge/release state belongs in the PR or active artifact, not CURRENT.

## 13. Human replacement test

A replacement operator should be able to read:

```text
WORKFLOW.md
AGENTS.md
docs/status/CURRENT.md
docs/designs/INDEX.md
relevant docs/designs/*/DESIGN.md
docs/changes/
docs/specs/
docs/architecture/
relevant ADRs
```

and answer:

- What exists now?
- What target state has been accepted?
- What Change is active?
- Which Design explains this code?
- What needs human attention?

If old chat logs are required, repository state is incomplete.

## Keep supporting tools separate

The repository conventions are the integration contract. Core protocol tools (`spec`, `init`, `migrate`, `check`) stay modular. Dashboards/runners/other consumers should remain separate and must not become a second canonical datastore.
