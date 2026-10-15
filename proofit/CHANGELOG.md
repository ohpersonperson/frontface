# CHANGELOG

## Unreleased

The 1337 module lands as proofit rules R11–R14 (new `src/proofit/leet.py`,
wired into the lint run): R11 cross-role duplication detection, R12 header
date check, R13 suspicious-character-count namesake (the eight-length canon:
93, 222, 555, 840, 1001, 1111, 1217, 1337), R14 missing-file verification.
R11/R12/R14 are fail-closed ERROR; R13 is heuristic WARNING per the
PARAM-PROOFIT-001 severity doctrine. Fixture: the actual 1,337-char poisoned
brief from 2026-10-09, firing all four rules (`tests/test_1337.py`, 27 new
tests). The staff brief gate (`staff/langchain/leet.py`) is untouched.

## 1.0.0 — 2026-09-24

Front-facing conversion of the `proofit` skill (skill-suite) into a
standalone Python package. The skill was prose-only: ten rules for locking
down workflows into unbreakable, zero-assumption runbooks. The conversion
turns the rules into a fail-closed linter.

What changed from the skill:

- The ten prose rules became a rule catalog with per-rule implementation
  status: 7 full mechanical checks (R2, R3, R4, R6, R7, R9, R10), 2 narrow
  heuristics (R1, R8), 1 convention check (R5, glossary format only).
- The skill's Output Format section became the input contract: the linter
  parses runbook-shaped Markdown rather than inventing a new format.
- Added the fail-closed gate the prose implied but couldn't enforce: any
  violation rejects the draft (exit 1); clean drafts pass (exit 0).
- The generator option was vetted and deliberately not built — it was a
  static template with a CLI wrapper that enforced nothing. The template
  ships as `templates/runbook-template.md` instead.
- Wording generalized from "free-tier multi-model workflows" to runbooks
  in general; the routing section applies whenever work routes across
  multiple services. No Ryan-specific content existed to remove.

Design calls made during conversion (all Ryan's):

- Linter over generator (evidence: the generator enforces nothing).
- Fail-closed over advisory/mixed (the spirit of "idiot-proof").
- Wizard deferred: linter + static template covers the value; the linter's
  checks are the engine a wizard would use later anyway.

Known limits (also in README):

- Shape, not truth: the linter cannot verify a rate limit is correct or a
  recovery path works.
- Rules 1 and 8 are tripwires with documented false-positive behavior.
- Rule 5 cannot detect undefined jargon without a glossary; that judgment
  is explicitly out of scope.
