# Human Operator Guide

This workflow is designed for **one human operator working with multiple AI agents**. Another human should be able to replace the operator by reading the repository, without needing prior conversations.

## 1. One-time setup

1. Create a Git repository and push it to your repository host.
2. Run `python init/init.py --target <repo>` from the `ai-workflow` checkout and choose the roles you need.
3. Commit `.ai-workflow.yml`, `WORKFLOW.md`, `AGENTS.md`, `.agents/`, and `docs/` on `main`.
4. Create `develop` from `main` and push it.
5. Protect `main` and `develop` on the repository host (branch protection or rulesets): require a pull request, block force pushes and deletion. This is the authoritative enforcement of the protected branch policy; ai-workflow does not try to reproduce it locally. Do not give agent credentials bypass permission.
6. Verify the protection: with the agent runtime's token in `GH_TOKEN` (or `GITHUB_TOKEN`), run `python <ai-workflow>/check/branch_protection.py` from the project checkout, or pass `--repo OWNER/NAME`. Exit 0 means both branches are protected against that credential; any other result is a setup blocker to fix (see `check/README.md`).
7. Connect repository access to the AI runtimes you use when available.
8. Treat the repository as canonical project state.

### Runtime credentials

To let an implementer runtime push its feature branch and open PRs without you, give it a credential scoped to the one repository with only the permissions it needs (for GitHub, a fine-grained token with Contents and Pull requests read/write, plus Administration read-only so it can run the protection check) and a short expiry. Keep it outside the repository, rely on step 5 to stop it from updating `main` or `develop`, and revoke it when no longer needed.

### Invoking an agent

Name the role, not the vendor, when you invoke an agent, for example: `You are the implementer. Sync the repository and work on feature/<change-id>.` Any runtime can fulfill any role; which one you pick is a per-session choice and is not recorded in the repository.

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
Architect creates feature/<id> from develop
with docs/changes/<id>/CHANGE.md
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
Human merges into develop
      ↓
Reviewed PR develop → main when releasing
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
Implementer pushes feature branch, opens/owns PR targeting develop
        ↓
Reviewer / CI / Human leaves actionable feedback
        ↓
Implementer fixes on same PR
        ↓
CI + re-review
        ↓
ready-for-human-merge
        ↓
Human merges
```

After you finalize a change's intent, this loop should run without you until the PR is `ready-for-human-merge`. You are pulled in only for ambiguity, consequential decisions, authority limits, or blocked credentials/infrastructure.

Your PR comments re-enter the same loop when they refine the accepted change. If your feedback changes the intent, acceptance criteria, architecture, or scope, expect the agent to close the PR and start a new change instead of rewriting the old one.

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

Status holds durable current truth only. Look in the PR or the active change for PR readiness, pending review, or a pending release; these are deliberately kept out of `CURRENT.md` so that merging never makes it stale.

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

## 11. Cost-conscious flow

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

