# AI Workflow Protocol

This directory defines the canonical repository protocol used by the `ai-workflow` ecosystem.

## Ownership

`spec/` owns:

- protocol version
- generated repository structure
- workflow semantics
- default roles
- branch model and protected branch policy
- generated templates

Tools consume the protocol. They must not redefine it independently.

## Project Marker

A compliant project declares its protocol version in:

```yaml
# .ai-workflow.yml
protocol: 2
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

Completed change artifacts are removed after durable knowledge is folded into the most appropriate current-truth surface (code, tests, module docs, specs, architecture, or ADRs).

## Roles and Runtimes

`.agents/<role-id>.md` describes each configured role. Agent identity is the role ID, named at invocation; the runtime (model, vendor, or tool) fulfilling a role is invocation state and is never recorded in the project. Default roles are defined in `roles.yaml`.

## Branch Model

- `main` — stable, releasable truth; updated through a reviewed PR from `develop`.
- `develop` — reviewed integration truth; feature branches start from and merge back into it through PR review.
- `feature/<change-id>` — one active change, including its `CHANGE.md` and branch-local status.

`main` and `develop` are protected: implementers never push to them or set them as upstream/push targets. `docs/status/CURRENT.md` is branch-sensitive and must be correct for the target branch when a branch is merged. `WORKFLOW.md` holds the full lifecycle, including autonomous change execution up to `ready-for-human-merge`.

Enforcement is layered: repository-host branch protection is authoritative; runtime adapters (see `../adapters/`) and optional local Git hooks are complementary.

## Compatibility

Protocol changes are explicit and versioned. A structural or semantic breaking change increments the protocol version.

### v1 → v2

v2 is a semantic and structural change:

- `.agents/<agent-id>.md` files named after vendors/runtimes become `.agents/<role-id>.md`, and `AGENTS.md` lists roles rather than runtimes.
- The `main` / `develop` / feature branch model and protected branch policy apply; active changes live only on feature branches.
- Completion folds knowledge into the most appropriate current-truth surface instead of always `docs/specs/`.

To migrate manually until `migrate/` exists: regenerate `WORKFLOW.md`, `AGENTS.md`, `.agents/`, and `docs/WORK_TRACKING.md` with `init/`, remove vendor-named agent files, set `protocol: 2`, create `develop` from `main`, and protect both branches on the repository host.

`init/` creates projects at the protocol version shipped with the checkout.
`migrate/` may later transform existing repositories to a target protocol semantically.
`check/` may later validate conformance.

## Design Principle

Keep the protocol small, current-state-first, vendor-neutral, and optimized for one human operator coordinating multiple AI agents. Human involvement is driven by risk, uncertainty, and authority rather than fixed ceremony.
