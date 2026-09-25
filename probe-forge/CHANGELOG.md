# Changelog — fairit

Front-facing conversion of two skill-suite skills, converted as one
unit: `responsibility-obfuscation-probe` v2.0 and `field-forge` v2.0.1
(both MIT). Converted 2026-09-24.

## What the conversion changed

- **One hypothesis library, not two.** The probe's hypothesis protocol
  (H-obfuscation / H-genuine / H-both / insufficient-evidence) and the
  forge's Hammer ran the same protocol in two places. They are now one
  implementation (`hypotheses.py`, `overlay.py`) with two consumers.
- **Renamed everything a stranger couldn't parse.** `field-forge` →
  `fairit`; Anvil → ground mapping, Hammer → evasion-hypothesis
  testing, Furnace → handoff. "Field" → case/material. The v2.0
  de-biasing (hypothesis testing replaces pre-judgment) is preserved
  verbatim in mechanism and now enforced in code.
- **The category-presumption ban moved from prose into code.**
  `CategoryPresumptionError` rejects evidence that only names a category
  ("therapy-speak", "uses corporate speak"). The v1 mandatory-flag
  failure mode is now a regression test, not a paragraph.
- **The discriminating-evidence requirement moved from prose into code.**
  Verdicts without the required evidence raise `HypothesisError`:
  H-obfuscation needs ≥1 favoring item, H-both needs both sides,
  insufficient-evidence must name what would resolve it.
- **The OBFUSCATION gate is one function** (`evidence_tag_for` /
  `supports_obfuscation`): the tag exists only on supported
  H-obfuscation. Suspected-but-untested material stays CLAIM with a
  hypothesis marker — the v2.0 rule, now un-skippable.
- **The stand-down rule is schema-enforced.** The brief renderer rejects
  any collision/adjudication/refinement/surprise section. Seed count
  (2–3) is validated.
- **Held-tension grammar is code-checked.** The subordinating-conjunction
  scan rejects "X, but Y" at the `HeldTension` constructor.
- **Evidence taxonomy reconciled once.** field-forge's 8-tier list
  mapped 1:1 onto the interrogation engine's 11-tag taxonomy; the 3
  unnamed tiers (HYPOTHESIS, REQUIREMENT, DEPENDENCY) documented as
  recognized. `check_matches_engine()` guards against future forks.
- **Jargon protocol generalized.** The original skill knew only
  therapy-speak; the same H-obfuscation/H-genuine/H-both structure now
  ships with three dialect marker lists (therapy, corporate,
  bureaucratic). Markers are tripwires, never verdicts.

## What was kept

- The v2.0 de-biasing in full: no mandatory flagging, no
  "obviously evasive," no verdict-first synthesis, meta-obfuscation as
  candidate (not verdict), the clean "no evasion hypotheses supported"
  finding as a valid output.
- All six execution disciplines (hold contradictions live, time-indexed
  person-states, detail vs core-claim corrections, isolate motive, test
  jargon claims, no softening) — the two codeable ones (subordinator
  scan, correction typing) are code; the rest are documented operator
  discipline, marked as such.
- The forge-brief shape (frontmatter provenance, ground / tested
  hypotheses / handoff sections) as the audit brief.
- The dialog procedure's precision-forcing questions, as operator
  protocol in the examples.
