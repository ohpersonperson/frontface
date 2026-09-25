---
artifact: interrogation-state
field: vendor-sla-conformance
interrogation: 1
date: 2026-09-24
depth: deep
trigger_context: adjudication requested — vendor claims SLA conformance
status: complete
lifecycle: INITIAL
protocol: IFS/1.0
persistence: external
canonical: true
---

# Interrogation State: Vendor SLA conformance (adjudication mode)

*Teaching example. Adjudication mode judges a claim against an explicit standard — here, a service contract. The field is constructed — no real findings.*

## Interrogation Metadata

- Date: 2026-09-24
- Field: Vendor SLA conformance
- Depth: deep (adjudication)
- Interrogation: 1
- Trigger context: adjudication requested — the vendor claims full SLA conformance for Q3
- Protocol: IFS/1.0
- Lifecycle: INITIAL

## The standard (supplied in the adjudication request; illustrative)

The service contract requires of any conforming quarter:

- **(S1)** 99.5% uptime measured on the vendor's own status page, excluding scheduled maintenance windows announced 72+ hours ahead.
- **(S2)** P1 incidents acknowledged within 15 minutes and resolved within 4 hours; every P1 must have a written postmortem within 5 business days.
- **(S3)** No single incident may affect more than 25% of the customer's active users.

## Prior State

- Prior interrogation: Not supplied
- Key dispositions: none (session 1)

## 1. Identify

- Field: Does Q3 conform to the contract's SLA?
- Objective: verdict on conformance — conforms / does not conform — per the contract's text, not the vendor's narrative.
- Scope: conformance only; whether the vendor is a good partner is a separate field.

## 2. Decompose

| # | Tag | Content |
|---|---|---|
| 1 | FACT | Contract text S1/S2/S3 as stated above |
| 2 | CLAIM | Vendor: "we met all SLAs in Q3" (quarterly report) |
| 3 | FACT | Status page: 99.7% uptime in Q3 (vendor's own measurement) |
| 4 | FACT | Two P1 incidents in Q3: Aug 9 (payment outage, 6.5 hours), Sep 14 (login outage, 2 hours) |
| 5 | FACT | Aug 9 postmortem published Aug 16 (5 business days); Sep 14 postmortem published Sep 23 (7 business days) |
| 6 | FACT | Aug 9 incident affected ~40% of active users (vendor's incident report) |
| 7 | OBSERVATION | Vendor's report counts the Aug 9 outage as "scheduled maintenance" — announced 41 hours ahead (report, unverified against the actual announcement) |

## 3. Diverge

### Take A — Conforms

The vendor's numbers clear the bars: 99.7% exceeds 99.5%, and if the Aug 9 outage was scheduled maintenance per the contract's exclusion, the incident counts drop to one P1, which was acknowledged in 8 minutes and resolved in 2 hours. Evidence: #2, #3, #7.

### Take B — Does not conform

The text fails on the incident record: the Sep 14 postmortem arrived in 7 business days against a 5-day requirement, and the Aug 9 incident hit 40% of users against S3's 25% cap. Evidence: #4, #5, #6, #1.

## 4. Collide

### Pair A/B

- Contradiction: does conformance live in the vendor's reclassification of the Aug 9 outage, or in the incident facts against the contract text?
- Premise that must break: A requires "announced 41 hours ahead" to satisfy a 72-hour notice requirement.
- Discriminator: #7 against S1's own words — 41 hours is less than 72. The exclusion fails on the contract's text; the Aug 9 outage is unscheduled, making it a P1 incident subject to S2 and S3. A breaks.

## 5. Refine

### Key 1

- Statement: The Aug 9 outage cannot be excluded as scheduled maintenance — the 41-hour notice fails the contract's 72-hour requirement.
- Classification: ESTABLISHED
- Evidence: FACT #7, FACT #1
- Confidence: HIGH — arithmetic on the contract's own terms.
- Structural vulnerability: depends on the 41-hour figure from the vendor's report being accurate (OBSERVATION).
- Falsifier: timestamped evidence of a 72+ hour advance announcement.

### Key 2

- Statement: Q3 fails S3 — the Aug 9 incident affected ~40% of active users against a 25% cap.
- Classification: ESTABLISHED
- Evidence: FACT #6, FACT #1
- Confidence: HIGH
- Structural vulnerability: none structural; the vendor's own incident report states the figure.
- Falsifier: a corrected incident report showing ≤25% affected.

### Key 3

- Statement: Q3 fails S2's postmortem deadline — the Sep 14 postmortem arrived in 7 business days against a 5-day requirement.
- Classification: ESTABLISHED
- Evidence: FACT #5, FACT #1
- Confidence: HIGH
- Structural vulnerability: business-day counting assumes no customer-side holidays fell in the window.
- Falsifier: a calendar showing a qualifying holiday inside the window.

*A candidate Key ("the vendor deliberately misclassified the outage") was discarded — motive attribution without evidence; the artifact is what's judged.*

## 6. Surprise

The vendor's uptime figure is the best number in the report — and it is the least informative. Conformance was never going to be decided by S1; the incident terms (S2/S3) are where the quarter was lost. The headline metric was a decoy, including in the vendor's own framing.

## 7. Synthesize

- Established: Aug 9 was unscheduled (fails S1 exclusion); incident hit 40% of users (fails S3); Sep 14 postmortem late (fails S2).
- Verdict: **DOES NOT CONFORM to the SLA** — fails S2 and S3 on the contract's text. S1's 99.7% figure is uncontested but not dispositive.
- Remaining uncertainties: verify the 41-hour announcement timestamp (#7).
- Primary next target: contractual remedy discussion, not further investigation.

## State Status

- Interrogation: Complete
- Lifecycle: INITIAL
- State: Canonical
- Persistence: External
- External save: performed by the caller, not the engine
