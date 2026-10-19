# AI Workflow

Core monorepo for a lightweight, vendor-neutral operating model for **one human operator working with multiple AI agents**.

The repository protocol is the shared contract. Core tools remain separate modules and communicate through that contract rather than private integration state.

## Modules

```text
spec/       canonical protocol, roles, templates, version
init/       bootstrap new repositories
migrate/    semantic migration module (planned)
check/      validation module (GitHub branch protection check; protocol validation planned)
```

Consumers such as dashboards or agent runners should live in separate repositories and consume the protocol rather than becoming part of core.

## Dependency Direction

```text
              spec
            /  |  \
         init migrate check
```

`init`, `migrate`, and `check` may depend on `spec`. They should not depend on one another's internals.

## Principles

- current-state-first
- Git-backed history
- one canonical repository state
- low ceremony
- human involvement by risk/uncertainty/authority
- vendor-neutral roles
- small composable tools
- protocol changes are explicit and versioned

## Bootstrap a Project

```bash
python -m pip install -r init/requirements.txt
python init/init.py --target /path/to/repository
```

The initializer asks for the project name and the role IDs to configure (default: `architect`, `implementer`, `reviewer`). The generated project declares the protocol version in `.ai-workflow.yml`.

## Test

```bash
python -m unittest discover -s init/tests
python -m unittest discover -s check/tests
```

## Dogfood This Monorepo

```bash
python init/init.py --self
```

See `HUMAN_SETUP.md` for the human operating flow and `spec/SPEC.md` for the protocol contract.
