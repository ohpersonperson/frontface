"""Ground mapping — the pre-interrogation audit of situational state.

Objective: establish exactly what is the case WITHOUT forcing narrative
resolution. Three outputs:

- Held tensions: opposing facts stated as parallel, non-subordinating
  sentences ("X is true. Y is also true."). Never "X, but Y" — the
  subordinating conjunction quietly privileges one side, which is a
  resolution smuggled in as grammar.
- Time-indexed person-state sequence: people change across time; map the
  states, never flatten a person to one characterization.
- Corrections typed as detail vs core-claim: fixing a date is a detail;
  changing what was claimed to have happened is a core-claim change —
  and the latter is the signal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Subordinating conjunctions that privilege one side of a tension.
# "X is true. Y is also true." stays. "X is true, but Y" is rejected —
# the "but" resolves the contradiction by demoting X.
SUBORDINATORS = (
    "but", "however", "although", "though", "yet", "whereas",
    "nevertheless", "nonetheless", "which means", "in other words",
    "so really", "that is to say",
)

_SUB_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in SUBORDINATORS) + r")\b",
    re.IGNORECASE,
)


class GroundError(ValueError):
    """Raised when mapped ground breaks the audit rules."""


def find_subordinators(text: str) -> list[str]:
    """Return the subordinating conjunctions found in the text."""
    return sorted({m.group(0).lower() for m in _SUB_RE.finditer(text)})


@dataclass(frozen=True)
class HeldTension:
    """One pair of opposing facts, held live as parallel sentences."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise GroundError("Held tension must not be empty.")
        bad = find_subordinators(self.text)
        if bad:
            raise GroundError(
                f"Held tension uses subordinating language {bad}: "
                f"{self.text!r}. Restate as parallel non-subordinating "
                "sentences — 'X is true. Y is also true.'"
            )


@dataclass(frozen=True)
class PersonState:
    """One person, one moment, one observed state. Time-indexed."""

    when: str
    person: str
    state: str

    def __post_init__(self) -> None:
        for label, value in (("when", self.when), ("person", self.person),
                             ("state", self.state)):
            if not value.strip():
                raise GroundError(f"PersonState.{label} must not be empty.")


@dataclass(frozen=True)
class Correction:
    """A correction typed by what changed.

    DETAIL: the facts stay the same, a detail was fixed (dates, names,
    sequence order). CORE-CLAIM: what was claimed to have happened
    changed. Core-claim changes are the signal — they mark where the
    account itself shifted.
    """

    kind: str  # "detail" | "core-claim"
    text: str

    def __post_init__(self) -> None:
        if self.kind not in ("detail", "core-claim"):
            raise GroundError(
                f"Correction kind must be 'detail' or 'core-claim', got {self.kind!r}."
            )
        if not self.text.strip():
            raise GroundError("Correction text must not be empty.")


@dataclass
class GroundMap:
    """The audited ground: tensions held, states sequenced, corrections typed."""

    tensions: list[HeldTension] = field(default_factory=list)
    person_states: list[PersonState] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)

    def core_claim_changes(self) -> list[Correction]:
        """The signal: corrections that changed the account itself."""
        return [c for c in self.corrections if c.kind == "core-claim"]

    def render(self) -> str:
        lines = ["## Audited ground"]
        for t in self.tensions:
            lines.append(f"- Held tension: {t.text}")
        for p in self.person_states:
            lines.append(f"- State [{p.when}] {p.person}: {p.state}")
        for c in self.corrections:
            lines.append(f"- Correction ({c.kind}): {c.text}")
        if not (self.tensions or self.person_states or self.corrections):
            lines.append("- (no ground mapped)")
        return "\n".join(lines)
