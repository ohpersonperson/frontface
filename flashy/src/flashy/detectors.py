"""Detectors: artificial stops, drift, and the confidence engine.

Two of these are data plus small functions; the third is a discipline the
package makes explicit rather than automatic.

- Artificial-stop detection is genuinely codeable: the phrases are a fixed
  list, and matching them in output text is a string scan.
- Drift detection is four questions, not a function — the package carries
  the questions and the snap-back rule; the judgment call stays with the
  operator (human or agent).
- The confidence engine is three levels with a hard rule: High and Medium
  never block; only Low pauses, and only for decisions that materially
  change the implementation.
"""

from __future__ import annotations

# Phrases that signal an artificial stop — an execution failure unless a
# genuine limit (context window, missing info, missing permission, safety)
# forces them. Ported verbatim from the original skill's list.
ARTIFICIAL_STOP_PHRASES = (
    "here's a starting point",
    "here's a foundation",
    "this should get you started",
    "you can expand this",
    "you can build upon this",
    "build upon this",
    "the rest follows similarly",
    "due to space",
    "here's part 1",
)

# Permission-to-continue phrases: not valid stopping points. The default
# assumption is to continue unless genuinely blocked.
PERMISSION_PHRASES = (
    "continue?",
    "should i keep going?",
    "want more?",
    "need anything else?",
    "shall i finish?",
)


def detect_artificial_stop(text: str) -> list[str]:
    """Return the artificial-stop phrases found in the text (case-insensitive)."""
    lowered = text.lower()
    return [p for p in ARTIFICIAL_STOP_PHRASES if p in lowered]


def asks_permission_to_continue(text: str) -> list[str]:
    """Return permission-to-continue phrases found (also not valid stops)."""
    lowered = text.lower()
    return [p for p in PERMISSION_PHRASES if p in lowered]


# The four drift questions, run after every milestone and whenever output
# starts feeling like explanation instead of building.
DRIFT_QUESTIONS = (
    "Am I still solving the original problem?",
    "Have I wandered into explanation instead of building?",
    "Did I forget earlier requirements?",
    "Would the user consider this actually finished?",
)

#: The snap-back rule, stated once so every consumer applies it identically.
DRIFT_CORRECTION = (
    "On drift: discard the drifted thread, restate the locked objective, "
    "resume from the last verified milestone. Correct and continue — no apology theater."
)

# --- Confidence engine --------------------------------------------------------

HIGH = "high"
MEDIUM = "medium"
LOW = "low"
CONFIDENCE_LEVELS = (HIGH, MEDIUM, LOW)

CONFIDENCE_GUIDANCE = {
    HIGH: "One reasonable interpretation, low cost if wrong — proceed silently.",
    MEDIUM: "Multiple reasonable interpretations, but cheap/reversible to redo — "
            "proceed, state the assumption inline, don't block on it.",
    LOW: "Materially different deliverables result, or it is expensive/irreversible — "
         "pause and ask. This is the ONLY legitimate pause trigger.",
}


class DetectorError(ValueError):
    """An invalid confidence level or detector input."""


def should_pause(confidence: str) -> bool:
    """Only Low confidence pauses — and only for implementation-changing decisions."""
    if confidence not in CONFIDENCE_LEVELS:
        raise DetectorError(f"Confidence must be one of {CONFIDENCE_LEVELS}.")
    return confidence == LOW


def is_implementation_changing(decision: str) -> bool:
    """Heuristic: does this decision materially change the implementation?

    Examples that do: choice of database/language/framework, deployment
    target, a required API key or credential, an ambiguity where two
    reasonable interpretations produce meaningfully different deliverables.
    The package can't decide this for you — this helper documents the
    bar so callers apply it consistently.
    """
    markers = (
        "database", "framework", "language", "deploy", "api key",
        "credential", "infrastructure", "architecture",
    )
    return any(m in decision.lower() for m in markers)
