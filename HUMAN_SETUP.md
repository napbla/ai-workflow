# Human Operator Guide

This workflow is designed for **one human operator working with multiple AI agents**. Another human should be able to replace the operator by reading the repository, without needing prior conversations.

## 1. One-time setup

1. Create a Git repository and push it to your repository host.
2. Run `python init/init.py --target <repo>` from the `ai-workflow` checkout.
3. Commit `WORKFLOW.md`, `AGENTS.md`, `.agents/`, and `docs/`.
4. Connect repository access to the AI surfaces you use when available.
5. Treat the repository as canonical project state.

## 2. Use Chat for thinking

Use normal Chat for:

- brainstorming
- requirements clarification
- trade-off discussion
- feature exploration
- small focused questions

Exploration does not need to be tracked until it produces committed work, durable constraints, or follow-up that must survive the conversation.

## 3. Use Work for substantial execution

Use Work when the task benefits from:

- broad repository inspection
- many files or artifacts
- multi-step research and synthesis
- substantial architecture/spec updates
- repo-wide review

Default to Chat for thinking; use Work when agentic execution adds value.

## 4. Refresh repository context

When current project state matters, say:

```text
sync repo
```

This convention means: refresh relevant repository state and continue from it rather than remembered conversation context.

For focused work:

```text
sync repo, then review docs/changes/<change-id>/CHANGE.md
```

## 5. Start a change only when work is committed

Typical flow:

```text
Chat exploration
      ↓
Human decides to pursue it
      ↓
docs/changes/<id>/CHANGE.md
      ↓
Agent implementation
      ↓
PR / review / CI
      ↓
Verify acceptance criteria
      ↓
Update current specs / architecture / ADR if needed
      ↓
Delete active change artifact
      ↓
Merge
```

A small low-risk fix may go directly to code + regression test when no persistent coordination context is needed.

## 6. Human involvement is exception-driven

The human operator should spend attention on:

- priorities
- ambiguous product intent
- decisions outside an agent's authority
- high-risk or consequential trade-offs
- unresolved conflicts
- final judgment where automation is not trusted enough

Do not add a human approval step merely because the workflow says so. Agent authority can increase over time without changing the workflow model; a future bounded workflow may assign final authority to agents instead of a human.

## 7. PR loop

For implementation work:

```text
Implementer opens/owns PR
        ↓
Reviewer / Human leaves actionable feedback
        ↓
Implementer fixes on same PR
        ↓
CI + re-review
        ↓
Merge
```

If an implementation agent can watch its own PR and react to reviews or CI, use that runtime feature. The shared workflow remains vendor-neutral.

PR comments are coordination, not canonical long-term state. Before merge, durable outcomes must appear in code, tests, specs, architecture, ADRs, or the active change.

## 8. Bugs

During an active change, fix an in-scope bug in the same change and add a regression test when appropriate.

After merge:

- tiny local bug → direct fix + regression test may be enough
- non-trivial or multi-session bug → create a new active change

Do not create artifacts merely for bookkeeping.

## 9. Operator dashboard

Use `docs/status/CURRENT.md` as the current handoff/dashboard view.

A useful request is:

```text
sync repo and update project status
```

The dashboard should emphasize:

- current objective
- active changes
- human attention needed
- blockers/risks
- next actions

Do not maintain status history manually by default; Git preserves prior versions.

## 10. Human replacement test

A replacement operator should be able to enter the project and read:

```text
README / project docs
WORKFLOW.md
AGENTS.md
docs/status/CURRENT.md
docs/changes/
docs/specs/
docs/architecture/
relevant ADRs
```

and answer:

- What is true now?
- What is changing now?
- What needs human attention?
- What should happen next?

If they need old chat logs to continue, repository state is incomplete.

## 11. Cost-conscious ChatGPT flow

```text
Need to think/discuss?          → Chat
Need fresh repo context?        → Chat + sync repo
Need substantial multi-step work? → Work
Need implementation?           → Coding agent
Need independent verification? → Reviewer agent
Need durable memory?           → Repository
```

Use the lightest surface that can complete the task reliably.

## Keep supporting tools separate

Treat the repository conventions as the integration contract. Core protocol tools (`spec`, `init`, `migrate`, `check`) live as independent modules in the `ai-workflow` monorepo. Consumer products such as dashboards or agent runners should remain separate repositories, read the same protocol, and must not own a second canonical project datastore.

