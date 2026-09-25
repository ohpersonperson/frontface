# meminqu — guided capture interviews for a memory store

Seven questions, asked seven different ways, written down exactly as
answered. That is the whole product.

An interview cycle walks each memory domain in order. For each domain,
the interviewer poses 2–4 questions in deliberately different
*registers* — direct, reflective, structural, irreverent, sparse,
temporal, contrastive — receives the answers, and captures them
**verbatim** into that domain's `raw.md`. No synthesis, no
interpretation, no analysis. The registers rotate across the cycle so
no two domains get interrogated from the same angle twice in a row.

No prerequisites. You don't need to know anything about the project's
history. The mechanism is the whole product.

*(Lineage: front-facing conversion of the `meminqu-memory-interrogation`
skill from Ryan's skill-suite, MIT. What changed is documented in
CHANGELOG.md — the decoupling record.)*

## What it does

- **Seven registers** (`registers.py`) — the question stances, kept
  exactly as the skill defined them, each with a description and
  example stems. They are data, so a caller can supply their own set;
  the shipped seven are the complete original set.
- **Cycle planning** (`plan_cycle`) — assigns registers per domain
  deterministically: consecutive domains never share a register set,
  and a full cycle uses every register. No fixed order, no repetition
  rut.
- **Verbatim entry format** (`entry.py`) — one `### Inquiry capture —
  <domain> (registers: …)` record per domain, questions paired with
  answers, answers embedded byte-identical. Skipped questions are
  recorded as skips, not silently dropped.
- **Session runner** (`session.py`) — the record-keeping side of the
  interview: domain walk, skip, explicit reassignment (material that
  belongs elsewhere is captured under the announced domain *unless*
  the operator explicitly reassigns it), and a completion report
  listing which domains got entries and where they landed.

## Why it works

Most "tell me about your week" systems fail in one of two places: they
ask every question the same way (so every answer comes from the same
angle), or they quietly rewrite what you said on the way in (so the
record is the interviewer's summary, not your words). This package
fixes both in code:

- **Register rotation** — `plan_cycle` guarantees angular variety. A
  test asserts consecutive domains differ and a full cycle covers all
  seven registers.
- **Verbatim preservation** — `format_entry` adds structure *around*
  answers but never touches them. The load-bearing test feeds answers
  with contradictions, typos, and markdown through formatting and
  asserts byte-identical survival.
- **Capture purity** — answers go through memdate's `capture()`,
  which raises `InterpretationError` if the text looks like synthesis
  ("in summary…") instead of a raw record. The refusal is the feature:
  it keeps capture and interpretation from mixing in the same motion.

## Installation

`meminqu` is a thin runner over `memdate` — it does
not reimplement capture, config, or storage. Install the dependency
first:

```bash
# from the staging tree
pip install -e ../memdate
pip install -e .
```

or for a quick offline run, put both `src` trees on the path:

```bash
PYTHONPATH=../memdate/src:src python3 -m unittest discover -s tests
PYTHONPATH=../memdate/src:src python3 examples/demo_interview.py
```

`pyproject.toml` declares `memdate` as a dependency honestly —
this package cannot function without it.

## Quickstart

```python
from meminqu import InterviewSession, Response
from memdate import MemoryConfig

config = MemoryConfig(root="./my-memory")  # domains from config, not from here
session = InterviewSession(config)

for domain in session.domains:
    registers = session.start_domain(domain)   # announce; get suggested registers
    # ... the operator/model asks questions, collects answers ...
    session.submit_answers(domain, [
        Response("direct", "What is the key fact?", "The server migration finished Tuesday."),
        Response("sparse", "This domain in one sentence.", "Quiet, for once."),
    ])
    # session.skip_domain(domain)              # or skip it — nothing is written

print(session.render_report())
```

## Where the formats meet

The original skill specified captures under a `## YYYY-MM-DD`
day-heading. The converted memdate writes a `## YYYY-MM-DD
HH:MM TZ` heading per entry instead. This package defers to the
library's heading — one source of truth for the capture format — and
the `### Inquiry capture — <domain> (registers: …)` marker rides
inside the entry body, where the register list stays attached to the
answers it describes.

## Evidence taxonomy

This package tags no evidence itself; its artifacts are `raw.md`
entries. memdate's README maps those onto the shared ten-tier
taxonomy (`raw.md` entries sit at OBSERVATION / CLAIM). No third
taxonomy was invented.

## Worked example

- `examples/example-1-full-cycle.md` — one full annotated cycle on
  neutral domains, register rotation shown.
- `examples/demo_interview.py` — scripted end-to-end run against a
  temp store; no model, no network.
