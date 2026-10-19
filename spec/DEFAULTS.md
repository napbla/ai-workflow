# Default Roles

Built-in role definitions live in `roles.yaml`. This file is a human-readable summary; YAML is canonical.

Role keys are the agent identities used in projects (`.agents/<role-id>.md`). Any runtime may fulfill a role; the assignment is made at invocation time. A role's `capabilities` are what the role expects, not permissions the runtime is guaranteed to have.

## Architect

Maintains current architecture/specifications, clarifies contracts and consequential trade-offs, and may maintain operator-facing status.

## Implementer

Implements active changes, owns PRs, handles review/CI feedback, and maintains tests plus implementation-facing current documentation.

## Reviewer

Reviews active work against current truth, leaves actionable feedback, detects regressions/contract violations, and identifies test gaps.

## Researcher

Researches technical/product questions and records only findings that need to survive the session.

## Generalist

Combines research, specification maintenance, implementation, PR ownership, review, testing, and project-state reporting.
