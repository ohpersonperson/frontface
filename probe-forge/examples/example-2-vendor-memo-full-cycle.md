# Worked Example 2: the vendor memo — full ground → probe → handoff cycle

A company misses a delivery, then sends a memo. This example runs the
whole overlay: ground mapping, jargon testing across two dialects,
evidence tagging, and the handoff brief.

## The sample

> "Regarding the Q3 deliverables: mistakes were made in the scoping
> phase. We're going to circle back with stakeholders and leverage our
> learnings going forward. The team remains committed to excellence."

## Step 1 — ground mapping

```python
ground = GroundMap(
    tensions=[
        HeldTension("The contract promised delivery September 1. Nothing was delivered by October."),
        HeldTension("The memo says the team is committed to excellence. No named person takes responsibility for the miss."),
    ],
    person_states=[
        PersonState("2026-08-15", "vendor PM", "assuring: 'on track for September'"),
        PersonState("2026-10-03", "vendor PM", "deflecting: memo issued, no new date given"),
    ],
    corrections=[
        Correction("core-claim", "first said scoping was complete; now says scoping failed"),
    ],
)
```

Note the second tension: "committed to excellence" vs "no named
responsibility" — stated as parallel sentences. Writing "committed to
excellence, *but* nobody takes responsibility" would smuggle the
conclusion into the grammar.

## Step 2 — probe the shield vocabulary

`detect_markers` hits three candidates across two dialects:

| phrase | dialect |
|---|---|
| mistakes were made | bureaucratic |
| circle back | corporate |
| going forward | bureaucratic |

Each goes through the protocol with its own evidence:

```python
flags = scan_and_test(memo, {
    "mistakes were made": (
        "the passive phrasing names no actor; internal emails name the PM "
        "who cut scoping short — the actor exists and is known", ""),
    "circle back": (
        "used here to end the paragraph about the miss without giving a new date", ""),
    "going forward": (
        "",  # no evidence either way for this instance
    ),
})
```

Results:

- "mistakes were made" → **H-obfuscation** (discriminating evidence: the
  actor is known internally but erased in the memo; the erasure appears
  only in the public-facing text).
- "circle back" → **H-obfuscation** (used to close the accountability
  topic without a commitment).
- "going forward" → **insufficient-evidence** (no observation either way;
  the probe refuses to convict or exonerate on detection alone).

## Step 3 — evidence tagging

```python
[evidence_tag_for(f.record) for f in flags]
# ["OBFUSCATION", "OBFUSCATION", "CLAIM"]
```

The third stays CLAIM with a hypothesis marker — suspected, untested,
not upgraded.

## Step 4 — the handoff brief

```python
brief = AuditBrief(
    case_name="vendor Q3 delivery miss",
    ground=ground,
    records=[f.record for f in flags],
    seeds=[
        "The vendor is managing the relationship, not the delivery: language erases actors exactly where accountability would attach.",
        "The 'learnings' frame converts a missed contract into process improvement — watch whether a new date ever appears.",
    ],
)
print(brief.render())
```

Rendered:

```markdown
---
artifact: audit-brief
date: 2026-09-24
protocol: fairit/1.0
lifecycle: FINAL
---

# Audit brief: vendor Q3 delivery miss

## Audited ground
- Held tension: The contract promised delivery September 1. Nothing was delivered by October.
- Held tension: The memo says the team is committed to excellence. No named person takes responsibility for the miss.
- State [2026-08-15] vendor PM: assuring: 'on track for September'
- State [2026-09-19] vendor PM: deflecting: memo issued, no new date given
- Correction (core-claim): first said scoping was complete; now says scoping failed

## Tested hypotheses

Candidate evasion: the phrase 'mistakes were made' may function as evasion
Best-supported hypothesis: H-obfuscation
Discriminating evidence:
  - [H-obfuscation] the passive phrasing names no actor; internal emails name the PM who cut scoping short — the actor exists and is known
Key mechanisms:
  - (none)
Remaining questions:
  - What observation would distinguish H-obfuscation from H-genuine here? (e.g. does the language appear only under pressure? is it followed by accountability or topic change?)

...

## Handoff seeds
1. The vendor is managing the relationship, not the delivery: language erases actors exactly where accountability would attach.
2. The 'learnings' frame converts a missed contract into process improvement — watch whether a new date ever appears.
```

The brief stops here. No collision, no adjudication, no surprise —
those belong to the interrogation engine. The seeds feed its Diverge
phase, and the overlay stands down.
