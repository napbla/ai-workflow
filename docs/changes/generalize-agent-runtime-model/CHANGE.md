# Generalize Agent Runtime Model and Branch Lifecycle

Status: Verifying
Owner: implementer (runtime assigned at invocation)

## Goal

Evolve the workflow to protocol v2 by separating role identity from AI runtime/vendor and by formalizing a stable/integration/feature branching model.

The repository remains the canonical transferable project state, but canonical state is branch-sensitive:

- `main` represents stable integrated truth.
- `develop` represents reviewed integration truth.
- active work lives on feature branches derived from `develop`.

## Branch Model

### `main` — stable

- Stable/releasable current truth.
- No active-change coordination artifacts are introduced directly on `main`.
- Implementers must not push directly to `main`.
- Implementers must not configure `main` as a push/upstream target.
- Changes reach `main` through reviewed integration from `develop`.
- Direct updates are reserved for explicit repository administration/bootstrap or emergency repair.

### `develop` — integration

- Integration branch for accepted feature work.
- New feature branches start from latest `develop`.
- Feature branches merge back into `develop` through PR/review.
- Implementers must not push directly to `develop`.
- Implementers must not configure `develop` as a push/upstream target.
- `develop` may be ahead of `main`.

### Feature branches

Default naming:

`feature/<change-id>`

Current branch:

`feature/generalize-agent-runtime-model`

A feature branch may contain the active `CHANGE.md`, branch-local status, implementation, tests, and current-truth updates.

Before merging a completed feature into `develop`:

1. verify acceptance criteria;
2. fold durable knowledge into the appropriate current-truth surfaces;
3. remove the active change artifact;
4. make branch-local status appropriate for the expected post-merge integration state;
5. merge through PR/review.

Release/integration from `develop` to `main` must leave `main` with stable, non-transient current state.

## Role Identity and Runtime Assignment

- Core agent identities are role-oriented, e.g. `architect`, `implementer`, `reviewer`.
- Runtime/model/vendor is assigned at invocation time and may change without changing the workflow contract.
- The protocol does not permanently bind ChatGPT, Claude Code, Codex, or future runtimes to roles.
- A role may be fulfilled by different runtimes in different sessions.

## Runtime Capability Boundaries

- Role responsibility and runtime capability are separate.
- Agents act only within capabilities actually available in their runtime.
- PR ownership means lifecycle responsibility, not guaranteed GitHub permissions.
- If push, PR creation, review publishing, or merge is unavailable, hand that action to the human or another capable agent without losing lifecycle ownership.

## Protected Branch Policy

Implementers may, when supported: edit, test, commit, push their working branch, and update its PR.

Implementers must not:

- push directly to `main` or `develop`;
- push any refspec whose destination is `main` or `develop`;
- set `main` or `develop` as upstream/push targets;
- bypass policy with force/mirror/all-style pushes to protected integration branches.

Core protocol defines this policy. Runtime-specific enforcement belongs in adapters.

For Claude Code, add a project-level `PreToolUse` Bash hook that blocks protected-branch operations while allowing normal feature-branch pushes. Local Git safeguards and GitHub branch protection/rulesets are stronger complementary layers.

## Review Delivery

- Reviewers must produce actionable review findings.
- Publishing as a PR review/comment is preferred.
- If PR write access is unavailable, returning findings to the invoking human/agent is a valid fallback.
- GitHub transport failure alone does not invalidate a completed review.

## Durable Current Truth

Completion must place durable knowledge in the most appropriate surface: code, tests, module docs, specs, architecture docs, or ADRs as appropriate.

Do not require every completed behavior change to duplicate itself in `docs/specs/`.

## Status Semantics

`docs/status/CURRENT.md` is branch-sensitive:

- `main`: stable integrated state;
- `develop`: integration state;
- feature branch: active change/review state for that branch.

A branch being merged must carry status suitable for the target's expected post-merge state so merge does not immediately make status stale.

## Autonomous Change Execution

Once the human finalizes a change intent and the Architect materializes the active change, the default path should require no further human coordination until a PR is ready for human merge review.

Target loop:

```text
Human finalizes intent
        ↓
Architect materializes change on feature branch
        ↓
Implementer runtime takes ownership
        ↓
implement → test → commit → push feature branch
        ↓
create/update PR targeting develop
        ↓
reviewer runs
        ↓
actionable findings / CI failures?
     yes ↓                 no
 Implementer fixes          ↓
 commit + push          final verification
        └──────────────→     ↓
                       ready-for-human-merge
```

Automation expectations:

