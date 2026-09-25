"""Trigger thresholds: whether the controller should fire at all.

A pressure-test that always fires is noise. The controller evaluates five
thresholds and only runs the full sequence when at least one trips.
Standing down — "no thresholds tripped" — is a valid output.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- The five thresholds ----------------------------------------------------

STAKES = "stakes"
CONFIDENCE_WITHOUT_EVIDENCE = "confidence-without-evidence"
CONTRADICTION = "contradiction-present"
PREMATURE_CONVERGENCE = "premature-convergence"
EXPLICIT = "explicit-invocation"

TRIGGERS = (
    STAKES,
    CONFIDENCE_WITHOUT_EVIDENCE,
    CONTRADICTION,
    PREMATURE_CONVERGENCE,
    EXPLICIT,
)

TRIGGER_DESCRIPTIONS = {
    STAKES: "the conclusion drives a hard-to-reverse decision or a high-consequence claim",
    CONFIDENCE_WITHOUT_EVIDENCE: "confidence is stated or implied at a level the evidence does not support",
    CONTRADICTION: "opposing evidence or a credible counter-take exists and has not been collided",
    PREMATURE_CONVERGENCE: "reasoning converged fast, a single take survived unchallenged, or no alternative was generated and rejected",
    EXPLICIT: "the user asked to stress-test, check reasoning, or run the audit",
}


class TriggerError(ValueError):
    """An unknown or invalid trigger name was supplied."""


@dataclass
class TriggerEvaluation:
    """Which thresholds tripped for a given reasoning-in-progress."""

    tripped: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        unknown = [t for t in self.tripped if t not in TRIGGERS]
        if unknown:
            raise TriggerError(f"Unknown trigger(s): {unknown!r}. Valid: {list(TRIGGERS)}")
        # Deduplicate, preserve order.
        seen: list[str] = []
        for t in self.tripped:
            if t not in seen:
                seen.append(t)
        self.tripped = seen

    @property
    def fires(self) -> bool:
        """True if at least one threshold tripped."""
        return len(self.tripped) > 0

    def stand_down_report(self) -> str:
        """The valid output when nothing tripped: do nothing further."""
        if self.fires:
            raise TriggerError("Cannot stand down: thresholds tripped.")
        return "No thresholds tripped. Standing down — no run performed."

    def report(self) -> str:
        if not self.fires:
            return self.stand_down_report()
        lines = ["Trigger thresholds tripped:"]
        for t in self.tripped:
            lines.append(f"  - {t}: {TRIGGER_DESCRIPTIONS[t]}")
        return "\n".join(lines)
