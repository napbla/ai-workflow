# check

Deterministic validation of a repository against the canonical protocol in `../spec/`.

Semantic project judgment belongs to agents or migration logic, not this module.

## GitHub branch protection

`branch_protection.py` answers one question: are `main` and `develop` protected on GitHub as the protocol requires? It only reads repository-host state through the GitHub REST API. It never changes settings and never inspects local commands. GitHub branch protection and rulesets are the enforcement boundary; this tool verifies them.

```bash
GH_TOKEN=... python check/branch_protection.py               # repo derived from the `origin` remote
python check/branch_protection.py --repo OWNER/NAME          # explicit repository
python check/branch_protection.py --api-url https://ghe.example/api/v3
```

Each branch counts as protected when active rulesets and/or classic branch protection together:

- require a pull request;
- block force pushes;
- block deletion;
- cannot be bypassed by the checking credential:
  - A ruleset counts only when its `current_user_can_bypass` is `never` or `pull_requests_only`. A ruleset showing `always` or `exempt` is ignored. One that is unreadable or shows an unknown value makes the result unverifiable.
  - Classic protection counts only with "Do not allow bypassing the above settings" (`enforce_admins`) enabled. Its PR requirement counts only when no user, team, or app is allowed to bypass required pull requests.

Run the check with the same credential the agent runtime uses, so the bypass evaluation applies to that credential. The token is read from `GH_TOKEN` or `GITHUB_TOKEN`. It is never printed and must never be committed. A fine-grained token needs Administration read-only to read classic protection.

| Exit | Meaning | Action |
| --- | --- | --- |
| `0` | Both branches protected for the checking credential | Continue normal autonomous execution |
| `1` | At least one branch is missing or not fully protected | Human setup blocker: configure protection |
| `2` | Protection could not be verified (no credential, insufficient permission, unknown bypass status, API failure, repository not found or not accessible) | Human setup blocker: fix access and re-run |

On exit `1` or `2` the output names the missing requirements and the remediation steps. Agents record it under Human Attention in `docs/status/CURRENT.md` and must not claim the branches are protected.

Limitations: bypass is evaluated only for the checking credential, and repository-level push restrictions are not evaluated. The tool reports what GitHub says; it does not prevent local mistakes.

Tests: `python -m unittest discover -s check/tests`.

## Planned

Protocol marker/version checks, required-path checks, and other machine-checkable structural invariants.
