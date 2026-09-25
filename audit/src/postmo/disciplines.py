"""The five audit disciplines, stated once.

An audit is not a narrative: a narrative resolves tension toward a
single coherent story; an audit holds the actual shape of what's been
said — including the parts that don't resolve — and tracks it
accurately as it changes.

Each discipline carries its code/operator split explicitly:
`mechanical` is what `scans.py` checks; `operator` is what needs a
human or model judgment and stays protocol, not code. The split is
honest, not aspirational — a mechanical check that fired is a finding;
an operator check is a responsibility.
"""

from __future__ import annotations

D1 = 1  # hold contradictions as contradictions
D2 = 2  # track person-state as time-indexed, not categorical
D3 = 3  # distinguish detail-correction from core-claim correction
D4 = 4  # don't supply motive or causality the teller didn't state
D5 = 5  # self-check for softening and evasion — including your own

DISCIPLINES: dict[int, dict[str, str]] = {
    D1: {
        "name": "hold-contradictions",
        "rule": (
            "When two stated things are in tension, do not pick one side, "
            "do not synthesize a third thing that subordinates one to the "
            "other, and do not flag the tension as a problem needing "
            "resolution. Both halves stay live. If a synthesis is true, "
            "the teller states it — never supply it on their behalf."
        ),
        "mechanical": (
            "Held tensions must be parallel non-subordinating sentences "
            "('X is true. Y is also true.') — the subordinator scan in "
            "scans.py rejects 'X, but/however/which means Y'."
        ),
        "operator": (
            "Recognizing that two statements ARE in tension (the scan "
            "checks grammar, not meaning); refusing to tidy the tension "
            "in surrounding prose; leaving silence where no resolving "
            "sentence is needed."
        ),
    },
    D2: {
        "name": "time-indexed-person-states",
        "rule": (
            "People are not 'good' or 'bad', 'safe' or 'dangerous' as fixed "
            "labels — they are in different states at different points, and "
            "all of those states are real simultaneously. Summarize "
            "sequences of states, never verdicts on persons."
        ),
        "mechanical": (
            "PersonState requires when + person + state, all non-empty; "
            "the verdict-word scan flags permanent-label language "
            "('he is a liar') for operator review."
        ),
        "operator": (
            "Resisting the pull to declare one state 'the mask' and another "
            "'the truth'; keeping the sequence ordered and complete."
        ),
    },
    D3: {
        "name": "correction-typing",
        "rule": (
            "Detail correction: a particular fact is revised (a time, an "
            "object, a peripheral sequence detail) — it does not touch any "
            "core claim standing elsewhere. Core-claim correction: a "
            "decision, boundary, conclusion, or central assertion is "
            "revised. Never let a detail correction trigger re-litigation "
            "of an uncorrected core claim. If ambiguous which kind, ask "
            "rather than guess."
        ),
        "mechanical": (
            "Correction records accept only 'detail' or 'core-claim'; the "
            "correction-candidate scan flags correction-like sentences "
            "('actually…', 'no wait…', 'to be clear…') that haven't been "
            "typed yet."
        ),
        "operator": (
            "Typing ambiguous corrections (ask, don't guess); holding the "
            "line that a detail fix does not reopen standing core claims."
        ),
    },
    D4: {
        "name": "no-supplied-motive",
        "rule": (
            "Track what happened and what was said — not why, unless the "
            "teller assigns the why. 'He tackled you because he panicked' "
            "is an invented motive, even if plausible. State the observed "
            "sequence: who did what, in what order. A directly requested "
            "read on motive is a flagged guess ('if I had to guess…'), "
            "never narrated as settled fact."
        ),
        "mechanical": (
            "The motive scan flags causal/motive attributions ('because he "
            "panicked', 'driven by', 'in order to') that carry no "
            "attribution marker ('he said', 'according to', quotes) and no "
            "explicit guess-flag."
        ),
        "operator": (
            "The final call on whether a flagged attribution was actually "
            "supplied by the teller in surrounding context the scan can't "
            "see; keeping flagged guesses flagged."
        ),
    },
    D5: {
        "name": "softening-self-check",
        "rule": (
            "Before finalizing, check: did a threat/betrayal/harm get "
            "gentler language than the teller used? Did a generous "
            "interpretation get supplied unasked? Did a restatement drop a "
            "contradiction or tidy it? Did ambivalence get resolved into "
            "one 'real' feeling? Did a direct question get answered "
            "evasively? The noticing is part of the deliverable. Also runs "
            "outward: name the teller's own smoothing once, plainly, "
            "without diagnosing — don't press, don't repeat if unpicked."
        ),
        "mechanical": (
            "The softening scan compares original vs restatement: "
            "downgrade wordlist ('betrayal' → 'mistake'), dropped strong "
            "terms, tidy-restatement phrases ('so what you're saying is'), "
            "ambivalence-resolution phrases ('the real feeling is')."
        ),
        "operator": (
            "Generous-interpretation detection; evasive-answer detection; "
            "judging whether a flagged downgrade is a genuine softening or "
            "the teller's own word choice."
        ),
    },
}


def discipline_name(n: int) -> str:
    """Short name for discipline n (1-5)."""
    if n not in DISCIPLINES:
        raise ValueError(f"Unknown discipline: {n!r}. Valid: 1-5.")
    return DISCIPLINES[n]["name"]
