# init

Bootstrap a new repository from the canonical protocol in `../spec/`.

This module owns only initialization behavior. It does not define workflow policy.

## Run

From the monorepo root:

```bash
python -m pip install -r init/requirements.txt
python init/init.py --target /path/to/project
```

Dogfood this monorepo:

```bash
python init/init.py --self
```
