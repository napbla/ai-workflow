# Initializer CLI

Current behavior of `init/init.py`, the command that bootstraps a repository at the protocol version shipped with the checkout.

## Options

| Option | Behavior |
| --- | --- |
| `--version` | Print the protocol version and exit (see below). |
| `--target PATH` | Initialize `PATH` (default: current directory). Mutually exclusive with `--self`. |
| `--self` | Initialize the ai-workflow monorepo itself. |
| `--roles PATH` | Role configuration YAML (default: `spec/roles.yaml`). |
| `--conflict ask\|skip\|overwrite\|abort` | How to handle existing generated files (default: `ask`). |

Without `--version`, the initializer prompts interactively, then writes the protocol files into the target.

## Prompts

1. **Project name** — default: the target directory name, or `ai-workflow` with `--self`.
2. **Roles to configure** — comma-separated role IDs from the roles file; default `architect,implementer,reviewer` (those present in the roles file, otherwise all roles). Unknown IDs are reported and the prompt repeats; duplicates are ignored.

Each selected role produces `.agents/<role-id>.md`, and `AGENTS.md` lists the roles. Role IDs must match `[a-z0-9][a-z0-9-]*`; a roles file with other keys fails with `Failed to load protocol` (exit 2). No runtime or vendor names are written.

## `--version`

- Prints `ai-workflow protocol v<version>` to stdout, where `<version>` is the trimmed content of `spec/VERSION`, and exits with status 0.
- `spec/VERSION` is the only version source; the initializer has no separate tool version.
- Exits before initialization: it does not prompt and does not create or modify any files, including a `--target` directory.
- If `spec/VERSION` cannot be read, prints `Failed to load protocol: <error>` to stderr and exits with status 2.

Coverage: `init/tests/test_init.py`, including a check that this repository's generated files (`WORKFLOW.md`, `AGENTS.md`, `.agents/`, `docs/WORK_TRACKING.md`, `.ai-workflow.yml`) match the initializer output.
