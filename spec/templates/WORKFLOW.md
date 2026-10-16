# $project_name — AI-Native Project Workflow

Protocol: `ai-workflow v$protocol_version`

This repository is the transferable shared state for one human operator working with multiple AI agents.

## North Star

The project should remain operable by:

- one human operator coordinating multiple AI agents
- a replacement human who has not seen prior conversations
- progressively more autonomous agents as capabilities improve
- bounded projects with zero human intervention when authority and reliability eventually permit it

Human involvement is required by **risk, uncertainty, and authority**, not by ceremony.

## Source of Truth

The Git repository is the source of truth.

Conversation history, PR comments, CI messages, and external tools are coordination surfaces. They are not canonical project state.

## Modularity and Tool Boundaries

Keep tools small and composable. Each tool should do one job well and exchange project state through repository conventions rather than private integration state.

The repository format is the protocol between tools and agents. A dashboard, initializer, validator, runner, or future agent system may read or update the same repository state without requiring tight coupling to another tool's implementation.

Do not introduce a second canonical datastore merely for convenience. Tool-specific caches or indexes must be disposable projections of repository state.

## State Model

- `docs/specs/` — current product/system behavior
- `docs/architecture/` — current technical design and contracts
- `docs/adr/` — durable rationale for important decisions future agents must understand
- `docs/changes/` — active work only
- `docs/status/CURRENT.md` — current operator-facing project snapshot
- code and tests — executable current truth
- Git history — historical record

Do not maintain a separate archive of completed changes. When active work is complete, fold durable knowledge into current-state artifacts and remove the active change artifact. Git preserves the history.

## Agent Bootstrap

Agent identity must come from the execution environment or invocation prompt. The repository defines what that identity means.

Before working, every agent must read:

1. `WORKFLOW.md`
2. `AGENTS.md`
3. `.agents/<its-agent-id>.md`
4. `docs/WORK_TRACKING.md`
5. relevant current-state artifacts
6. the relevant active change, if one exists

If agent identity is not explicit, do not guess it.

Do not rely on previous conversation history when repository artifacts exist.

## Context Refresh

Conversation context may be stale.

A request such as `sync repo` means:

1. refresh relevant repository state using available repository access
2. re-read current rules and role if relevant
3. inspect active changes and affected current-state artifacts
4. inspect changed code/tests when needed
5. continue from repository state, not remembered conversation state

If repository access is unavailable, say so rather than silently using stale context.

## Active Change Lifecycle

Use the lightest path that preserves transferable project state.

### Exploration

Exploratory discussion stays in conversation until there is committed work, a durable decision, or cross-session follow-up.

### Normal Change

For non-trivial committed work:

`Explore → Active Change → Implement → Verify → Fold Current Truth → Remove Active Change → Merge`

An active change normally needs only:

`docs/changes/<change-id>/CHANGE.md`

Add `DESIGN.md` only when the change is complex enough to benefit from it.

### Small Fix

A small, local, low-risk fix may go directly to code + tests without a change artifact when no other human or agent needs persistent coordination context.

### Decision Escalation

Do not hard-code approval gates into the lifecycle.

Escalate to the human operator or configured higher authority when:

- the decision exceeds the agent's configured authority
- risk or uncertainty is material
- requirements conflict
- a consequential trade-off needs higher-authority judgment

If future role policy grants greater authority to agents—or removes the human from a bounded workflow—the same operating model should continue without redesign.

## Risk and Authority

### Low Risk

Examples: private helpers, local naming, implementation details, local refactoring.

Agents may decide within their assigned authority.

### Medium Risk

Examples: internal APIs, module data structures, dependencies.

Agents may proceed when their role permits it. Record only decisions that another agent or future session must know.

### High Risk

Examples: public contracts, persistence, core domain models, module boundaries, security-sensitive behavior, major architecture.

Proceed only within assigned authority. Otherwise record the issue in the active change and escalate to the configured higher authority.

## Durable Decisions

Use an ADR only when the rationale remains useful after the implementation is complete.

An ADR should answer a future question such as: "Why is the system intentionally designed this way?"

Do not use ADRs as a changelog. Git is the changelog.

When an accepted decision changes current behavior or architecture, update the corresponding `docs/specs/` or `docs/architecture/` artifact.

## Implementation Rules

- Make the smallest change that satisfies the goal.
- Preserve current contracts unless the change explicitly modifies them.
- Avoid unrelated refactoring.
- Follow current repository patterns.
- Add or update tests when behavior changes.
- Update current-state documentation when behavior or architecture changes.
- Surface uncertainty instead of silently inventing requirements.
- Do not create process artifacts that exist only to compensate for temporary model limitations.

## Pull Request Ownership

When work uses a pull request, the assigned implementer owns it until handoff or merge.

Within its runtime capabilities and authority, the implementer should:

- keep the PR scoped to the active change
- respond to actionable review feedback
- address relevant CI failures
- update tests and current-state documentation when needed
- push follow-up fixes to the same PR when supported

PR comments coordinate work; durable outcomes must be reflected in repository state before merge.

## Review Rules

Review against:

1. active change goal and acceptance criteria
2. current specs and architecture
3. relevant ADRs
4. correctness and compatibility
5. tests
6. unnecessary complexity

Reviewers should identify actionable problems before rewriting implementation unless explicitly assigned to fix them.

## Project Status

`docs/status/CURRENT.md` is the operator dashboard, not a historical report.

It should make it possible for a human replacement to quickly answer:

- What is the project trying to do now?
- What active changes exist?
- What is blocked or risky?
- What requires human attention?
- What should happen next?

Derive status from repository evidence. Do not infer it from chat history. Do not maintain status archives by default; Git preserves prior versions.

## Human Handoff Requirement

A replacement human should be able to take over by reading repository state without needing previous conversations.

Optimize documentation for current understanding, not historical narration.

If a handoff requires reconstructing old chats, the repository state is incomplete.

## Agent Communication

Agents communicate durable state through repository artifacts: current specs, architecture, active changes, ADRs, code, tests, commits, PRs, reviews, and CI results.

Never assume another agent has access to your conversation history.

## Conflict Priority

When instructions conflict, use this order:

`Human explicit decision → current specs/architecture → relevant ADR → active change → WORKFLOW.md → agent judgment`

Role authority is a permission boundary, not a competing source of truth. If a conflict cannot be resolved within authority, escalate rather than guess.

## Core Principle

Keep the working tree optimized for understanding **what is true now** and **what is changing now**. Let Git preserve what happened before.
