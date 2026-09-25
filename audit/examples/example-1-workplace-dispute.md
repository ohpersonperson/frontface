# Worked example: warehouse shift dispute (direct audit mode)

A neutral multi-person situation, audited start to finish. The teller
is Priya, the shift manager. Two warehouse staff — Dana and Marco —
disagree about a damaged pallet, and the disagreement is getting
personal. Priya asked for an audit: "don't resolve this, just hold it."

*(The situation is constructed for teaching — it shows the audit's
shape, not real findings.)*

## The material (what Priya said)

> Dana says the pallet was already damaged when it arrived. Marco says
> it was intact and Dana must have damaged it during unloading, because
> he panicked about the backlog. Actually, the shift was Tuesday, not
> Monday. Marco withdrew his claim that Dana hid the damage — he says
> he never actually saw her hide anything.

## Discipline 1 — hold the contradictions

Two tensions, held as parallel sentences (the scan rejects any
subordinating connective):

- Dana says the pallet was already damaged. Marco says it was intact.
- Marco says Dana damaged it during unloading. Dana says she found it
  that way.

No synthesis. No "the truth is probably somewhere in the middle."
Both halves stay live.

## Discipline 2 — time-indexed person-states

| When | Person | State |
|------|--------|-------|
| 2026-09-18 | Dana | calm, cooperative |
| 2026-09-20 | Dana | withdrawn, clipped |
| 2026-09-18 | Marco | agitated, loud |
| 2026-09-20 | Marco | quieter, avoiding Dana |

Dana is not "difficult." Marco is not "a liar." Tuesday-Dana and
Thursday-Dana are both real. The scan flags permanent-label language
if it appears — none did here.

## Discipline 3 — correction typing

- **(detail)** "The shift was Tuesday, not Monday." — a date fix. It
  does not reopen anything else.
- **(core-claim)** "Marco withdrew the claim that Dana hid the damage."
  — the account itself shifted. This is the signal: whatever Marco's
  current position is, the hidden-damage claim is gone, and it stays
  gone unless he re-asserts it.

## Discipline 4 — no supplied motive

Flagged: *"Dana must have damaged it during unloading, because he
panicked about the backlog."*

Two problems, both mechanical: "must have damaged" assigns the act,
and "because he panicked" assigns the why — neither was stated by
Dana. The observed sequence is: the pallet was damaged; Dana and
Marco disagree about when. The panic is Marco's attribution, and the
record keeps it marked as his.

## Discipline 5 — softening self-check

Priya's draft summary said Marco "misspoke" about hiding the damage.
The original word in Marco's account was stronger — he had *accused*
her. Downgrade flagged: accusation → misspeaking. The record keeps
the stronger term until Marco himself softens it.

## The rendered record

```python
from postmo import AuditRecord, HeldTension, PersonState, Correction

rec = AuditRecord(case_name="Warehouse shift dispute")
rec.tensions.append(HeldTension(text=(
    "Dana says the pallet was already damaged. Marco says it was intact.")))
rec.states.append(PersonState(when="2026-09-18", person="Dana",
                              state="calm, cooperative"))
rec.states.append(PersonState(when="2026-09-20", person="Dana",
                              state="withdrawn, clipped"))
rec.corrections.append(Correction(kind="detail",
    text="The shift was Tuesday, not Monday."))
rec.corrections.append(Correction(kind="core-claim",
    text="Marco withdrew the claim that Dana hid the damage."))
rec.log(1, "enforced", "2 tensions held as parallel sentences")
rec.log(2, "enforced", "4 person-states sequenced, no verdicts")
rec.log(3, "enforced", "1 detail + 1 core-claim correction typed")
rec.log(4, "flagged", "supplied motive: 'because he panicked'")
rec.log(5, "flagged", "downgrade: accusation -> misspeaking")
print(rec.render())
```

## The conversational surface

`rec.render_conversation()` produces the human-readable digest —
tensions named explicitly, per-person accounts, correction types
stated before responding to them, flags inline, and the closing
line: *"Nothing here is resolved. The contradictions stay live; the
sequences stay sequences."*

## What the next session loads

The rendered record is the full structured artifact: tensions,
states, corrections, flags, the timestamped discipline log, and any
evidence items. A later session parses it back (`postmo.parse`)
and continues the audit — nothing re-derived, nothing lost.
