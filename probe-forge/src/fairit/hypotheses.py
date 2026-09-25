"""Competing-hypothesis testing — the shared core of this package.

Every candidate evasion (shield vocabulary, fogging, DARVO, passive-voice
responsibility-dodging, whatever dialect it arrives in) is tested as
competing hypotheses instead of pre-judged:

- H_OBFUSCATION: the language functions as armor — deflecting
  responsibility, buying status, or changing the topic.
- H_GENUINE: the language is a sincere attempt, correlated with
  accountability.
- H_BOTH: genuine effort that is also conveniently shielding. Both can be
  true — and this is the common case.
- INSUFFICIENT_EVIDENCE: the honest finding when the evidence cannot
  distinguish the hypotheses. Not a failure.

The load-bearing rule, enforced in code: a hypothesis wins ONLY on
**discriminating evidence** — observations that would differ between the
hypotheses. Category membership ("this is therapy-speak", "this is
corporate language") is never evidence. A record that tries to convict
on category alone is rejected.
"""

from __future__ import annotations

from dataclasses import dataclass, field

H_OBFUSCATION = "H-obfuscation"
H_GENUINE = "H-genuine"
H_BOTH = "H-both"
INSUFFICIENT_EVIDENCE = "insufficient-evidence"

VERDICTS = (H_OBFUSCATION, H_GENUINE, H_BOTH, INSUFFICIENT_EVIDENCE)
DIRECTIONED = (H_OBFUSCATION, H_GENUINE, H_BOTH)

SUPPORT_STATUSES = ("supported", "contested", "unsupported")


class HypothesisError(ValueError):
    """Raised when a hypothesis record breaks the testing rules."""


class CategoryPresumptionError(HypothesisError):
    """Raised when a record tries to convict on category membership alone.

    The old probe (v1) pre-judged whole categories of language as
    obfuscation. This error is that failure mode, made impossible in code:
    "therapy-speak" by itself, with no observation attached, is not
    discriminating evidence of anything.
    """


# Category labels that may contextualize a record but may never stand
# in for evidence. Lowercase, punctuation-stripped for matching.
CATEGORY_LABELS = frozenset({
    "therapy speak", "therapy-speak", "therapyspeak", "self regulation",
    "self-regulation", "selfregulation",
    "corporate speak", "corporate-speak", "corporatespeak",
    "bureaucratic", "bureaucratese", "legalese", "wellness speak",
    "wellness-speak", "hr speak", "hr-speak",
})


def looks_category_only(text: str) -> bool:
    """True when an evidence item names a category and observes nothing.

    Heuristic, deliberately conservative: it catches the bare label
    ("therapy-speak") and the label plus filler words ("uses
    therapy-speak", "sounds like corporate speak"). Anything with a real
    observation attached passes — the prose-level judgment ("is this
    actually discriminating?") stays with the operator, and this check
    exists to make the *failure mode* impossible, not to certify the
    good cases.
    """
    import re
    import string

    cleaned = text.strip().lower().translate(
        str.maketrans(string.punctuation, " " * len(string.punctuation))
    )
    cleaned = " ".join(cleaned.split())
    if cleaned in CATEGORY_LABELS:
        return True
    for label in CATEGORY_LABELS:
        rest = cleaned.replace(label, " ", 1)
        filler = rest.split()
        # e.g. "uses therapy-speak" / "sounds like corporate speak"
        if len(filler) <= 2 and all(
            w in {"uses", "using", "use", "sounds", "like", "is", "very", "kind",
                  "of", "sort", "type", "just", "simply"} for w in filler
        ):
            return True
        if re.fullmatch(r"(uses|using|is|sounds like)\s*", rest + " ") or not filler:
            return True
    return False


