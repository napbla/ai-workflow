# AI Workflow Protocol

This directory defines the canonical repository protocol used by the `ai-workflow` ecosystem.

## Ownership

`spec/` owns:

- protocol version
- generated repository structure
- workflow semantics
- default roles
- generated templates

Tools consume the protocol. They must not redefine it independently.

## Project Marker

A compliant project declares its protocol version in:

```yaml
# .ai-workflow.yml
protocol: 1
```

## Required Project State

```text
.ai-workflow.yml
WORKFLOW.md
AGENTS.md
.agents/

docs/
  WORK_TRACKING.md
  architecture/
  specs/
  adr/
  changes/
  status/CURRENT.md
```

Semantics:

- `specs/` — current product/system behavior
- `architecture/` — current technical truth and contracts
- `adr/` — durable rationale that future operators/agents still need
- `changes/` — active coordination state only
- `status/CURRENT.md` — current operator-facing snapshot
- Git — historical record

Completed change artifacts are removed after durable truth is folded into current-state artifacts.

## Compatibility

Protocol changes are explicit and versioned. A structural or semantic breaking change increments the protocol version.

`init/` creates projects at the protocol version shipped with the checkout.
`migrate/` may later transform existing repositories to a target protocol semantically.
`check/` may later validate conformance.

## Design Principle

Keep the protocol small, current-state-first, vendor-neutral, and optimized for one human operator coordinating multiple AI agents. Human involvement is driven by risk, uncertainty, and authority rather than fixed ceremony.
