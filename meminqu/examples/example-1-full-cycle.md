# Worked Example: one full interview cycle

A complete guided-capture cycle over three neutral domains
(`personal`, `work`, `projects`), showing the register rotation, the
verbatim capture, and the completion report. This is the output of
`examples/demo_interview.py`, annotated.

## The plan

`plan_cycle` assigned registers deterministically — consecutive domains
never share a set, and all seven registers appear across the cycle:

| Domain | Registers |
|---|---|
| personal | direct, reflective, structural |
| work | irreverent, sparse, temporal |
| projects | contrastive, direct, reflective |

## Domain 1: personal

**Announce:** one clean line — "personal."

**Ask** (2–4 questions, one per register):

1. **[Direct / forensic]** "What is the single most important fact in this domain right now?"
   → "Dentist appointment Thursday at 2pm. Do not reschedule again."
2. **[Reflective / interior]** "What does this domain feel like from the inside this week?"
   → "Stretched thin but oddly calm. Like the week before a trip."
3. **[Structural / systems]** "Which part of this domain's system is under the most strain?"
   → "The handoff between me and Priya — everything queues there."

**Capture.** The answers are packaged verbatim — typos, contradictions,
and all — and appended to `personal/raw.md` under memdate's
pure CAPTURE rules:

```markdown
## 2026-09-24 22:17 UTC — source: meminqu

### Inquiry capture — personal (registers: direct, reflective, structural)

**[Direct / forensic]** What is the single most important fact in this domain right now?
Dentist appointment Thursday at 2pm. Do not reschedule again.

**[Reflective / interior]** What does this domain feel like from the inside this week?
Stretched thin but oddly calm. Like the week before a trip.

**[Structural / systems]** Which part of this domain's system is under the most strain?
The handoff between me and Priya — everything queues there.
```

**Confirm:** "Captured to personal/raw.md." Move on.

## Domain 2: work

**Ask** — note the registers rotated; none repeat the personal set:

1. **[Irreverent / cutting]** "Cut the diplomacy: what is actually going on here?"
   → "We are busy performing progress instead of making it."
2. **[Sparse / minimal]** "This domain in one sentence."
   → "Half-built, fully loved, zero deadline."
3. **[Temporal / what's alive now]** "What changed here since the last time you looked?"
   → "Sleep is back to normal for the first time in a month."

Same capture shape into `work/raw.md`. The irreverent answer is kept
exactly as said — the interviewer does not soften it on the way in.
That is the whole point of the register: politeness is a filter, and
the filter stays off during capture.

## Domain 3: projects

Registers: contrastive, direct, reflective. The contrastive question —
"What is *not* true here, though it might look that way?" — is the one
that defines edges: "It looks like the team is aligned. It is not —
three people are quietly job-hunting." Captured verbatim.

## Completion

```
Interview complete.

Captured:
  - personal: personal/raw.md
  - projects: projects/raw.md
  - work: work/raw.md

Next: continue / deepen a domain / distill / exit.
```

No analysis was performed at any point. If the operator now wants
distillation, that is a separate, explicitly requested operation —
never mixed into the capture pass.
