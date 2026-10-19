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

Without `--version`, the initializer prompts interactively for the project name and agents, then writes the protocol files into the target.

## `--version`

- Prints `ai-workflow protocol v<version>` to stdout, where `<version>` is the trimmed content of `spec/VERSION`, and exits with status 0.
- `spec/VERSION` is the only version source; the initializer has no separate tool version.
- Exits before initialization: it does not prompt and does not create or modify any files, including a `--target` directory.
- If `spec/VERSION` cannot be read, prints `Failed to load protocol: <error>` to stderr and exits with status 2.

Coverage: `init/tests/test_init.py`.
