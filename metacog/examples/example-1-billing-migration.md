# Worked Example: Should Northwind migrate billing to the new provider?

A complete collision record for a business decision — the kind of call a
stranger can follow end to end. This is a constructed teaching example;
the findings are illustrative, not real.

---
artifact: collision-record
date: 2026-09-24
protocol: metacog/1.0
lifecycle: INITIAL
---

# Collision Record

Trigger thresholds tripped: stakes, contradiction-present

The migration is a hard-to-reverse vendor change (stakes), and the
finance lead has an uncollided counter-take: churn improved on support
staffing, not billing (contradiction-present).

## Countermodel

Strength: strong

The strongest opposing case has three premises. Premise one: the migration
cost is not the headline number — the data shows that the last three
provider migrations in this industry overran by 2.4x on average, because
contract penalties and dual-running fees were excluded from the business
case. Premise two: the churn argument reverses under measurement. The
evidence from the Q1 cohort shows churn fell only after support response
times improved, not after the billing change, so the mechanism attributed
to billing is actually support staffing. Premise three: the new provider's
uptime record is worse, not better — three documented outages in the last
twelve months versus one on the current contract. Therefore the conclusion
rests on underestimated cost, misattributed churn improvement, and a
weaker reliability premise, and migration now is the wrong call.

## Load-Bearing Assumptions

- [load-bearing] Migration cost stays under $40k
  - collision: weakened
  - attack: Three comparable migrations overran by 2.4x on dual-running fees and contract penalties excluded from the business case.
- [load-bearing] Churn drops below 4% as a result of the migration
  - collision: survives
  - attack: The Q1 cohort shows churn falling on support improvements, not billing changes — but the cohort is one quarter and the migration cohort is untested either way.
- [structural] The new provider's dashboard is easier to use
  - (not collided — structural assumptions don't change conclusions)

## Confidence

Before: 80 → After: 55 (delta -25)

## Surprise

The churn mechanism and the billing mechanism are independent variables.
Support staffing is the hidden variable in both the churn story and the
migration story — neither side of the original argument named it. That
came out of the collision, not from either side alone.

---

## What this record shows a stranger

1. **Thresholds gate the run.** Two tripped, so it fired. If the call had
   been low-stakes and uncontested, the record would be one line:
   "No thresholds tripped. Standing down."
2. **The countermodel is specific.** Three named premises, named evidence,
   named mechanisms — the steelman heuristics (see `steelman.py`) would
   flag "some might disagree" as a strawman and fail the run.
3. **Only load-bearing assumptions get collided.** The dashboard opinion is
   structural — colliding it would be motion without effect.
4. **The delta is the output.** 80 → 55 is a finding: one assumption
   weakened, one survived. No conclusion was demoted — nothing broke.
5. **Surprise proves friction.** The hidden-variable insight existed in
   neither the conclusion nor the countermodel alone.
