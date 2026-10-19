# Generalize Agent Runtime Model

Status: Planned
Owner: claude-code

## Goal

Evolve the workflow from vendor-named agents toward a runtime-neutral role model, and incorporate the lifecycle lessons discovered during the first end-to-end Chat → Work → Implementer → Reviewer → Merge test.

This is expected to become a semantic protocol change and therefore target protocol v2.

## Constraints

- Keep the repository as the canonical transferable project state.
- Keep the protocol vendor-neutral; vendor/runtime-specific enforcement belongs in adapters or runtime configuration.
- Preserve the low-ceremony, current-state-first workflow.
- Do not assume every runtime can push, comment, create PRs, or merge.
- Do not require a specific vendor/model for any core role.
- Protected integration branches such as `main` and `develop` must not be directly updated by implementers.
- Runtime-specific safeguards must complement, not replace, repository-host branch protection.

## Required Behavior

### Role identity and runtime assignment

- Core agent identities are role-oriented rather than vendor-oriented (for example `architect`, `implementer`, `reviewer`).
- A runtime/model/vendor is assigned to a role at invocation time and may change without changing the workflow contract.
- The protocol does not bind ChatGPT, Claude Code, Codex, or any future runtime permanently to a role.
- A role may be fulfilled by different runtimes in different sessions.

### Runtime capability boundaries

- Role responsibility and runtime capability are separate concepts.
- Agents act within the capabilities actually available in their runtime.
- When a required transport/action is unavailable (for example GitHub review publishing returns Forbidden), the workflow falls back to handing off the action or feedback without treating the whole review/change as failed.
- PR ownership means lifecycle responsibility, not guaranteed possession of every GitHub permission.

### Protected branch policy

- Implementers may edit, test, commit, and push working branches when their runtime permits it.
- Implementers must not directly push to protected integration branches such as `main` or `develop`, nor configure those branches as push/upstream targets.
- Vendor-specific enforcement (for example Claude Code `PreToolUse` hooks) belongs outside the core protocol semantics.
- Local Git safeguards and GitHub branch protection/rulesets may enforce the same policy at stronger boundaries.

### Review delivery

- Reviewers must produce actionable review findings.
- Publishing findings as a PR review/comment is preferred when supported.
- If PR write access is unavailable, returning the findings to the invoking human/agent is a valid fallback.
- A GitHub transport failure alone must not invalidate an otherwise completed review.

### Durable current truth

- Completion must ensure durable knowledge is reflected in the most appropriate current truth.
- Do not require every completed behavior change to create/update `docs/specs/` when code, tests, or module documentation are sufficient current truth.
- Use `docs/specs/` for product/system contracts that benefit from explicit specification, not as mandatory duplicate documentation.

### Completion and status

- `docs/status/CURRENT.md` must reflect post-merge reality, not only pre-merge readiness.
- The lifecycle must define how status becomes correct after merge without requiring stale “ready to merge” state to remain on the default branch.
- Active change artifacts remain transient coordination state and are removed when the change is complete.

## Acceptance Criteria

- [ ] Protocol semantics and generated templates use runtime-neutral role identities rather than vendor-name identity as the default model.
- [ ] Runtime assignment to roles is documented as invocation/runtime state, not repository-vendor coupling.
- [ ] Role responsibility is explicitly separated from runtime capabilities and permissions.
- [ ] Implementer/PR ownership wording allows capability-aware handoff for push, PR, review-comment, and merge actions.
- [ ] Protected-branch policy forbids implementers from directly updating or setting upstream to protected integration branches.
- [ ] Reviewer workflow has a documented fallback when PR review/comment publishing is unavailable.
- [ ] Completion rules no longer force every durable behavior change into `docs/specs/`; they require the appropriate current-truth surface instead.
- [ ] Status/completion semantics address post-merge `CURRENT.md` staleness.
- [ ] Claude-specific protected-branch enforcement is implemented as a runtime adapter/hook without making the core protocol Claude-specific.
- [ ] Tests cover the changed initializer/protocol generation behavior and any guard logic that is added.
- [ ] Protocol version is incremented if the final accepted design is breaking under `spec/SPEC.md` compatibility rules.
- [ ] Generated/self-bootstrap project state is updated to conform to the accepted protocol.

## Evidence From v1 End-to-End Test

The first workflow test established that:

- repo-based handoff worked across Chat, Work, Claude Code, and Codex without shared chat history;
- Codex caught committed Python bytecode and weak repository hygiene;
- one Codex runtime could review successfully but failed to publish review feedback because of GitHub API permissions;
- Claude Code could implement locally but GitHub transport permissions were not equivalent to its role responsibility;
- forcing a small local CLI behavior into `docs/specs/` created likely documentation duplication;
- `docs/status/CURRENT.md` became stale immediately after the merge it described as pending.

These are protocol design inputs, not historical requirements to preserve verbatim after the change is complete.

## Open Design Questions

Resolve during design/implementation only if necessary:

- whether role instances should be exactly `architect/implementer/reviewer` or allow named/multiple instances such as `implementer-secondary`;
- how protected branches are declared in project configuration versus defaulted by adapters;
- whether post-merge status refresh is performed by the merger, a follow-up automation, or represented so no post-merge mutation is necessary.
