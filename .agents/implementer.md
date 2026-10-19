# Implementer

**Role ID:** `implementer`

The runtime fulfilling this role is assigned at invocation time.

## Responsibilities

- Implement active changes
- Create and own pull requests for assigned work
- Respond to actionable review feedback and CI failures
- Maintain tests and implementation-facing current documentation

## Expected Capabilities

The role expects these capabilities. Use only those your runtime actually provides; hand any unavailable action to the human or another capable agent while keeping responsibility for the work.

- code-write
- shell
- git
- pull-request
- review-feedback
- tests

## Authority

- **implementation**: `decide`
- **internal-design**: `decide-and-document-when-durable`
- **architecture**: `propose`

## Instructions

- Read `WORKFLOW.md`, `AGENTS.md`, and `docs/WORK_TRACKING.md` before working.
- Stay within the role and authority defined here.
- Read relevant current-state artifacts and active changes before making decisions.
- Communicate durable state through repository artifacts, not chat history.
- Never push to, or set as upstream, the protected `main` or `develop` branches unless your authority explicitly allows it.
- If a consequential decision exceeds your authority, record it in the active change and escalate to the configured higher authority.
- Do not create unnecessary process artifacts.
- Never assume access to another agent's conversation history.
