# memdate — file-based memory with a hard CAPTURE/DISTILL split

Plain Markdown memory for people or agents. One load-bearing invariant:

**CAPTURE preserves. DISTILL interprets. Never mix them.**

- **CAPTURE** appends timestamped raw records. No summarizing, no
  synthesis, no editing yesterday's entries. Raw is the permanent record.
- **DISTILL** consolidates raw into `distilled.md` — and the library
  checksums raw before and after, voiding the run if anything touched it.
- **INDEX** regenerates the cross-domain connective tissue
  (entities→domains, dependencies, open questions, hot zones) after any
  multi-domain distill. Derived, never authoritative over raw.

No prerequisites. You don't need to know anything about the project's
history. The mechanism is the whole product.

*(Lineage: front-facing conversion of the `memdate-v2` skill from Ryan's
skill-suite, MIT. What changed is documented in CHANGELOG.md — the
decoupling record.)*

## What it does

A memory store is a directory:

```
<root>/
├── INDEX-cross-domain.md     ← regenerated after multi-domain distills
├── DROP/                     ← ingestion: NEW / PROCESSED / PENDING / QUARANTINE
├── personal/
│   ├── raw.md                ← append-only evidence log
│   └── distilled.md          ← derived synthesis + provenance frontmatter
└── work/
    ├── raw.md
    └── distilled.md
```

The domain list is configuration, not identity. This package ships with
neutral defaults (`personal`, `work`, `projects`, `reference`, `misc`) —
define your own via constructor, JSON, or YAML. Storage is a
`StorageAdapter`: the local filesystem by default, Google Drive as an
optional seam you can implement (it fails loudly until you do, instead of
pretending to work).

## Why it works

Most memory systems rot because recording and interpreting happen in the
same motion: you write down what happened *and* what it means, and a
month later you can't tell which was which. The split is enforced in
code, not just in prose:

- **Capture isolation** — `capture()` only appends; it has no code path
  that edits prior entries (tested: old content is always a strict prefix
  of new content). Entry text is scanned for interpretation markers
  ("in summary", "overall,", … — configurable); a hit raises unless you
  pass `force=True`, and then the bypass is stamped into the entry
  header. The exception is visible, never silent.
- **Distill isolation** — `distill()` checksums `raw.md` before writing
  `distilled.md` and re-checks after. If raw changed mid-run, the run is
  void. A test adapter that sabotages raw mid-distill proves the check
  fires.
- **Index discipline** — the four required sections and the 7-step
  regeneration procedure are code. Single-domain distills skip the index
  with a recorded reason. The verify pass asserts no orphan entities and
  no sourceless questions.
- **Raw wins conflicts** — stated in the docs, enforced by the
  architecture: nothing in the distill path can write to raw.

## Quickstart

Zero dependencies beyond Python 3.10+.

```bash
cd memdate
PYTHONPATH=src python3 -m unittest discover -s tests   # 72 offline tests
```

```bash
export PYTHONPATH=src
python3 examples/run_local.py --root /tmp/memo init
python3 examples/run_local.py --root /tmp/memo capture \
    --domain work --text "Acme Corp emailed: contract renews March 1." --source email
python3 examples/run_local.py --root /tmp/memo capture \
    --domain work --text "In summary, the deal is safe."
# InterpretationError: Entry looks like interpretation, not capture —
# markers found: in summary. Rewrite as raw record, or pass force=True
# to record the bypass explicitly.
```

Distill from a file holding your consolidated synthesis:

```bash
python3 examples/run_local.py --root /tmp/memo distill --domain work \
    --file /tmp/work-distilled.md \
    --entities "Acme Corp,Priya" --informs personal \
    --questions "Does the freeze delay the paperwork?"
python3 examples/run_local.py --root /tmp/memo index --touched work,personal
```

Or use it as a library:

```python
from memdate import (
    MemoryConfig, default_adapter, ensure_layout,
    capture, distill, regenerate_index,
)

cfg = MemoryConfig(root="/tmp/memo", domains=("garden", "car"))
store = default_adapter(cfg.root)
ensure_layout(cfg, adapter=store)

capture(cfg, "garden", "Planted tomatoes, north bed.", adapter=store)
distill(cfg, "garden", "North bed: tomatoes planted.",
        entities=["north bed"], lifecycle="ITERATIVE", adapter=store)
```

Drop a file in `DROP/NEW/` with a leading `domain: <name>` line and
`sweep` routes it — captured to the right domain's raw, or quarantined
with a reason file if it's unroutable or reads like synthesis:

```bash
printf 'domain: work\n\nFixed the flaky test.\n' > /tmp/memo/DROP/NEW/note.md
python3 examples/run_local.py --root /tmp/memo sweep
```

## Inputs, outputs

- **Input (capture):** domain, text, optional source. Output: timestamped
  entry appended to `<domain>/raw.md`.
- **Input (distill):** domain, consolidated body, optional entities /
  entity notes / informs / open questions / lifecycle. Output:
  `<domain>/distilled.md` with provenance frontmatter.
- **Input (index):** list of domains the distill touched. Output:
  `INDEX-cross-domain.md`, or a recorded skip for single-domain distills.

## Distilled body conventions

Two line-prefixes the index understands:

- `? ` — uncertainty flag → collected into Hot Zones.
- `! ` — explicit raw↔distilled divergence note → collected into Hot Zones.

Entity note contradictions across domains (work says "reliable", personal
says "misses deadlines") also land in Hot Zones as `[tension]` entries.

## Evidence-taxonomy mapping

This package shares a vocabulary with the `adversarial-ifs` evidence
taxonomy (ten tiers). The mapping is explicit — memdate doesn't tag
evidence itself, but its artifacts sit at defined tiers:

| memdate artifact | IFS tier | Why |
|---|---|---|
| `raw.md` entry (logged event) | `OBSERVATION` | Reported/logged, not independently verified |
| `raw.md` entry (someone's assertion) | `CLAIM` | Explicit assertion by a source |
| `distilled.md` synthesis | `INFERENCE` | Conclusion drawn from raw evidence |
| `distilled.md` `? ` flags, index open questions | `UNKNOWN` | Flagged as not presently determinable |
| distiller-verified fact | `FACT` | Directly established ground truth |
| provisional model in a distillation | `HYPOTHESIS` | Needs stress-testing before use |

No code dependency between the packages — the table is the contract, so
neither taxonomy can silently fork.

## Worked example

`examples/example-1-two-domains.md` — a full CAPTURE → DISTILL → INDEX
cycle on two neutral domains, with the actual file contents shown at
each step.

*The field is constructed for teaching — it shows the mechanism's shape,
not real findings.*

## FAQ

**Where's Google Drive?** The original skill lived in a Drive folder.
This package defaults to the local filesystem; `GoogleDriveAdapter`
documents the seam and raises `DriveNotConfigured` with setup pointers
until you implement it. Drive is an adapter, not the root.

**Can a model do the distilling?** Yes — that's the intended shape. The
model supplies the consolidated body; the library stamps provenance and
enforces that raw wasn't touched. The library never calls a model itself.

**Does capture need the index?** No. Capture works from the first entry;
distill works per-domain; the index appears once two domains are
distilled.

**What about the memory interviewer?** The guided-capture interviewer
(`meminqu`) builds on this library's capture contract — it converts next
and shares this package's domain config.

## License

MIT. See LICENSE.
