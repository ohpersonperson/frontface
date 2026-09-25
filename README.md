# frontface

Eight small, offline, stdlib-only Python packages. No frameworks, no network,
no build step. Each one does one job.

| Package | Does what |
|---|---|
| `pressit` | Pressure-tests a claim, decision, or contradiction until what's load-bearing is left standing. |
| `metacog` | Audits confidence — checks whether the certainty attached to a claim is earned. |
| `flashy` | Finishing discipline for multi-step work: checkpoints, quality gates, no dropped threads. |
| `memdate` | File-based memory with a hard capture/distill split. You define your own directory and domains. |
| `meminqu` | Inquires against a memdate memory store — structured interviews of what you recorded. |
| `fairit` | Fairs things up: catches responsibility-obfuscation and evasion in how something is said. |
| `postmo` | Postmortem discipline: holds a messy multi-person situation without resolving it prematurely. |
| `proofit` | Fail-closed linter for AI-generated claims. Prove it or flag it. |

## Layout

Each package is self-contained: `src/`, `tests/`, `examples/`, `README.md`,
`CHANGELOG.md`, `pyproject.toml`, `LICENSE` (MIT).

## Test

```bash
for d in pressit metacog flashy memdate meminqu fairit postmo proofit; do
  PYTHONPATH="$d/src" python -m pytest "$d/tests/" -q
done
```

`meminqu` needs `memdate/src` on the path too — it deliberately imports
memdate's shared core instead of duplicating it:

```bash
PYTHONPATH="meminqu/src:memdate/src" python -m pytest meminqu/tests/ -q
```

404 tests, all green, all offline.

## Note

These are the front-facing conversions of a private skill suite — decoupled
from the original context, renamed in plain language, and carrying no
private material. What's here stands on its own.

## Coming next

I'm working on a webapp/UI for frontface. The goal is to make these tools
easier to explore and use through a practical browser-based interface.
More details coming soon.
