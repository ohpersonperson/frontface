"""The codeable core: mechanical linter checks for the five disciplines.

Honesty note, stated once and enforced by the tests: the phrase-list
checks are tripwires, not proof. They catch the mechanical signatures
of discipline violations — subordinating conjunctions, downgrade
wordlists, unattributed motive attributions, tidy-restatement phrases —
and emit REVIEW items for the operator. A fired check is a finding;
a quiet check is not a clean bill of health. What needs judgment
lives in the discipline table (`disciplines.py`), marked as operator
protocol, and stays there.

Overlap note: the subordinator scan and the HeldTension / PersonState /
Correction records mirror `evasion_audit/ground.py` (the probe+forge
conversion). This package stays standalone and dependency-free, so the
definitions are duplicated here rather than imported — the wordlists
are intentionally identical so the two packages can't silently
disagree. See README "Overlap with evasion_audit".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


class ScanError(ValueError):
    """Raised when a scan input breaks the record rules."""


def sentences(text: str) -> list[str]:
    """Split text into sentences. Rough is fine — this is a tripwire."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


# --- Discipline 1: subordinating-conjunction scan -----------------------------

# Conjunctions and connectives that privilege one side of a tension.
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


def find_subordinators(text: str) -> list[str]:
    """Return the subordinating conjunctions found in the text."""
    return sorted({m.group(0).lower() for m in _SUB_RE.finditer(text)})


@dataclass(frozen=True)
class HeldTension:
    """One pair of opposing facts, held live as parallel sentences.

    "I adored her and I'm furious at her" is two sentences, not one
    with a 'but'. The constructor enforces it — a tension that
    subordinates one side has already resolved the contradiction
    in grammar, and the audit refuses to hold it.
    """

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ScanError("Held tension must not be empty.")
        bad = find_subordinators(self.text)
        if bad:
            raise ScanError(
                f"Held tension uses subordinating language {bad}: "
                f"{self.text!r}. Restate as parallel non-subordinating "
                "sentences — 'X is true. Y is also true.'"
            )


# --- Discipline 2: time-indexed person-states ---------------------------------

# Permanent-label language: nouns of character applied as fixed verdicts.
# "He's a liar" is a verdict; "he was lying on Tuesday" is a state.
# Adjectives ("dangerous", "difficult") are deliberately NOT here — they
# can legitimately describe a moment. This list is nouns only.
VERDICT_WORDS = (
    "liar", "fraud", "monster", "narcissist", "psychopath", "sociopath",
    "manipulator", "abuser", "predator", "saint", "angel",
)

