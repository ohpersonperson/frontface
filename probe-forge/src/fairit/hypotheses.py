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

import warnings
from dataclasses import dataclass, field
from enum import Enum

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


class CategoryGateDeclinedWarning(UserWarning):
    """The category-only tripwire was consulted and declined to fire.

    Emitted for every evidence phrase the gate lets through, carrying
    the phrase and the tripwire result — so the consultation is
    auditable instead of silent. The heuristic stays narrow by design;
    this warning is its visibility, not a claim of completeness.
    """


class OriginType(str, Enum):
    """The operator's claimed origin of one evidence item.

    Visibility and scrutiny, not truth authentication: the package
    labels what the operator *claims*, it does not verify the claim.
    """

    OPERATOR_PARAPHRASE = "operator-paraphrase"
    INDEPENDENT_OBSERVATION = "independent-observation"
    SYNTHETIC_GENERATION = "synthetic-generation"


def normalize_origin_type(value: OriginType | str | None) -> OriginType:
    """Validate a claimed origin; omission or unknown values raise.

    Accepts an OriginType member or a string (case-insensitive;
    hyphens, underscores, and spaces treated alike). Never defaults
    silently: ``None`` and anything outside the three origins raise
    HypothesisError.
    """
    if value is None:
        raise HypothesisError(
            "origin_type is required: operator-paraphrase, "
            "independent-observation, or synthetic-generation. Omission "
            "is a validation error — the origin must be claimed, never "
            "defaulted."
        )
    if isinstance(value, OriginType):
        return value
    if isinstance(value, str):
        key = value.strip().upper().replace("-", "_").replace(" ", "_")
        try:
            return OriginType[key]
        except KeyError:
            pass
    raise HypothesisError(
        f"Invalid origin_type {value!r}: must be one of "
        + ", ".join(m.value for m in OriginType)
    )


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

    `origin_type` is the operator's *claimed* origin of the item —
    operator paraphrase, independent observation, or synthetic
    generation. Mandatory: omission is a validation error. The package
    surfaces the claim in render; it does not authenticate it.
    """

    text: str
    favors: str = "neutral"
    origin_type: OriginType | str | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise HypothesisError("Evidence item text must not be empty.")
        if self.favors not in DIRECTIONED + ("neutral",):
            raise HypothesisError(f"Bad evidence direction: {self.favors!r}.")
        # Normalize the claimed origin (frozen dataclass: __setattr__).
        object.__setattr__(
            self, "origin_type", normalize_origin_type(self.origin_type)
        )
        if looks_category_only(self.text):
            raise CategoryPresumptionError(
                f"Category membership is not evidence: {self.text!r}. "
                "Attach an observation — what was said, done, or omitted, "
                "and what would differ between the hypotheses."
            )
        # The gate was consulted and declined: surface it. Silent
        # pass-through becomes an auditable warning carrying the phrase
        # and the tripwire result. (stacklevel=3: warn() <- __post_init__
        # <- the dataclass-generated __init__ <- the constructing caller.)
        warnings.warn(
            CategoryGateDeclinedWarning(
                f"looks_category_only gate declined for phrase {self.text!r}: "
                "tripwire result=False — phrase passed as evidence. "
                "The gate was consulted; this warning is the audit record."
            ),
            stacklevel=3,
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
            f"  - [{e.favors} | {e.origin_type.value}] {e.text}" for e in self.evidence
        ) or lines.append("  (none)")
        lines.append("Key mechanisms:")
        lines.extend(
            f"  - {m.name} [{m.status}]" for m in self.mechanisms
        ) or lines.append("  (none)")
        if self.remaining_questions:
            lines.append("Remaining questions:")
            lines.extend(f"  - {q}" for q in self.remaining_questions)
        return "\n".join(lines)
