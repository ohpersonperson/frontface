# Frontface browser demos

The two Pyodide demos, copied verbatim into the repo on 2026-11-10 so the
repo and the demo stop living in different places:

- `index.html` — pressit: interrogate a claim in the browser. Canned
  pre-scan needs no key; the full interrogation needs the visitor's own
  OpenRouter key and model id.
- `proofit/index.html` — proofit: lint a runbook in the browser. Needs
  no key; nothing leaves the page.

Both run fully client-side via Pyodide and install the pinned package
from PyPI in the browser (`pressit==1.2.0`,
`frontface-proofit==1.2.0`).

## Live hosts

- https://frontface-five.vercel.app/ (pressit; proofit at `/proofit/`)
- https://ohpersonperson.github.io/frontface/ (mirror; proofit at `/proofit/`)

Both returned 200 on 2026-11-10.

## Deployment

Deployment config is still Ryan's step: there is no Vercel config or
GitHub Pages workflow in this repo yet, and nothing in this directory
has been deployed by copying it here. The live hosts above are served
from the copies that predate this move; pointing them at this directory
is a separate decision for Ryan.
