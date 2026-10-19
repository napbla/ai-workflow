# Fix CURRENT.md Merge-Safe Semantics

Status: Planned
Owner: implementer

## Goal

Prevent `docs/status/CURRENT.md` from becoming stale immediately after a branch or release PR is merged.

The bug exposed by the protocol-v2 release is that `develop` carried statements such as:

- `main` still uses protocol v1;
- v2 is waiting to be released from `develop` to `main`;
- the next step is to merge/release a PR.

Those statements were true before the merge but became false the moment the same file landed on `main`.

## Principle

`CURRENT.md` is current truth, not merge coordination state.

It may describe facts that are true for the checked-out branch, but content intended to merge into another protected branch must already be valid on the target after merge.

Do not put transient lifecycle claims in durable status when they will become false solely because a PR is merged.

Examples of transient claims that belong in the active change or PR instead:

- "PR #N is waiting for merge"
- "main is still on v1"
- "develop is ahead of main"
- "release this branch to main next"
- "review is pending"

Prefer durable statements such as:

- "The project uses protocol v2."
- "main is the stable branch; develop is the integration branch."
- "No active changes are integrated."
- "GitHub branch protection is required for main and develop."

## Required Behavior

1. Update workflow/status guidance so `CURRENT.md` distinguishes durable project truth from transient PR/change coordination.
2. Preserve branch-sensitive status where useful, but forbid target-invalid statements that become stale on merge.
3. Before merging a feature branch into `develop`, its final `CURRENT.md` must be valid on `develop`.
4. Before merging `develop` into `main`, the merged `CURRENT.md` must already be valid on `main`.
5. PR readiness, pending review, pending release, ahead/behind state, and similar transient lifecycle information belongs in the PR or active change rather than durable current status.
6. Fix this repository's current v2 status text so it is valid on both protected branches after synchronization.
7. Keep generated templates/self-bootstrap state consistent with the accepted rule.

## Acceptance Criteria

- [ ] `WORKFLOW.md` explains that `CURRENT.md` must be merge-safe and must not contain merge-invalid transient state.
- [ ] `spec/templates/WORKFLOW.md` carries the same semantics.
- [ ] `docs/WORK_TRACKING.md` and its template give completion guidance that produces target-valid status.
- [ ] No durable status rule requires recording PR readiness or release-pending state in `CURRENT.md`.
- [ ] This repository's final `docs/status/CURRENT.md` contains no stale claim that `main` is still v1 or awaiting the v2 release.
- [ ] The final status can be merged from `develop` to `main` without becoming false merely because the merge happened.
- [ ] No unrelated CI, migration-tool, or feature work is added.

## Scope

This is a small protocol-v2 semantics fix. It does not change the branch model, role model, autonomous review loop, or protocol version.
