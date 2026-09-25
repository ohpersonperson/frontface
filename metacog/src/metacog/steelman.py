"""Steelman-quality heuristics: catch weak countermodels mechanically.

The most common failure mode of a pressure test is the strawman — a
countermodel so weak the collision is theater and the confidence revision
is invalid. A model can always *claim* it steelmanned. These heuristics
check the countermodel's text for the mechanical signatures of weakness:

- too short to be specific,
- hedge phrases with no named premises ("some might disagree..."),
- no named premises, evidence, or mechanism at all,
- a restatement of the conclusion wearing contrast clothing.

They cannot prove a countermodel is strong. They reliably catch the ones
that are obviously weak — which is the failure mode the 2026-09-23
live-model evals found in small models.

An honest admission ("I cannot build a strong countermodel") is not a
failure: it is a finding — the conclusion may be unopposed because the
field is thin, not because it is strong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Phrases that signal a weak version being offered instead of the strongest case.
WEAK_MARKERS = (
    "some might say",
    "someone might disagree",
    "someone might argue",
    "some might argue",
    "it could be argued",
    "one could argue",
    "critics might say",
    "others might claim",
)

# Markers that the countermodel names something concrete: a premise, a piece
# of evidence, a mechanism, or data.
SPECIFICITY_MARKERS = (
    "premise",
    "evidence",
    "mechanism",
    "data",
    "because",
    "study",
    "studies",
    "measurement",
    "measured",
    "record",
    "documented",
)

# Markers that the text actually opposes the conclusion rather than echoing it.
CONTRAST_MARKERS = (
    "however",
    "but",
    "instead",
    "on the contrary",
    "in contrast",
    "rather",
    "fails",
    "false",
    "wrong",
)

# Admissions that no strong countermodel exists — an honest finding.
UNOPPOSED_MARKERS = (
    "cannot build a strong countermodel",
    "no strong countermodel",
    "unable to construct",
    "no credible opposing case",
)

#: A steelman under this many words is almost always a strawman.
MIN_WORDS = 40

STRONG = "strong"
WEAK = "weak"
UNOPPOSED = "unopposed"


@dataclass
class SteelmanReport:
    strength: str
    flags: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True unless the countermodel is a strawman.

        'Unopposed' is ok — it is a finding, not a failure.
        """
        return self.strength in (STRONG, UNOPPOSED)


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def check_countermodel(text: str, conclusion: str) -> SteelmanReport:
    """Run the mechanical checks on a countermodel's text."""
    flags: list[str] = []
    lowered = text.lower()

    if any(m in lowered for m in UNOPPOSED_MARKERS):
        return SteelmanReport(
            strength=UNOPPOSED,
            flags=["unopposed-thin-field: no strong countermodel could be built"],
        )

    words = _words(text)
    if len(words) < MIN_WORDS:
        flags.append(f"too-short: {len(words)} words (minimum {MIN_WORDS})")

    has_weak = any(m in lowered for m in WEAK_MARKERS)
    has_specific = any(m in lowered for m in SPECIFICITY_MARKERS)
    if has_weak and not has_specific:
        flags.append("hedged-no-specifics: weak-version phrasing with no named premises")
    if not has_specific:
        flags.append("no-named-premises: no premise, evidence, mechanism, or data named")

    # Restatement check: if the countermodel shares most of the conclusion's
    # content words and uses no contrast language, it is echoing, not opposing.
    conclusion_words = set(_words(conclusion))
    counter_words = set(words)
    stopwords = {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with",
        "is", "are", "was", "were", "be", "it", "its", "that", "this", "as",
        "at", "by", "from", "we", "you", "they", "will", "would", "should",
    }
    content_conclusion = conclusion_words - stopwords
    content_counter = counter_words - stopwords
    if content_conclusion:
        overlap = len(content_conclusion & content_counter) / len(content_conclusion)
        has_contrast = any(m in lowered for m in CONTRAST_MARKERS)
        if overlap > 0.6 and not has_contrast:
            flags.append(
                f"restates-conclusion: {overlap:.0%} content-word overlap, no contrast language"
            )

    strength = WEAK if flags else STRONG
    return SteelmanReport(strength=strength, flags=flags)
