# init

Bootstrap a new repository from the canonical protocol in `../spec/`.

This module owns only initialization behavior. It does not define workflow policy.

## Run

From the monorepo root:

```bash
python -m pip install -r init/requirements.txt
python init/init.py --target /path/to/project
```

The initializer prompts for the project name and a comma-separated list of role IDs from `spec/roles.yaml` (default: `architect,implementer,reviewer`), and writes one `.agents/<role-id>.md` per role. See `docs/specs/init-cli.md` for the full CLI contract.

Dogfood this monorepo:

```bash
python init/init.py --self
```

Show the protocol version shipped with this checkout (reads `spec/VERSION`, writes nothing):

```bash
python init/init.py --version
```

## Test

```bash
python -m unittest discover -s init/tests
```
