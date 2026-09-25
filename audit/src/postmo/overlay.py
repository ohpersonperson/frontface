"""The overlay contract: where this audit attaches, and what it never does.

As an overlay on the interrogation engine (`adversarial_ifs`), the audit
attaches at two phase hooks:

- Decompose: disciplines 2 (time-indexed person-states), 3 (correction
  typing), and 4 (no supplied motive) govern actor mapping, corrections
  in the source material, and the decomposed field (observed sequences
  only).
- Collide: discipline 1 (hold contradictions — the strict enforcer: no
  subordinating conjunctions, no synthesized third thing, no flagging
  tensions as problems) and discipline 5 (softening self-check on every
  collision output before it passes onward).

The overlay never: resolves a contradiction the engine is holding,
supplies the synthesis (that's the engine's Synthesize phase, or the
user's), or converts a direct-mode audit into an interrogation unasked.

No engine running: the overlay reports the audit record and stops.
Direct audit mode is the headline use — "don't resolve this, just hold
it" — and needs no engine at all.
"""

from __future__ import annotations

from .disciplines import D1, D2, D3, D4, D5

# Phase hooks: engine phase -> disciplines enforced there.
ATTACHMENT_POINTS: dict[str, tuple[int, ...]] = {
    "Decompose": (D2, D3, D4),
    "Collide": (D1, D5),
}

# What the overlay must never do. Enforced at the schema level by
# record.check_stand_down (no synthesis/resolution/verdict sections)
# and stated here so the contract is readable in one place.
NEVER = (
    "resolve a contradiction the engine is holding",
    "supply the synthesis on the teller's behalf",
    "convert a direct-mode audit into an interrogation unasked",
    "soften threat, danger, harm, or betrayal language",
    "treat one correction as license to revisit unrelated standing claims",
)


class OverlayError(ValueError):
    """Raised when overlay input breaks the contract."""


def attachment_for(phase: str) -> tuple[int, ...]:
    """Disciplines enforced at an engine phase."""
    if phase not in ATTACHMENT_POINTS:
        raise OverlayError(
            f"Unknown engine phase {phase!r}. "
            f"Known: {', '.join(ATTACHMENT_POINTS)}."
        )
    return ATTACHMENT_POINTS[phase]


def describe_contract() -> str:
    """The contract as human-readable text."""
    lines = ["Audit overlay contract:", ""]
    for phase, disciplines in ATTACHMENT_POINTS.items():
        lines.append(f"- On {phase}: disciplines {', '.join(map(str, disciplines))}.")
    lines.append("")
    lines.append("The overlay never:")
    for item in NEVER:
        lines.append(f"- {item}.")
    lines.append("")
    lines.append(
        "No engine running: report the audit record and stop. "
        "Direct audit mode needs no engine."
    )
    return "\n".join(lines)
