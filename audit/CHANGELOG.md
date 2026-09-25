# Changelog — postmo

## 1.0.0 — 2026-09-24 (front-facing conversion)

Converted from the `forensic-situational-audit` skill (v2.0) in Ryan's
skill-suite. Last conversion in the suite besides proofit (on hold
pending a design call).

### Renames
- `forensic-situational-audit` → `postmo` ("forensic" sounds
  like crime scenes to a stranger; the mechanism is holding messy
  situations, not forensics).
- "Field" language → "case"/"situation" throughout.

### Prose → code
- **D1:** subordinating-conjunction scan; `HeldTension` rejects
  subordinating language at construction.
- **D2:** `PersonState` schema (when/person/state, all required);
  verdict-word scan flags permanent-label nouns ("liar", "narcissist" —
  nouns only, adjectives can legitimately describe a moment).
- **D3:** `Correction` kind validation (`detail` | `core-claim`);
  correction-candidate scan surfaces untyped correction-like sentences.
- **D4:** supplied-motive scan — causal/motive attributions without
  attribution markers flagged; attributed motives pass; marked guesses
  kept marked. Includes bare mental-state attributions ("he panicked").
- **D5:** softening scan on original/restatement pairs — downgrade
  wordlist, dropped strong terms, tidy-restatement phrases,
  ambivalence-resolution phrases.
- **Stand-down rule** enforced in code: the record rejects
  synthesis/resolution/verdict sections on render and parse.
- **Full structured audit record**: tensions, person-state sequences,
  corrections, motive flags, softening flags, timestamped discipline
  log, evidence items — render/parse round-trip, plus a conversational
  digest (`render_conversation()`).

### Kept as operator protocol (marked in `disciplines.py`)
- Recognizing that two statements ARE in tension (scans check grammar).
- Typing ambiguous corrections (ask, don't guess).
- Generous-interpretation and evasive-answer detection (D5).
- Final call on flagged motive attributions with unseen context.

### Design decisions
- Ryan's call: **full** structured record (not minimal) — the record
  the next session loads, with timestamps.
- Evidence: no new taxonomy — reuses the shared 11-tag set, vendored
  with the `check_matches_engine()` fork guard (same pattern as
  evasion_audit).
- Overlap with evasion_audit's ground mapping: documented, not
  imported — this package stays standalone and dependency-free, with
  intentionally identical wordlists.
- 55 offline tests. During development the suite caught a real hole:
  the forbidden-stem `"resolv"` did not match `"resolution"`, so a
  `## Resolution` section would have passed the stand-down check.
  Fixed to `"resolut"`.

### Lossy in translation
- The phrase-list checks are tripwires, not proof — stated in the
  module docstring and the README, not buried.
- "Yet" as a temporal adverb ("not yet delivered") will trip the
  subordinator scan; the operator dismisses it. Documented as a known
  false-positive shape.
- The conversational digest is a structured-to-readable transform, not
  a real conversation — the operator's actual replies stay with the
  operator.
