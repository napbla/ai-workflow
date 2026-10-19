# Protocol v2 with GitHub-Enforced Branch Protection

Status: Planned
Owner: implementer (runtime assigned at invocation)

## Goal

Deliver protocol v2 with the agreed runtime-neutral role model, branch lifecycle, autonomous PR loop, completion semantics, and branch-sensitive status model, while simplifying protected-branch enforcement.

The key simplification is:

- GitHub branch protection / rulesets are the authoritative enforcement mechanism for `main` and `develop`.
- The workflow does not attempt to parse arbitrary shell/Git commands to reproduce GitHub's protection locally.
- Repository tooling only needs to verify whether the required GitHub protections are configured and surface a human setup blocker when they are not.

## Branch Model

- `main`: stable/releasable current truth.
- `develop`: integration branch.
- `feature/<change-id>`: active work branches created from `develop`.
- Feature work reaches `develop` through PR/review.
- Stable integration reaches `main` through reviewed `develop` → `main` integration.

## Runtime-Neutral Roles

Core role identities are:

- `architect`
- `implementer`
- `reviewer`

Runtime/model/vendor is invocation state, not durable role identity. Claude, Codex, ChatGPT, or another runtime may fill any role when capable.

## Autonomous Change Execution

After the human finalizes intent, the normal path should proceed without further human coordination until a PR is ready for human merge review:

```text
human finalizes intent
        ↓
change materialized on feature branch
        ↓
implementer
  implement → test → commit → push
        ↓
create/update PR → develop
        ↓
reviewer / CI
        ↓
findings?
 yes → implementer fixes → push → reviewer again
 no  → ready-for-human-merge
        ↓
human reviews / comments / merges
```

Implementation-level human PR feedback stays in the same loop. Human feedback that materially changes intent, acceptance criteria, architecture, or scope closes the current PR/change and starts a new change.

The implementer cannot self-certify review completion; the reviewer owns the review verdict on the latest head.

## Simplified Protected-Branch Requirement

### Authoritative enforcement

GitHub must protect both `main` and `develop` against direct updates that bypass the reviewed PR workflow.

The protocol should require repository-host configuration such as branch protection rules or rulesets that prevent direct pushes to those branches for the credentials used by agents/implementers.

### Verification only

ai-workflow should not implement a shell/Git semantic guard.

Instead, provide the smallest practical verification path that answers:

```text
Are main and develop protected as required?
```

If yes:

- continue normal autonomous execution.

If no or unverifiable:

- surface a clear human-attention/setup blocker;
- explain what GitHub protection must be configured;
- do not claim the repository is protected.

Verification may live in the existing `check/` capability or another small vendor adapter, but it must remain simple and focused on repository-host state rather than command parsing.

Credentials/tokens must never be committed to repository state.

## Review Delivery

- Reviewer produces actionable findings against the latest PR head.
- PR review/comment is preferred when transport is available.
- If review publishing is unavailable, findings may be returned to the invoking human/agent.
- Transport failure alone does not invalidate the review.
- A PR reaches `ready-for-human-merge` only when the latest head has a clean reviewer verdict and any required CI/checks pass.

## Durable Current Truth

Completion folds durable knowledge into the most appropriate surface: code, tests, module docs, specs, architecture docs, or ADRs as appropriate.

Do not require every behavior change to duplicate itself in `docs/specs/`.

## Status Semantics

`docs/status/CURRENT.md` is branch-sensitive:

- `main`: stable integrated state;
- `develop`: integration state;
- feature branch: active change/review state.

Before merge, feature-branch status must be written so the target branch will not immediately contain stale pre-merge state.

## Carry Forward From Closed PR #2

PR #2 was closed without merge because the branch-enforcement architecture became overcomplicated and the human changed that architectural requirement.

The replacement change may selectively reuse still-valid work from PR #2, including:

- role-neutral agent identities;
- protocol versioning/migration notes;
- `main` / `develop` / feature lifecycle docs;
- autonomous execution semantics;
- reviewer ownership semantics;
- branch-sensitive status/completion semantics;
- initializer/template updates;
- tests unrelated to the removed local Git parser;
- ADR material that remains consistent with this simplified design.

Do not carry forward the complex Claude protected-branch command parser or requirements that depend on it.

Historical source:

- closed PR #2
- last known PR #2 head at closure: `43bcd32a2f70294353cdf0e83714363b9dba644b`

## Acceptance Criteria

- [ ] Protocol version is v2 if required by compatibility rules.
- [ ] Generated/default role identities are runtime-neutral (`architect`, `implementer`, `reviewer`).
- [ ] Runtime assignment is documented as invocation state.
- [ ] `main`, `develop`, and `feature/<change-id>` lifecycle is documented and reflected in generated/self-bootstrap state.
- [ ] Implementer ownership, reviewer ownership, and autonomous execution to `ready-for-human-merge` are documented.
- [ ] Human feedback semantics distinguish refinement from materially new work.
- [ ] Completion rules use the appropriate current-truth surface rather than mandatory specs duplication.
- [ ] Branch-sensitive status semantics prevent stale post-merge status.
- [ ] Complex Claude/local Git command parsing is removed from the required design.
- [ ] GitHub branch protection/rulesets are the authoritative protection requirement for `main` and `develop`.
- [ ] There is a simple way to verify whether required GitHub protection is configured.
- [ ] Missing/unverifiable GitHub protection is surfaced as a human setup blocker with clear remediation.
- [ ] No token/credential is stored in repository state.
- [ ] Tests cover protocol generation and the branch-protection verification behavior that can be tested deterministically.
- [ ] This repository's generated/self-bootstrap state conforms to the accepted v2 protocol.

## Non-Goals

- Parsing arbitrary Bash syntax.
- Reimplementing Git refspec/config semantics.
- Preventing every possible local bypass.
- Treating a Claude hook as a security boundary.

GitHub repository-host protection is the security boundary.
