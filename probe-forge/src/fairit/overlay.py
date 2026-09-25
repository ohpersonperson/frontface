"""The evasion-probe protocol: test, never presume.

This is the front-facing form of the two skills being converted together:

- responsibility-obfuscation-probe: every candidate evasion becomes
  competing hypotheses tested against discriminating evidence.
- field-forge's probe stage: the same protocol, generalized past
  therapy-speak to any shield dialect (corporate, bureaucratic).

One implementation, two consumers — the overlap the assessment flagged
is structural, and this module is the single place the protocol lives.

The probe's outputs:
- ObfuscatedObject: the responsibility that MAY be dodged, with a
  support status (supported / contested / unsupported) — never a verdict.
- JargonFlag: one instance of possibly-evasive vocabulary, run through
  H-obfuscation / H-genuine / H-both against discriminating evidence.
- The evidence tag for a record: OBFUSCATION only when H-obfuscation is
  supported by discriminating evidence; otherwise CLAIM with a
  hypothesis marker. Suspected-but-untested material is never upgraded
  on category membership alone.

The probe never collides, adjudicates, refines, or extracts surprise.
Its output feeds whatever comes next (the interrogation engine's
Diverge phase, or the operator's own judgment) as hypothesis-tagged
material.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dialects import DIALECTS, detect_markers
from .evidence import OBFUSCATION, CLAIM, normalize_tag
from .hypotheses import (
    H_OBFUSCATION,
    H_GENUINE,
    H_BOTH,
    INSUFFICIENT_EVIDENCE,
    SUPPORT_STATUSES,
    DiscriminatingEvidence,
    HypothesisRecord,
    Mechanism,
)


class ProbeError(ValueError):
    """Raised when probe input breaks the protocol."""


@dataclass(frozen=True)
class JargonFlag:
    """One instance of possibly-evasive vocabulary, under test.

    `dialect` names where the shield vocabulary came from; `record`
    carries the actual hypothesis test. A flag with no test attached is
    incomplete — detection without testing is exactly the v1 failure
    mode this package exists to prevent.
    """

    phrase: str
    dialect: str
    record: HypothesisRecord

    def __post_init__(self) -> None:
        if not self.phrase.strip():
            raise ProbeError("Jargon flag needs the flagged phrase.")
        if self.dialect not in DIALECTS:
            raise ProbeError(
                f"Unknown dialect {self.dialect!r}. Known: {', '.join(DIALECTS)}."
            )


@dataclass(frozen=True)
class ObfuscatedObject:
    """The responsibility that may be dodged — a hypothesis, not a verdict."""

    candidate: str
    support: str  # supported | contested | unsupported
    apparent_function: str = ""  # what the evasion would achieve if real

    def __post_init__(self) -> None:
        if not self.candidate.strip():
            raise ProbeError("Obfuscated-object candidate must not be empty.")
        if self.support not in SUPPORT_STATUSES:
            raise ProbeError(f"Bad support status: {self.support!r}.")


def run_jargon_test(
    phrase: str,
    dialect: str,
    evidence_for_obfuscation: str,
    evidence_for_genuine: str,
    *,
    mechanisms: list[Mechanism] | None = None,
    remaining_questions: list[str] | None = None,
) -> JargonFlag:
    """Run one jargon instance through the hypothesis protocol.

    Both hypotheses are tested against discriminating evidence. When the
    evidence favors one side, that hypothesis wins; when it favors both,
    the honest verdict is H-both; when it can't distinguish them, the
    honest verdict is insufficient-evidence — never a verdict.
    """
    has_obf = bool(evidence_for_obfuscation.strip())
    has_gen = bool(evidence_for_genuine.strip())
    if has_obf and not has_gen:
        verdict = H_OBFUSCATION
        evidence = [DiscriminatingEvidence(evidence_for_obfuscation, H_OBFUSCATION)]
    elif has_gen and not has_obf:
        verdict = H_GENUINE
        evidence = [DiscriminatingEvidence(evidence_for_genuine, H_GENUINE)]
    elif has_obf and has_gen:
        verdict = H_BOTH
        evidence = [
            DiscriminatingEvidence(evidence_for_obfuscation, H_OBFUSCATION),
            DiscriminatingEvidence(evidence_for_genuine, H_GENUINE),
        ]
    else:
        verdict = INSUFFICIENT_EVIDENCE
        evidence = []
        if not remaining_questions:
            remaining_questions = [
                "What observation would distinguish H-obfuscation from "
                "H-genuine here? (e.g. does the language appear only under "
                "pressure? is it followed by accountability or topic change?)"
            ]
    record = HypothesisRecord(
        candidate=f"the phrase {phrase!r} may function as evasion",
        verdict=verdict,
        evidence=evidence,
        mechanisms=list(mechanisms or []),
        remaining_questions=list(remaining_questions or []),
    )
    return JargonFlag(phrase=phrase, dialect=dialect, record=record)


def scan_and_test(
    text: str,
    evidence: dict[str, tuple[str, str]],
) -> list[JargonFlag]:
    """Detect shield vocabulary in text and run each hit through the protocol.

    `evidence` maps each detected phrase to
    (evidence_for_obfuscation, evidence_for_genuine). A hit with no
    supplied evidence gets the insufficient-evidence verdict — the probe
    refuses to test-free convict OR exonerate on detection alone.
    """
    flags: list[JargonFlag] = []
    for dialect, phrase in detect_markers(text):
        for_obf, for_gen = evidence.get(phrase, ("", ""))
        flags.append(
            run_jargon_test(
                phrase, dialect, for_obf, for_gen,
                remaining_questions=[
                    "What evidence would distinguish obfuscation from "
                    "genuine use here?"
                ] if not (for_obf.strip() or for_gen.strip()) else [],
            )
        )
    return flags


def evidence_tag_for(record: HypothesisRecord, *, probe_ran: bool = True) -> str:
    """The evidence tag a record earns.

    OBFUSCATION only when the probe ran and H-obfuscation is supported
    by discriminating evidence. Everything else stays CLAIM — with a
    hypothesis marker, so downstream consumers know a test was run.
    """
    if probe_ran and record.supports_obfuscation():
        return normalize_tag(OBFUSCATION, probe_ran=True)
    return normalize_tag(CLAIM)