- The implementer may use a repository-scoped credential/token to push its feature branch and create/update its PR.
- Credentials must not be stored in repository files.
- Branch policy must prevent that credential/runtime from updating `main` or `develop` directly.
- Review and CI feedback should be consumed automatically when the runtime supports it.
- Human PR comments/reviews are first-class feedback: any actionable human feedback returns the PR to the implementation loop until it is addressed and re-verified.
- The implementer remains responsible for iterating on actionable automated-review, CI, and human-review feedback until the PR is clean or an issue exceeds its authority/capability.
- Human feedback that is implementation-level and preserves the accepted intent/scope stays in the same PR loop.
- Human feedback that materially changes the accepted intent, acceptance criteria, architecture, or scope ends the current change instead of mutating the existing PR into a different job.
- In that case, close the current PR/change without merging, create a new change/feature branch/PR from the appropriate integration baseline, and carry forward only artifacts that remain valid (for example end-to-end/regression tests, reusable implementation pieces, or verified findings).
- The new change must state the new intent and acceptance criteria explicitly; the closed PR remains historical coordination evidence, not current truth.
- If it is unclear whether feedback is a refinement or a materially new change, escalate rather than silently expanding scope.
- Human attention is requested only for ambiguity, consequential decisions, blocked credentials/infrastructure, or the final merge decision.
- The terminal state for autonomous execution is `ready-for-human-merge`, not automatic merge into `develop` or `main`.
- Runtime-specific automation mechanisms (for example Claude Code review/fix loops or hooks) are adapters; the protocol defines the lifecycle contract rather than requiring a particular vendor feature.

## Acceptance Criteria

- [x] Protocol documents the `main` / `develop` / feature branch model.
- [x] `main` is stable/releasable truth and `develop` is integration truth.
- [x] New feature work branches from `develop` and merges back through PR/review.
- [x] Implementers cannot directly push or set upstream/push targets to `main` or `develop`.
- [x] Generated defaults use runtime-neutral role identities instead of vendor-name identities.
- [x] Runtime assignment to roles is invocation/runtime state.
- [x] Role responsibility is separated from runtime capabilities/permissions.
- [x] PR ownership supports capability-aware handoff.
- [x] After human intent finalization, the normal workflow can run autonomously through implementation, tests, feature-branch push, PR creation/update, review-feedback iteration, and final verification until `ready-for-human-merge`.
- [x] Human interaction is not required during the autonomous loop unless risk, ambiguity, authority, credentials, or infrastructure require escalation.
- [x] Actionable human PR comments that preserve the accepted change intent re-open the implementation loop: sync feedback → implement → test → push → re-verify until the PR is ready for human merge again.
- [x] Human feedback that materially changes intent, acceptance criteria, architecture, or scope closes the current PR/change and starts a new feature branch/PR rather than mutating the old one.
- [x] A replacement change may reuse still-valid evidence such as end-to-end/regression tests and implementation fragments, but its new intent and acceptance criteria are materialized explicitly in repository state.
- [x] Runtime credentials are never stored in repository state and cannot directly update protected integration branches.
- [x] Reviewer workflow has a fallback when PR publishing is unavailable.
- [x] Completion rules require appropriate current truth instead of mandatory `docs/specs/` duplication.
- [x] Status semantics prevent pre-merge state becoming stale on the target branch.
- [x] Claude protected-branch enforcement is implemented as a runtime adapter/hook without making the core protocol Claude-specific.
- [x] Guard tests cover allowed feature-branch pushes and denied protected-branch/upstream cases.
- [x] Initializer/self-bootstrap output conforms to protocol v2.
- [x] Protocol version is incremented under compatibility rules.
- [x] Current repository branching state is internally consistent.

## Evidence From v1 End-to-End Test

The first workflow test showed that repo-based handoff works, but also revealed runtime permission differences, review-publishing failure as a transport concern, unnecessary spec duplication for small local behavior, post-merge status staleness, and the mistake of placing transient active-change state directly on `main`.

## Implementation Notes

Open design questions were resolved during implementation and recorded in `docs/adr/0001-protocol-v2-roles-and-branch-model.md`:

- Simultaneous role instances share the role ID; distinct instance IDs are deferred.
- Protected branches (`main`, `develop`) are fixed by the protocol, not configurable; adapters hard-code them.
- `develop` → `main` is a normal reviewed PR; no release artifact.
- A Git `pre-push` helper is optional/documented, not generated.

Decisions taken under implementer `architecture: propose` authority, flagged for architect/human confirmation at merge review:

- New top-level `adapters/` module (`adapters/claude-code/`) holds runtime enforcement; `.claude/settings.json` registers the hook in place.
- Fixed (non-configurable) protected branch names.

Verification: `python -m unittest discover -s init/tests` and `python -m unittest discover -s adapters/claude-code/tests`. `init/tests` also asserts this repository's generated files match init output.
