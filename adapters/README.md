# adapters

Runtime-specific enforcement of policies defined by the protocol in `../spec/`.

The protocol stays runtime-neutral; an adapter maps one policy onto one runtime's extension mechanism. Adapters must not redefine policy.

| Adapter | Runtime | Enforces |
| --- | --- | --- |
| `claude-code/` | Claude Code | Protected branch policy (PreToolUse Bash hook) |
