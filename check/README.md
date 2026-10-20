# check

Deterministic validation against the canonical protocol in `../spec/`.

Semantic product/design judgment belongs to agents or humans. The check module validates only properties that can be determined mechanically.

## Protocol validator

`protocol.py` validates a target repository against the protocol version shipped by the current ai-workflow checkout.

```bash
python check/protocol.py
python check/protocol.py --target /path/to/repository
```

The default target is the current working directory.

For protocol v3 it validates:

- required protocol files/directories;
- `.ai-workflow.yml` marker against `spec/VERSION`;
- the protocol version declared by `WORKFLOW.md`;
- Design status values;
- instance-level Realization Maps for `Implementing` / `Realized` Designs;
- that `Realized` mappings match current repository paths;
- that a `Realized` Design has no remaining `Target` mappings;
- `docs/designs/INDEX.md` as the exact projection of realized source `Areas`;
- duplicate exact realized source-area ownership across Designs;
- Design-derived active Changes reference an existing Design and include a commit-like `Design-Revision`.

Exit codes:

| Exit | Meaning |
| --- | --- |
| `0` | Target satisfies all implemented deterministic checks |
| `1` | Protocol violations found |
| `2` | Validator could not read/validate the target (for example invalid target path or I/O failure) |

The validator intentionally does **not** judge Design quality, verify that a Design revision was actually accepted/merged, prove Git commit reachability, infer semantic supersession, mutate the target, or migrate older protocol versions.

## GitHub branch protection

`branch_protection.py` answers one question: are `main` and `develop` protected on GitHub as the protocol requires? It only reads repository-host state through the GitHub REST API. It never changes settings and never inspects local commands. GitHub branch protection and rulesets are the enforcement boundary; this tool verifies them.

```bash
GH_TOKEN=... python check/branch_protection.py
python check/branch_protection.py --repo OWNER/NAME
python check/branch_protection.py --api-url https://ghe.example/api/v3
```

Each branch counts as protected when active rulesets and/or classic branch protection together:

- require a pull request;
- block force pushes;
- block deletion;
- cannot be bypassed by the checking credential.

Run the check with the same credential the agent runtime uses. The token is read from `GH_TOKEN` or `GITHUB_TOKEN`, is never printed, and must never be committed.

| Exit | Meaning | Action |
| --- | --- | --- |
| `0` | Both branches protected for the checking credential | Continue normal autonomous execution |
| `1` | At least one branch is missing or not fully protected | Human setup blocker: configure protection |
| `2` | Protection could not be verified | Human setup blocker: fix access and re-run |

Limitations: bypass is evaluated only for the checking credential, repository-level push restrictions are not evaluated, and this checker does **not yet verify required status checks**. For the ai-workflow repository, GitHub protection separately requires the Actions check named `core-tests` on both `main` and `develop`.

## Tests

```bash
python -m unittest discover -s check/tests
```
