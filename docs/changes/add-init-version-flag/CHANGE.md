# Add Initializer --version Flag

Status: Verifying
Owner: claude-code

## Goal

Add a standard `--version` flag to the initializer that reports the protocol version shipped with the current checkout.

## Constraints

- `spec/VERSION` remains the single source of truth.
- Do not introduce a separate initializer/tool version.
- `--version` must exit without prompting for project or agent input.
- Keep the implementation minimal and use standard `argparse` behavior when practical.

## Acceptance Criteria

- [x] `python init/init.py --version` exits with status 0.
- [x] Output is `ai-workflow protocol v<version>`, using the value from `spec/VERSION`.
- [x] Running `--version` creates or modifies no project files.
- [x] Relevant automated test coverage is added.

## Notes

This is a low-risk CLI feature. No protocol version bump is required because repository protocol semantics are unchanged.

Implemented as a small custom `argparse` action rather than `action="version"` so `spec/VERSION` is read only when `--version` is passed; a missing file still fails with the existing `Failed to load protocol` message (exit 2) instead of a traceback on every invocation. Tests: `python -m unittest discover -s init/tests`.

Before merge: remove this directory (behavior is documented in `init/README.md` and covered by `init/tests/`).
