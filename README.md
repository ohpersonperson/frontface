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

## Ledgers

The six stateless tools (`pressit`, `proofit`, `flashy`, `metacog`,
`fairit`, `postmo`) keep a local append-only ledger of their own runs:
`~/.frontface/<tool>/ledger.jsonl`. One JSON record per run — timestamps,
counts, verdicts, confidence deltas. The ledger never stores your input
text, only a SHA-256 digest of it: what happened and what kind, never
the words. Each tool carries its own copy of the ledger module
(`ledger.py`, vendored — no shared dependency). Opt out any time:

```bash
FRONTFACE_NO_LEDGER=1          # disable recording entirely
FRONTFACE_LEDGER_DIR=/path    # move the ledgers somewhere else
```

`python -m proofit ledger [n]` prints the proofit ledger; for the
library tools, `Ledger("<tool>").summary()` does the same in code.

## What frontface is not (yet)

The eight packages don't talk to each other. There is no shared protocol,
no common record format, no adapter layer, no runtime — each tool is an
island that happens to live in the same repo (the one exception:
`meminqu` reads `memdate` stores, a one-way import, not an interop layer).
If the README ever implies otherwise, that's a bug in the README. Shared
machinery between the tools is roadmap, not reality, and it will be
labeled as such when it exists.

## Test

```bash
for d in ifs metacog flashy memdate meminqu probe-forge audit proofit; do
  PYTHONPATH="$d/src" python -m pytest "$d/tests/" -q
done
```

`meminqu` needs `memdate/src` on the path too — it deliberately imports
memdate's shared core instead of duplicating it:

```bash
PYTHONPATH="meminqu/src:memdate/src" python -m pytest meminqu/tests/ -q
```

419 tests, all green, all offline.

## Note

These are the front-facing conversions of a private skill suite — decoupled
from the original context, renamed in plain language, and carrying no
private material. What's here stands on its own.

## Coming next

I'm working on a webapp/UI for frontface. The goal is to make these tools
easier to explore and use through a practical browser-based interface.
More details coming soon.