_VERDICT_RE = re.compile(
    r"\b(is|are|was|were|'s|'re)\s+(such\s+a\s+|a\s+|an\s+|the\s+)?("
    + "|".join(re.escape(w) for w in VERDICT_WORDS)
    + r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class VerdictWordHit:
    sentence: str
    word: str


def find_verdict_words(text: str) -> list[VerdictWordHit]:
    """Flag permanent-label language for operator review.

    A hit is a REVIEW item, not a rejection — the operator decides
    whether the teller's own word stands (recorded as their CLAIM) or
    the auditor smuggled in a verdict.
    """
    hits: list[VerdictWordHit] = []
    for sentence in sentences(text):
        for match in _VERDICT_RE.finditer(sentence):
            hits.append(VerdictWordHit(sentence=sentence, word=match.group(3).lower()))
    return hits


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
                raise ScanError(f"PersonState.{label} must not be empty.")


# --- Discipline 3: correction typing -------------------------------------------

CORRECTION_KINDS = ("detail", "core-claim")

# Sentences that look like corrections but haven't been typed yet.
# Matched as plain substrings — this is a tripwire, not a parser, and
# every marker here is distinctive enough that substring matching is
# the honest implementation.
CORRECTION_MARKERS = (
    "actually", "no wait", "correction:", "to be clear,",
    "let me correct", "i misspoke", "that was wrong",
    "not quite —", "not quite -",
)


@dataclass(frozen=True)
class Correction:
    """A correction typed by what changed.

    DETAIL: a particular fact is revised (a time, an object, a peripheral
    sequence detail). Does not touch any core claim standing elsewhere —
    never let it trigger re-litigation of an uncorrected core claim.
    CORE-CLAIM: a decision, boundary, conclusion, or central assertion is
    revised. Core-claim changes are the signal: they mark where the
    account itself shifted.
    """

    kind: str  # "detail" | "core-claim"
    text: str

    def __post_init__(self) -> None:
        if self.kind not in CORRECTION_KINDS:
            raise ScanError(
                f"Correction kind must be 'detail' or 'core-claim', got {self.kind!r}."
            )
        if not self.text.strip():
            raise ScanError("Correction text must not be empty.")


@dataclass(frozen=True)
class CorrectionCandidate:
    """A correction-like sentence that hasn't been typed yet.

    The skill's rule: if ambiguous which kind, ask rather than guess.
    The scan surfaces candidates; the operator types them.
    """

    sentence: str
    marker: str


def find_correction_candidates(text: str) -> list[CorrectionCandidate]:
    """Flag correction-like sentences that need typing (D3, operator step)."""
    found: list[CorrectionCandidate] = []
    for sentence in sentences(text):
        lowered = sentence.lower()
        for marker in CORRECTION_MARKERS:
            if marker in lowered:
                found.append(CorrectionCandidate(sentence=sentence, marker=marker))
                break
    return found


# --- Discipline 4: supplied-motive detection -----------------------------------

# Attributions that make a motive/causal claim legitimate — the teller
# (or a named source) assigned the why.
ATTRIBUTION_MARKERS = (
    "said", "stated", "told me", "according to", "in her words",
    "in his words", "in their words", "she thinks", "he thinks",
    "they think", "i think", "my read", "my take",
)

# Explicit guess-flags: a requested read on motive is allowed when
# marked as a guess, never narrated as settled fact.
GUESS_MARKERS = (
    "if i had to guess", "my guess is", "possibly", "maybe",
    "perhaps", "could be that", "i wonder if",
)

# Motive/causal attributions: claims about WHY someone did something,
# or what was going on inside them — stated without attribution.
MOTIVE_PATTERNS = (
    r"because\s+(he|she|they)\s+\w+ed\b",          # "because he panicked"
    r"because\s+(he|she|they)\s+(was|were)\s+\w+ing\b",  # "because she was testing"
    r"\b(he|she|they)\s+(panicked|felt|feels|feared|resented|envied)\b",
    r"\bdriven by\b",
    r"\bmotivated by\b",
    r"\bin order to\b",
    r"\bout of\s+(spite|fear|jealousy|anger|guilt|shame|love)\b",
    r"\b(wanted|needed)\s+to\s+(feel|prove|show|hurt|punish|control)\b",
    r"\bwas trying to\s+(hurt|punish|control|manipulate|prove)\b",
)

_MOTIVE_RES = tuple(re.compile(p, re.IGNORECASE) for p in MOTIVE_PATTERNS)
_ATTRIBUTION_RE = re.compile(
    r"\b(" + "|".join(re.escape(m) for m in ATTRIBUTION_MARKERS) + r")\b|\"",
    re.IGNORECASE,
)
_GUESS_RE = re.compile(
    r"\b(" + "|".join(re.escape(m) for m in GUESS_MARKERS) + r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MotiveFlag:
    """One unattributed motive/causal attribution.

    severity "flag": supplied motive, no attribution — a D4 violation.
    severity "guess": explicitly marked as a guess — allowed, but must
    stay marked; the record keeps it so a later session can't quietly
    promote it to fact.
    """

    sentence: str
    pattern: str
    severity: str  # "flag" | "guess"

    def __post_init__(self) -> None:
        if self.severity not in ("flag", "guess"):
            raise ScanError(f"Bad motive-flag severity: {self.severity!r}.")
        if not self.sentence.strip():
            raise ScanError("Motive flag needs the flagged sentence.")


def detect_supplied_motive(text: str) -> list[MotiveFlag]:
    """Flag motive attributions with no teller attribution (D4).

    "He tackled you because he panicked" → flag. "He said he panicked"
    → clean (the teller assigned the why). "If I had to guess, he
    panicked" → guess (allowed, kept marked).
    """
    flags: list[MotiveFlag] = []
    for sentence in sentences(text):
        lowered = sentence.lower()
        matched = next(
            (p for p, rx in zip(MOTIVE_PATTERNS, _MOTIVE_RES) if rx.search(sentence)),
            None,
        )
        if not matched:
            continue
        if _GUESS_RE.search(sentence):
            flags.append(MotiveFlag(sentence=sentence, pattern=matched, severity="guess"))
        elif not _ATTRIBUTION_RE.search(sentence):
            flags.append(MotiveFlag(sentence=sentence, pattern=matched, severity="flag"))
        # attributed motive ("he said he panicked") is clean — the
        # teller assigned the why, so discipline 4 is satisfied.
    return flags


# --- Discipline 5: softening detection ------------------------------------------

# Strong terms (threat/harm/betrayal language) and their soft replacements.
# A restatement that swaps the left column for the right is softening.
DOWNGRADE_PAIRS: tuple[tuple[str, str], ...] = (
    ("betrayal", "mistake"), ("betrayed", "mistake"),
    ("lied", "misspoke"), ("lying", "misspeaking"),
    ("threatened", "warned"), ("threat", "concern"),
    ("harmed", "hurt"), ("harm", "hurt"),
    ("abused", "mistreated"), ("abuse", "mistreatment"),
    ("attacked", "confronted"), ("attack", "confrontation"),
    ("stole", "took"), ("stolen", "taken"),
    ("cheated", "was unfaithful"), ("cheating", "infidelity"),
    ("manipulated", "influenced"), ("manipulation", "influence"),
    ("gaslit", "confused"), ("gaslighting", "confusion"),
    ("dangerous", "difficult"), ("terrified", "uncomfortable"),
    ("terrifying", "uncomfortable"),
)

STRONG_TERMS = frozenset(strong for strong, _ in DOWNGRADE_PAIRS)

# "So what you're saying is…" restatements that tidy the account.
TIDY_PHRASES = (
    "so what you're saying is", "so what you are saying is",
    "in other words,", "to summarize,", "essentially,",
    "basically,", "the bottom line is",
)

# Resolving ambivalence into one "real" feeling.
AMBIVALENCE_PHRASES = (
    "the real feeling", "what you really mean", "what you really feel",
    "actually you just", "deep down you", "the truth is you",
    "your real", "admit it",
)

_TIDY_RE = re.compile(
    r"\b(" + "|".join(re.escape(p.rstrip(",")) for p in TIDY_PHRASES) + r")\b",
    re.IGNORECASE,
)
_AMBIVALENCE_RE = re.compile(
    r"\b(" + "|".join(re.escape(p) for p in AMBIVALENCE_PHRASES) + r")\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SofteningFlag:
    """One caught softening.

    kind "downgrade": a strong term became a soft one
    ("betrayal" → "mistake").
    kind "dropped": a strong term vanished with no replacement.
    kind "tidy-restatement": "so what you're saying is…" — a restatement
    that tidies the account.
    kind "ambivalence-resolved": "the real feeling is…" — ambivalence
    resolved into one feeling.
    """

    kind: str
    detail: str
    original_term: str = ""
    replacement: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("downgrade", "dropped", "tidy-restatement",
                             "ambivalence-resolved"):
            raise ScanError(f"Bad softening-flag kind: {self.kind!r}.")
        if not self.detail.strip():
            raise ScanError("Softening flag needs a detail.")


def _word_present(word: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE) is not None


def detect_softening(original: str, restatement: str) -> list[SofteningFlag]:
    """Compare the teller's words against a restatement (D5).

    Catches: strong terms downgraded to soft ones, strong terms dropped
    entirely, tidy-restatement phrases, and ambivalence-resolution
    phrases in the restatement. What it cannot catch — generous
    interpretations supplied unasked, evasive answers — stays operator
    protocol (see disciplines.py D5).
    """
    flags: list[SofteningFlag] = []
    for strong, soft in DOWNGRADE_PAIRS:
        if _word_present(strong, original) and not _word_present(strong, restatement):
            if _word_present(soft, restatement):
                flags.append(SofteningFlag(
                    kind="downgrade",
                    detail=f"{strong!r} in the original became {soft!r} in the restatement.",
                    original_term=strong, replacement=soft,
                ))
            else:
                flags.append(SofteningFlag(
                    kind="dropped",
                    detail=f"{strong!r} appears in the original but not in the restatement.",
                    original_term=strong,
                ))
    tidy = _TIDY_RE.search(restatement)
    if tidy:
        flags.append(SofteningFlag(
            kind="tidy-restatement",
            detail=f"Restatement uses a tidying phrase: {tidy.group(0)!r}.",
        ))
    ambivalence = _AMBIVALENCE_RE.search(restatement)
    if ambivalence:
        flags.append(SofteningFlag(
            kind="ambivalence-resolved",
            detail=f"Restatement resolves ambivalence: {ambivalence.group(0)!r}.",
        ))
    return flags


# --- Batch audit: run every mechanical check at once ----------------------------

@dataclass
class ScanReport:
    """Everything the mechanical checks found in one text (or pair)."""

    subordinators: list[str] = field(default_factory=list)
    verdict_words: list[VerdictWordHit] = field(default_factory=list)
    correction_candidates: list[CorrectionCandidate] = field(default_factory=list)
    motive_flags: list[MotiveFlag] = field(default_factory=list)
    softening_flags: list[SofteningFlag] = field(default_factory=list)

    def clean(self) -> bool:
        """True when no check fired. Not a clean bill of health — see the
        honesty note at the top of this module."""
        return not (self.subordinators or self.verdict_words
                    or self.correction_candidates or self.motive_flags
                    or self.softening_flags)


def scan_text(text: str, *, restatement: str = "") -> ScanReport:
    """Run every mechanical check over `text`.

    Pass the auditor's restatement as `restatement` to enable the D5
    softening comparison. Everything that fires is a REVIEW item for
    the operator — the scan finds, the operator decides.
    """
    return ScanReport(
        subordinators=find_subordinators(text),
        verdict_words=find_verdict_words(text),
        correction_candidates=find_correction_candidates(text),
        motive_flags=detect_supplied_motive(text),
        softening_flags=detect_softening(text, restatement) if restatement else [],
    )
