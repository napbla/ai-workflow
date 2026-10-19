# ai-workflow — Current Project State

Updated: 2026-10-19

## Current Objective

Evolve the workflow toward protocol v2 by separating role identity from AI runtime/vendor, making permissions capability-aware, and incorporating lifecycle findings from the first end-to-end workflow test.

## Active Changes

- `docs/changes/generalize-agent-runtime-model/CHANGE.md` — Planned, owned by `claude-code`.

## Human Attention

- Design decisions are only needed if implementation reaches the open questions recorded in the active change.

## Blockers / Risks

- This is a semantic protocol change; generated/self-bootstrap state must remain internally consistent.
- Runtime-specific enforcement must not leak vendor assumptions into the core protocol.

## Next

- Implementer reads the active change, proposes/implements the smallest coherent protocol-v2 design, and keeps runtime-specific safeguards modular.
- Verify generated project state and self-bootstrap behavior before merge.

## Current Truth References

- Specs: `docs/specs/`
- Architecture: `docs/architecture/`
- Active changes: `docs/changes/`
- Durable decisions: `docs/adr/`
