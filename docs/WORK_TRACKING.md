# Work Tracking Rules

This file defines when project state must be written to the repository.

## Principle

Use the minimum artifact needed for another human or agent to continue the project without the current conversation.

The repository is canonical. External issue trackers are not required.

## Decision Test

Ask:

> Will another human or agent need this after the current conversation, coding session, branch, or review disappears?

- **No** → keep it temporary.
- **Yes** → materialize it in the repository.

## 1. Exploration

Brainstorming, discarded ideas, and unresolved discussion may stay in Chat.

Create repository state only when discussion produces:

- committed work
- a durable requirement or constraint
- a decision future agents must understand
- a blocker or open question that must survive the session

Do not preserve conversation for its own sake.

## 2. Active Changes

Use `docs/changes/<change-id>/CHANGE.md` for non-trivial committed work that needs cross-session or cross-agent coordination.

The active change lives on its feature branch (`feature/<change-id>` by default), never directly on `main`.

Recommended shape:

```md
# Change Title

Status: Planned | In Progress | Blocked | Verifying
Owner: <human-or-role-id>

## Goal

## Constraints

## Acceptance Criteria

- [ ] ...

## Notes

Only durable context, blockers, or decisions needed to continue the change.
```

Use checklist state as progress evidence. Do not invent percentage completion.

Add `DESIGN.md` only when design complexity justifies a separate artifact.

## 3. Small Fixes

A small local fix does not need a change artifact when all are true:

- scope is obvious
- risk is low
- one session/agent can complete it
- no durable coordination context is needed

The code, regression test, commit, and PR may be sufficient evidence.

## 4. Bugs During Active Work

If a bug belongs to an active change:

1. fix it within the same change/branch when practical
2. add or update a regression test when appropriate
3. update `CHANGE.md` only if scope, acceptance criteria, blockers, or durable assumptions changed
4. update current specs if the expected behavior was previously wrong or missing

Do not create a separate bug artifact merely for bookkeeping.

## 5. Bugs After Merge

Treat a post-merge bug according to coordination need:

- tiny, local, low-risk bug → direct fix + regression test may be enough
- non-trivial bug or multi-session work → create a new active change
- bug exposing incorrect current behavior documentation → update the relevant spec
- bug exposing a durable architectural mistake/decision → update architecture and use an ADR only when future rationale matters

## 6. Scope Discovered During Implementation

Do not silently expand active work when the new scope is materially independent.

Choose one:

- add it to the current change if it is required to satisfy the same goal
- create a separate active change if it can be delivered independently
- escalate when prioritization or trade-offs require human judgment

## 7. Review Feedback

PR comments and reviews are coordination surfaces.

Before merge, ensure any durable outcome is reflected in one or more of:

- code
- tests
- current spec
- current architecture
- ADR
- active change acceptance criteria/notes

Do not copy every review comment into documentation.

Feedback that preserves the accepted intent stays in the same change and PR. Feedback that materially changes intent, acceptance criteria, architecture, or scope starts a new change instead (see Autonomous Change Execution in `WORKFLOW.md`).

## 8. Completing a Change

Before merge/close:

1. verify acceptance criteria
2. fold durable knowledge into the most appropriate current-truth surface: code, tests, module docs, `docs/specs/`, or `docs/architecture/`
3. create/update ADR only if durable rationale is worth preserving
4. ensure tests capture important behavioral regressions
5. make `docs/status/CURRENT.md` merge-safe: true on the target branch after the merge, and still true after the next `develop` → `main` merge, with no PR readiness, pending review, or pending release state (see Project Status in `WORKFLOW.md`)
6. remove `docs/changes/<change-id>/` from the working tree

Do not duplicate behavior in `docs/specs/` when code, tests, or module docs already state it clearly.

Git preserves merged code and durable documentation history. The active `CHANGE.md` itself is not required to survive completion; this remains valid even when a squash merge removes its intermediate branch history. Do not move it to an archive directory.

## 9. Current-State Rule

A new agent should not need completed change files to understand the system.

If deleting an active change would remove knowledge required to operate or modify the current system, that knowledge belongs in current specs, architecture, ADRs, code, or tests first.
