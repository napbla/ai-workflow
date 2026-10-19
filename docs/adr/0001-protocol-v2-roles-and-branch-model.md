# ADR 0001: Protocol v2 — role identities, runtime assignment, and branch model

Status: Accepted when merged into `develop`. Decisions 3 (fixed branch names) and 4 (the `adapters/` module) were proposed by the implementer under `architecture: propose` authority; the merge review confirms or rejects them.

## Context

The first end-to-end use of protocol v1 showed that repository-based handoff works, but also exposed:

- agent files named after vendors (`chatgpt`, `claude-code`, `codex`), which bound a role to one runtime even though any capable runtime could fill it;
- runtimes with different permissions (one could not push or open PRs), so "PR ownership" could not mean "has GitHub write access";
- review publishing failing for transport reasons while the review itself was complete;
- small local behavior being duplicated into `docs/specs/` only because completion rules required it;
- `docs/status/CURRENT.md` going stale immediately after merge;
- transient active-change state committed directly on `main`.

## Decision

1. **Agent identity is a role ID** (`architect`, `implementer`, `reviewer`, …). The runtime fulfilling a role is chosen at invocation and never recorded in the repository. Role capabilities describe expectations, not guaranteed runtime permissions; an agent hands unavailable actions to a capable party and keeps lifecycle ownership.
2. **Branch model**: `main` is stable truth, `develop` is reviewed integration truth, and each active change lives on `feature/<change-id>` from `develop`. Active-change artifacts never land directly on `main`.
3. **Protected branches** `main` and `develop` are fixed by the protocol, not configurable per project. Implementers never push to them or set them as upstream/push targets.
4. **Enforcement is layered**: repository-host branch protection is authoritative; runtime adapters (`adapters/`, e.g. a Claude Code PreToolUse hook) are best-effort early guards; local Git `pre-push` hooks are optional and documented, not generated.
5. **Autonomous execution ends at `ready-for-human-merge`.** Feedback that refines accepted intent stays in the PR loop; feedback that changes intent, acceptance criteria, architecture, or scope starts a new change.
6. **Release from `develop` to `main` is a normal reviewed PR**; no separate release artifact.
7. **Completion folds knowledge into the most appropriate current-truth surface** rather than always `docs/specs/`.
8. **Status is branch-sensitive** and must be correct for the target branch at merge time.

## Consequences

- Swapping the runtime behind a role needs no repository change.
- Branch names are not configurable; a project needing other names would require a protocol change (or a future `.ai-workflow.yml` setting).
- Simultaneous instances of one role share a role ID; distinct instance IDs are deferred until a real need appears.
- Adapters live in their own module so the core protocol stays runtime-neutral.
- v1 projects need a semantic migration (see `spec/SPEC.md`, "v1 → v2").
