"""Evidence taxonomy.

Every input to an interrogation is tagged with exactly one of these tiers.
The core rule is negative: never silently upgrade an assertion into a fact
or an inference into a conclusion. Tags stay visible through every phase.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Tier definitions -------------------------------------------------------

FACT = "FACT"
OBSERVATION = "OBSERVATION"
CLAIM = "CLAIM"
INFERENCE = "INFERENCE"
ASSUMPTION = "ASSUMPTION"
HYPOTHESIS = "HYPOTHESIS"
REQUIREMENT = "REQUIREMENT"
CONSTRAINT = "CONSTRAINT"
DEPENDENCY = "DEPENDENCY"
UNKNOWN = "UNKNOWN"
# Overlay-only: set when the optional evasion-probe overlay is ON.
OBFUSCATION = "OBFUSCATION"

TAXONOMY: dict[str, str] = {
    FACT: "Directly established, unassailable ground truth.",
    OBSERVATION: "Reported or logged, but not independently verified.",
    CLAIM: "An explicit assertion made by an actor or source.",
    INFERENCE: "A conclusion logically drawn from facts or verified observations.",
    ASSUMPTION: "Presumed true without adequate supporting evidence.",
    HYPOTHESIS: "A proposed explanatory model that still needs stress-testing.",
    REQUIREMENT: "A condition that must be true for a model to hold.",
    CONSTRAINT: "A boundary condition limiting viable outcomes.",
    DEPENDENCY: "An element relying directly on the state of another.",
    UNKNOWN: "A critical variable that cannot presently be determined.",
    OBFUSCATION: (
        "Evasive maneuver or jargon shield masking responsibility. "
        "Tag ONLY when the evasion-probe overlay is active and the evasion "
        "hypothesis is supported by discriminating evidence."
    ),
}

CORE_TAGS = frozenset(
    {FACT, OBSERVATION, CLAIM, INFERENCE, ASSUMPTION, HYPOTHESIS,
     REQUIREMENT, CONSTRAINT, DEPENDENCY, UNKNOWN}
)


class EvidenceError(ValueError):
    """Raised when an evidence item breaks the taxonomy rules."""


@dataclass(frozen=True)
class EvidenceItem:
    """One tagged input to the interrogation."""

    text: str
    tag: str

    def __post_init__(self) -> None:
        tag = self.tag.strip().upper()
        if tag not in TAXONOMY:
            raise EvidenceError(
                f"Unknown evidence tag {self.tag!r}. "
                f"Valid tags: {', '.join(sorted(TAXONOMY))}."
            )
        if not self.text.strip():
            raise EvidenceError("Evidence item text must not be empty.")


def normalize_tag(tag: str, *, overlay_on: bool = False) -> str:
    """Validate and normalize a tag. OBFUSCATION needs the overlay on."""
    normalized = tag.strip().upper()
    if normalized not in TAXONOMY:
        raise EvidenceError(f"Unknown evidence tag {tag!r}.")
    if normalized == OBFUSCATION and not overlay_on:
        raise EvidenceError(
            "OBFUSCATION is overlay-only: it may be tagged only when the "
            "evasion-probe overlay is active. Use CLAIM with a hypothesis "
            "marker for suspected-but-untested evasion."
        )
    return normalized


def tag_list() -> list[str]:
    """All valid tags, in canonical order."""
    return list(TAXONOMY)
