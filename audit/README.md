# postmo — hold the mess, don't resolve it

An audit is not a narrative. A narrative resolves tension toward a
single coherent story; an audit holds the actual shape of what's been
said — including the parts that don't resolve — and tracks it
accurately as it changes.

Five disciplines, enforced where they're mechanical and explicit
protocol where they need judgment:

1. **Hold contradictions as contradictions.** "I adored her and I'm
   furious at her" stays two live halves — never "X, but Y", never a
   synthesized third thing, never flagged as a problem needing
   resolution.
2. **Track people as time-indexed states, not verdicts.** Tuesday-her
   and Thursday-her are both real. Nobody is "a liar" as a fixed label.
3. **Type every correction: detail vs core-claim.** A fixed date doesn't
   reopen standing claims; a withdrawn accusation is the signal.
4. **Never supply motive the teller didn't state.** "He tackled you
   because he panicked" is invented, even if plausible. Observed
   sequence only — who did what, in what order.
5. **Self-check for softening.** Did "betrayal" become "mistake"? Did a
   restatement tidy the account? Did ambivalence get resolved into one
   "real" feeling? The noticing is part of the deliverable.

No prerequisites. No model, no network — the operator (human or model)
supplies the material; the library enforces the discipline. The
mechanism is the whole product.

*(Lineage: the front-facing conversion of the `forensic-situational-audit`
skill from Ryan's skill-suite, MIT. What changed is documented in
CHANGELOG.md — the name, the "field" language, and prose rules turned
into checked code.)*

## What it does

Two modes:

- **Direct audit (the headline).** "Don't resolve this, just hold it."
  The operator works a messy multi-person situation conversationally;
  the package scans drafts for discipline violations and accumulates
  the audit record. No engine, no interrogation.
- **Overlay.** Attaches to the interrogation engine's Decompose phase
  (disciplines 2–4) and Collide phase (disciplines 1, 5 — the strict
  enforcer: no subordinating conjunctions, no synthesized third thing).
  The overlay never resolves, never synthesizes, never converts a
  direct audit into an interrogation unasked.

The canonical artifact is the **audit record**: which disciplines
fired, held tensions, person-state sequences, typed corrections,
softening and motive flags — structured data with timestamps that the
next session can load and continue from. Machine-readable first
(`record.render()`), renderable conversationally
(`record.render_conversation()`).

## Why it works

Most "holding space" collapses into narrative smoothing — the grammar
does the resolving before anyone notices. The audit attacks that
mechanically:

- **The subordinator scan** rejects "X, but/however/which means Y" in
  held tensions. The "but" demotes one side; the audit refuses to hold
  a tension that's already been resolved in grammar.
- **The motive scan** flags causal attributions with no teller
  attribution ("because he panicked") while passing attributed ones
  ("he said he panicked") and keeping marked guesses marked.
- **The softening scan** compares the teller's words against
  restatements: downgrade wordlist ("betrayal" → "mistake"), dropped
  strong terms, tidy-restatement phrases ("so what you're saying is"),
  ambivalence-resolution phrases ("the real feeling is").
- **The stand-down rule** is schema-level: the record rejects
  synthesis/resolution/verdict sections. An audit that resolves has
  stopped auditing.

What the scans can't do stays explicitly operator protocol — each
discipline's table entry (`disciplines.py`) marks the code/operator
split. A fired check is a finding; a quiet check is not a clean bill
of health.

## Quickstart

Zero dependencies beyond Python 3.10+. Fully offline.

```bash
cd audit
PYTHONPATH=src python3 -m unittest discover -s tests   # 55 offline tests
```

Lint an audit draft:

```bash
PYTHONPATH=src python3 examples/lint_audit.py --text examples/bad-draft.txt \
    --restatement examples/bad-restatement.txt
```

Build a record in code:

```python
from postmo import (
    AuditRecord, HeldTension, PersonState, Correction, scan_text,
)

rec = AuditRecord(case_name="Warehouse shift dispute")
rec.tensions.append(HeldTension(text=(
    "Dana says the pallet was already damaged. "
    "Marco says it was intact.")))
rec.states.append(PersonState(when="2026-09-18", person="Dana",
                              state="calm, cooperative"))
rec.corrections.append(Correction(kind="core-claim",
    text="Marco withdrew the claim that Dana hid the damage."))
rec.log(1, "enforced", "1 tension held as parallel sentences")

report = scan_text("He tackled you because he panicked.")
for flag in report.motive_flags:
    print(flag.severity, ":", flag.sentence)

print(rec.render())              # the machine-readable record
print(rec.render_conversation()) # the human surface

# Next session:
from postmo import parse
rec2 = parse(rec.render())  # everything survives the round trip
```

## Inputs, outputs

- **Input:** situation material (prose), held tensions, person-state
  observations, corrections, restatements to check.
- **Output:** a `ScanReport` (REVIEW items per discipline), and/or a
  rendered `audit-record` Markdown document — complete, timestamped,
  parseable back into the full structured record.

## Worked examples

- `examples/example-1-workplace-dispute.md` — a full direct-audit
  cycle on a neutral workplace dispute, all five disciplines, record
  and conversational surface.
- `examples/example-2-lint-flags.md` — the linter catching a bad
  audit draft, flag by flag.

*Both situations are constructed for teaching — they show the audit's
shape, not real findings.*

## Overlap with evasion_audit (documented, not imported)

Disciplines 1–3 mirror the ground-mapping in `evasion_audit`
(the probe+forge conversion): the subordinator wordlist, the
`HeldTension` / `PersonState` / `Correction` records are intentionally
identical. This package stays standalone and dependency-free, so the
definitions are duplicated rather than imported — the wordlists match
so the two packages can't silently disagree. The evidence taxonomy is
the same 11-tag set all three packages share, vendored here with the
`check_matches_engine()` fork guard.

## FAQ

**Does it need the interrogation engine?** No. Direct audit mode is
standalone and is the headline use. Overlay mode attaches to engine
phases; with no engine running, the overlay reports the record and
stops.

**Does it resolve anything?** Never. That's the stand-down rule, and
it's enforced in code, not just in prose.

**What does it cost?** Nothing. Stdlib only, no model calls, no network.

## License

MIT. See LICENSE.