@dataclass(frozen=True)
class DiscriminatingEvidence:
    """One observation that would differ between the hypotheses.

    `favors` names which hypothesis this observation supports, or
    "neutral" for an observation that constrains the case without
    favoring a side (e.g. a timeline fact both hypotheses must fit).
    """

    text: str
    favors: str = "neutral"

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise HypothesisError("Evidence item text must not be empty.")
        if self.favors not in DIRECTIONED + ("neutral",):
            raise HypothesisError(f"Bad evidence direction: {self.favors!r}.")
        if looks_category_only(self.text):
            raise CategoryPresumptionError(
                f"Category membership is not evidence: {self.text!r}. "
                "Attach an observation — what was said, done, or omitted, "
                "and what would differ between the hypotheses."
            )


@dataclass(frozen=True)
class Mechanism:
    """One candidate tactic, held as a hypothesis with a support status."""

    name: str
    status: str  # supported | contested | unsupported

    def __post_init__(self) -> None:
        if self.status not in SUPPORT_STATUSES:
            raise HypothesisError(f"Bad mechanism status: {self.status!r}.")
        if not self.name.strip():
            raise HypothesisError("Mechanism name must not be empty.")


@dataclass
class HypothesisRecord:
    """The result of testing one candidate evasion.

    - candidate: the responsibility that may be dodged, or the flagged
      language instance — specific, not a category.
    - verdict: the best-supported hypothesis, or INSUFFICIENT_EVIDENCE.
    - evidence: observations that separate the hypotheses.
    - mechanisms: candidate tactics, each with a support status.
    - remaining_questions: what evidence would resolve the open
      hypotheses. Required when the verdict is INSUFFICIENT_EVIDENCE.
    """

    candidate: str
    verdict: str
    evidence: list[DiscriminatingEvidence] = field(default_factory=list)
    mechanisms: list[Mechanism] = field(default_factory=list)
    remaining_questions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise HypothesisError(f"Bad verdict: {self.verdict!r}.")
        if not self.candidate.strip():
            raise HypothesisError("Candidate must name the specific evasion or language instance.")
        self._require_discriminating_evidence()

    def _favors(self, direction: str) -> list[DiscriminatingEvidence]:
        return [e for e in self.evidence if e.favors == direction]

    def _require_discriminating_evidence(self) -> None:
        if self.verdict == H_OBFUSCATION and not self._favors(H_OBFUSCATION):
            raise HypothesisError(
                "H-obfuscation requires at least one evidence item favoring "
                "H-obfuscation. Category membership does not count."
            )
        if self.verdict == H_GENUINE and not self._favors(H_GENUINE):
            raise HypothesisError(
                "H-genuine requires at least one evidence item favoring H-genuine."
            )
        if self.verdict == H_BOTH and not (
            self._favors(H_OBFUSCATION) and self._favors(H_GENUINE)
        ):
            raise HypothesisError(
                "H-both requires discriminating evidence on BOTH sides — "
                "at least one item favoring H-obfuscation and one favoring "
                "H-genuine. Otherwise the honest verdict is one of the "
                "other three."
            )
        if self.verdict == INSUFFICIENT_EVIDENCE and not self.remaining_questions:
            raise HypothesisError(
                "An insufficient-evidence verdict must name what evidence "
                "would resolve the open hypotheses."
            )

    def supports_obfuscation(self) -> bool:
        """True only for a supported H-obfuscation verdict.

        This is the single gate for the OBFUSCATION evidence tag.
        Everything else — including suspected-but-untested material —
        stays CLAIM with a hypothesis marker.
        """
        return self.verdict == H_OBFUSCATION and (
            not self.mechanisms
            or any(m.status == "supported" for m in self.mechanisms)
        )

    def summary(self) -> str:
        lines = [
            f"Candidate evasion: {self.candidate}",
            f"Best-supported hypothesis: {self.verdict}",
            "Discriminating evidence:",
        ]
        lines.extend(
            f"  - [{e.favors}] {e.text}" for e in self.evidence
        ) or lines.append("  (none)")
        lines.append("Key mechanisms:")
        lines.extend(
            f"  - {m.name} [{m.status}]" for m in self.mechanisms
        ) or lines.append("  (none)")
        if self.remaining_questions:
            lines.append("Remaining questions:")
            lines.extend(f"  - {q}" for q in self.remaining_questions)
        return "\n".join(lines)
