# fairit — ground mapping and evasion-hypothesis testing

Tests whether evasive-looking communication is actually evading
anything — and if so, what. It never presumes evasion. Three stages:

1. **Ground mapping.** Establish the exact situational state without
   forcing narrative resolution: opposing facts as parallel,
   non-subordinating sentences ("X is true. Y is also true." — never
   "X, but Y"), people as time-indexed states, every correction typed
   as detail vs core-claim.
2. **Evasion-hypothesis testing.** Every candidate evasion — therapy-speak,
   corporate-speak, bureaucratic passive voice, fogging, DARVO,
   projection — becomes competing hypotheses: **H-obfuscation /
   H-genuine / H-both**, tested against discriminating evidence.
3. **Handoff.** 2–3 seed frames plus the audited ground, handed to
   whatever comes next. Then the package stands down.

The one rule everything else serves: **a hypothesis wins only on
discriminating evidence** — observations that would differ between the
hypotheses. Category membership ("this is therapy-speak") is never
evidence. "Insufficient evidence to distinguish" is an honest finding,
not a failure.

No prerequisites. The mechanism is the whole product. No model, no
network — this is pure machinery. The operator (human or model) supplies
the evidence; the library enforces the testing discipline.

*(Lineage: the front-facing conversion of two skills from Ryan's
skill-suite, MIT — `responsibility-obfuscation-probe` and `field-forge`,
converted as one unit because they share one hypothesis-testing core.
What changed in the conversion is documented in CHANGELOG.md.)*

## Quickstart

```python
from fairit import scan_and_test, evidence_tag_for

text = "Mistakes were made in the scoping phase. We're going to circle back."
flags = scan_and_test(text, {
    "mistakes were made": (
        "the passive phrasing names no actor; internal emails name the PM "
        "who cut scoping short — the actor is known",
        "",
    ),
    "circle back": (
        "used to end the paragraph about the miss without giving a new date",
        "",
    ),
})
for flag in flags:
    print(flag.phrase, "->", flag.record.verdict, "->", evidence_tag_for(flag.record))
# mistakes were made -> H-obfuscation -> OBFUSCATION
# circle back -> H-obfuscation -> OBFUSCATION
```

Full cycle demo (ground → probe → brief), no model needed:

```bash
cd probe-forge
PYTHONPATH=src python3 examples/run_cycle.py
```

## What it does

**Ground mapping** (`ground.py`) — the pre-interrogation audit:

- Held tensions must be parallel non-subordinating sentences. The
  subordinating-conjunction scan is in code: "promised a refund, *but*
  none arrived" is rejected; "promised a refund. None arrived." passes.
- People are time-indexed states, never one flat characterization.
- Corrections are typed detail vs core-claim. Core-claim changes — the
  account itself shifting — are the signal, and the library surfaces
  them.

**Hypothesis testing** (`hypotheses.py`) — the shared core:

- Four verdicts: H-obfuscation, H-genuine, H-both, insufficient-evidence.
- Code-enforced rules: H-obfuscation needs ≥1 evidence item favoring it;
  H-both needs evidence on *both* sides; insufficient-evidence must name
  what would resolve the open hypotheses.
- The category-presumption check: evidence that only names a category
  ("therapy-speak", "uses corporate speak") is rejected with
  `CategoryPresumptionError`. This is the old probe's failure mode
  (pre-judging therapy-speak as armor), made impossible in code.

**Probe protocol** (`overlay.py`) — jargon in three dialects (therapy,
corporate, bureaucratic; see `dialects.py`):

- Detection produces *candidates*, never verdicts. A detected phrase with
  no evidence gets insufficient-evidence — the probe refuses to convict
  *or* exonerate on detection alone.
- The evidence tag: **OBFUSCATION** only when H-obfuscation is supported
  by discriminating evidence. Everything else stays **CLAIM** with a
  hypothesis marker. Suspected-but-untested material is never upgraded
  on category membership alone.

**Audit brief** (`brief.py`) — the output artifact with frontmatter
(`artifact:`, `date:`, `protocol:`, `lifecycle:`), Markdown
render/parse, and the stand-down rule enforced in code: the brief must
never contain collision, adjudication, refinement, or surprise sections.
Those belong to the interrogation engine. If the engine isn't running,
the brief is reported and the work stops.

**Evidence taxonomy** (`evidence.py`) — one authoritative mapping.
field-forge shipped an 8-tier list; the interrogation engine uses 11
tags (10 core + overlay-only OBFUSCATION). The forge's 8 map 1:1 onto
the engine's; the 3 the forge never named (HYPOTHESIS, REQUIREMENT,
DEPENDENCY) are documented as recognized. `check_matches_engine()`
guards against silent forks when the sibling package is importable.

## What's honest about the limits

- The library cannot prove a counter-hypothesis is *strong* — the
  evidence-quality judgment stays with the operator. What it makes
  impossible is the failure modes: verdicts without discriminating
  evidence, category-based presumption, silent upgrades to OBFUSCATION,
  subordinated tensions, and the overlay doing the engine's job.
- The dialog procedure (asking for raw input, precision-forcing
  questions) is an operator protocol, documented in the examples — it
  isn't codeable without a model in the loop, and isn't pretended to be.

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

55 offline tests: verdict rules, category-presumption rejection (the v1
regression suite), the OBFUSCATION gate, the subordinator scan,
correction typing, taxonomy reconciliation, brief round-trip and
stand-down, dialect detection, and a full ground→probe→brief cycle.
