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

## Protocol v3

v3 separates project evolution into:

```text
Design → one or more Changes → source changes
```

- Designs describe accepted target/conceptual state.
- Changes describe coherent transformations.
- Source changes implement Changes.
- Realization Maps + `docs/designs/INDEX.md` let agents find which Design explains current code without rereading the whole repository.

See `spec/SPEC.md` and `WORKFLOW.md` for the contract.

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
- explicit versioned protocol semantics

## Bootstrap a Project

```bash
python -m pip install -r init/requirements.txt
python init/init.py --target /path/to/repository
```

The initializer creates the v3 repository contract including `docs/designs/INDEX.md`, then asks for project name and configured role IDs.

A brand-new project should create and accept its initial Design before implementation begins.

## Test

```bash
python -m unittest discover -s init/tests
python -m unittest discover -s check/tests
```

## Dogfood This Monorepo

```bash
python init/init.py --self
```

See `HUMAN_SETUP.md` for the human operating flow.
