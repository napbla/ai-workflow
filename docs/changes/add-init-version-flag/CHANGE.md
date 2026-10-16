# Add Initializer --version Flag

Status: Planned
Owner: claude-code

## Goal

Add a standard `--version` flag to the initializer that reports the protocol version shipped with the current checkout.

## Constraints

- `spec/VERSION` remains the single source of truth.
- Do not introduce a separate initializer/tool version.
- `--version` must exit without prompting for project or agent input.
- Keep the implementation minimal and use standard `argparse` behavior when practical.

## Acceptance Criteria

- [ ] `python init/init.py --version` exits with status 0.
- [ ] Output is `ai-workflow protocol v<version>`, using the value from `spec/VERSION`.
- [ ] Running `--version` creates or modifies no project files.
- [ ] Relevant automated test coverage is added.

## Notes

This is a low-risk CLI feature. No protocol version bump is required because repository protocol semantics are unchanged.
