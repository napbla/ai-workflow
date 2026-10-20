# Implement Design → Change → Source Lifecycle

Status: In Progress
Owner: architect

Design: docs/designs/design-change-source-lifecycle/DESIGN.md
Design-Revision: 305121fb9b24bb31c753044a8262b0380882bc71

## Goal

Implement the accepted Design → Change → Source lifecycle as the repository protocol so newly initialized projects can use Design PRs, Design-bound Changes, realization traceability, and final-head folding without relying on chat conventions.

## Constraints

- Keep the protocol vendor-neutral.
- Preserve GitHub branch protection as the authoritative enforcement boundary.
- Do not include CI required-check automation or migration tooling in this Change.
- Treat this as protocol v3 because it introduces a new canonical artifact class and branch/lifecycle semantics.

## Acceptance Criteria

- [ ] Protocol version is 3 in the canonical spec and self-marker.
- [ ] WORKFLOW and generated template define Design, Change, source change, branch semantics, revision binding, realization maps, folding, and final-head review.
- [ ] Work-tracking rules define Design lifecycle, Change lifecycle, per-area realization, INDEX maintenance, and supersession.
- [ ] SPEC declares `docs/designs/` and `docs/designs/INDEX.md` as protocol state and documents v2 → v3 compatibility impact.
- [ ] Human operator guide explains brand-new-project Design PR flow and implementation Change derivation.
- [ ] Architect/implementer/reviewer guidance reflects Design responsibilities and revision binding.
- [ ] Initializer creates `docs/designs/INDEX.md` and the required Design directory for new projects.
- [ ] Initializer tests cover the v3 generated structure and semantics.
- [ ] The accepted lifecycle Design is updated with a realized map for this implementation.
- [ ] Completed Change coordination state is removed before final review.
- [ ] Final reviewed HEAD contains all fold/status/index updates.

## Non-Goals

- GitHub Actions / required CI checks.
- Semantic migration tooling for existing v1/v2 projects.
- Dashboard or consumer implementation.
