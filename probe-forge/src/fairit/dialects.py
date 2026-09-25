"""Shield-vocabulary marker lists, by dialect.

These lists detect *candidate* instances of jargon that MAY function as
evasion. Detection is the start of the hypothesis protocol, never its
conclusion: a marker hit feeds H-obfuscation / H-genuine / H-both
testing in `hypotheses.py`. No marker, list, or dialect ever produces a
verdict by itself.

The original skill only knew therapy-speak. The same structure covers
corporate-speak and bureaucratic passive voice — the mechanism doesn't
care which dialect the shield is written in.
"""

from __future__ import annotations

# (dialect, phrases). Phrases are matched case-insensitively as
# substrings — they are tripwires, not judgments.
SHIELD_MARKERS: dict[str, tuple[str, ...]] = {
    "therapy": (
        "holding space", "doing the work", "inner child", "boundaries",
        "triggered", "processing", "my truth", "self-care", "nervous system",
        "regulation", "co-regulation", "shadow work", "attachment style",
        "parts of me", "sitting with", "unpacking",
    ),
    "corporate": (
        "circle back", "synergy", "leverage", "bandwidth", "deep dive",
        "move the needle", "take this offline", "low-hanging fruit",
        "best practices", "thought leadership", "rightsizing",
        "synergize", "actionable", "paradigm",
    ),
    "bureaucratic": (
        "mistakes were made", "regrettable", "inappropriate", "it was decided",
        "processes were followed", "at this time", "going forward",
        "lessons learned", "unfortunate", "miscommunication",
        "administrative error", "procedural",
    ),
}

DIALECTS = tuple(SHIELD_MARKERS)


def detect_markers(text: str) -> list[tuple[str, str]]:
    """Find candidate shield-vocabulary instances.

    Returns a list of (dialect, phrase) hits. A hit is a candidate for
    hypothesis testing — it says "examine this," nothing more.
    """
    lowered = text.lower()
    hits: list[tuple[str, str]] = []
    for dialect, phrases in SHIELD_MARKERS.items():
        for phrase in phrases:
            if phrase in lowered:
                hits.append((dialect, phrase))
    return hits
