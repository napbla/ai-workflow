# ADR 0001: Protocol v2 — role identities, runtime assignment, and branch model

Status: Accepted when merged into `develop`. Decision 3 (fixed branch names) was proposed by the implementer under `architecture: propose` authority; the merge review confirms or rejects it. Decision 4 is the human operator's decision.

## Context

The first end-to-end use of protocol v1 showed that repository-based handoff works, but also exposed:

- agent files named after vendors (`chatgpt`, `claude-code`, `codex`), which bound a role to one runtime even though any capable runtime could fill it;
- runtimes with different permissions (one could not push or open PRs), so "PR ownership" could not mean "has GitHub write access";
- review publishing failing for transport reasons while the review itself was complete;
- small local behavior being duplicated into `docs/specs/` only because completion rules required it;
- `docs/status/CURRENT.md` going stale immediately after merge;
- transient active-change state committed directly on `main`.

A first v2 attempt (closed PR #2) also enforced the protected branch policy with a Claude Code hook that parsed shell and Git commands. It grew into a partial reimplementation of Bash and Git semantics and still could not be a security boundary, so the human operator rejected that approach.

## Decision

1. **Agent identity is a role ID** (`architect`, `implementer`, `reviewer`, …). The runtime fulfilling a role is chosen at invocation and never recorded in the repository. Role capabilities describe expectations, not guaranteed runtime permissions; an agent hands unavailable actions to a capable party and keeps lifecycle ownership.
2. **Branch model**: `main` is stable truth, `develop` is reviewed integration truth, and each active change lives on `feature/<change-id>` from `develop`. Active-change artifacts never land directly on `main`.
3. **Protected branches** `main` and `develop` are fixed by the protocol, not configurable per project. Implementers never push to them or set them as upstream/push targets.
4. **Repository-host protection is the enforcement boundary.** GitHub branch protection or rulesets must require a PR and block force pushes and deletion on `main` and `develop`, without bypass for agent credentials. ai-workflow does not parse commands to reproduce this locally; it only verifies host state (`check/branch_protection.py`) and treats missing or unverifiable protection as a human setup blocker.
5. **Autonomous execution ends at `ready-for-human-merge`.** Feedback that refines accepted intent stays in the PR loop; feedback that changes intent, acceptance criteria, architecture, or scope starts a new change.
6. **Release from `develop` to `main` is a normal reviewed PR**; no separate release artifact.
7. **Completion folds knowledge into the most appropriate current-truth surface** rather than always `docs/specs/`.
8. **Status is merge-safe current truth.** Status stays branch-sensitive: a feature branch's status may describe that branch's own active change. Whatever merges into `develop` or `main` must already be true there after the merge. PR readiness, pending review, pending merge or release, and ahead/behind comparisons between branches stay in the PR or active change.

## Consequences

- Swapping the runtime behind a role needs no repository change.
- Branch names are not configurable; a project needing other names would require a protocol change (or a future `.ai-workflow.yml` setting).
- Simultaneous instances of one role share a role ID; distinct instance IDs are deferred until a real need appears.
- The core protocol stays runtime-neutral, and no agent tool hook is needed. Runtime-specific hooks may still be added as conveniences, but they are not part of the protocol and not security boundaries.
- Verification needs a credential that can read the repository's protection settings; without one, protection is reported as unverifiable, never assumed.
- v1 projects need a semantic migration (see `spec/SPEC.md`, "v1 → v2").
