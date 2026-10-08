"""The evasion-probe overlay (opt-in).

Decoupling note: this is the mechanism of the skill-suite's "Field Forge"
overlay, renamed in plain language. The workshop stage names
(Anvil/Hammer/Furnace) are replaced by what each stage actually does:

- GROUND (was "Anvil"): map the exact situational state without forcing a
  narrative resolution.
- PROBE (was "Hammer"): test — never presume — evasion hypotheses, including
  jargon armor of any kind (corporate, legal, therapeutic, wellness).
- HANDOFF (was "Furnace"): build 2-3 Take seeds and feed them into the
  kernel's Diverge phase, then stand down.

The overlay never replaces Diverge/Collide. Default: OFF. Activate only when
asked, or when the field is clearly an evasion / responsibility problem.

PARAM-PRESSIT-003: the activation condition is now evaluated, not just
stated. `scan_evasion_cues()` runs a passive deterministic pre-scan over
the field text against the fixed EVASION_CUES list; when cues are present
and the overlay flag is off, `engine.run()` raises `EvasionHalt` until the
operator explicitly acknowledges (re-invoke with acknowledge_evasion=True,
overlay on or false-alarm confirmed). The flag itself is never auto-engaged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

GROUND = "ground"
PROBE = "probe"
HANDOFF = "handoff"

# Evasion hypotheses for jargon-armor testing. Every flagged instance of
# shield-vocabulary is run through H-obfuscation / H-genuine / H-both —
# never pre-judged as armor by category membership alone.
H_OBFUSCATION = "H-obfuscation"
H_GENUINE = "H-genuine"
H_BOTH = "H-both"
H_INSUFFICIENT = "insufficient-evidence"

JARGON_HYPOTHESES = (H_OBFUSCATION, H_GENUINE, H_BOTH, H_INSUFFICIENT)

SUPPORT_STATUSES = ("supported", "contested", "unsupported")


class OverlayError(ValueError):
    """Raised when overlay input breaks the contract."""


class EvasionHalt(RuntimeError):
    """Mandatory hard halt: evasion cues present, overlay off, unacknowledged.

    Carries the matched cues. In a non-interactive library "halt until
    acknowledged" takes this shape: the exception stops field processing,
    and the caller re-invokes with acknowledge_evasion=True — either
    activating the overlay or confirming the false alarm. Deliberately
    NOT an EngineError subclass caught by run()'s normalize handler;
    this halt must propagate, never surface as ok=False.
    """

    def __init__(self, cues: list[str]) -> None:
        self.cues = list(cues)
        super().__init__(
            "Evasion pre-scan found cues: "
            + ", ".join(repr(c) for c in cues)
            + ". Field processing halted: re-invoke with "
            "acknowledge_evasion=True (overlay on, or false alarm "
            "confirmed). The overlay flag is never auto-engaged."
        )


# PARAM-PRESSIT-003: fixed, documented cue list for the passive
# deterministic pre-scan. Case-insensitive substring match. The list is
# deliberately narrow — it catches evasion-shaped fields, it does not
# certify clean ones.
EVASION_CUES = (
    # Responsibility denial: the outcome is placed outside the actor.
    "not my fault",
    "wasn't my fault",
    "was not my fault",
    "not my responsibility",
    "wasn't my responsibility",
    "was not my responsibility",
    "mistakes were made",
    "i had no choice",
    "i was just following orders",
    # Motive framing: noble intent offered in place of an account.
    "i was only trying to help",
    "i was just trying to help",
    "my intentions were good",
    "i meant well",
    # "I don't know" patterns: claimed ignorance as a shield.
    "i don't know",
    "i dont know",
    "i can't remember",
    "i cant remember",
    "don't recall",
    "can't recall",
)


def scan_evasion_cues(field_text: str) -> list[str]:
    """Passive pre-scan: return the evasion cues present in the field text.

    Deterministic (fixed cue list, case-insensitive substring match),
    no side effects. Does not touch the overlay flag — evaluation only.
    """
    lowered = field_text.lower()
    return [cue for cue in EVASION_CUES if cue in lowered]


@dataclass
class JargonFlag:
    """One instance of possibly-evasive vocabulary."""

    phrase: str
    hypothesis: str = H_INSUFFICIENT
    discriminating_evidence: str = ""

    def __post_init__(self) -> None:
        if self.hypothesis not in JARGON_HYPOTHESES:
            raise OverlayError(f"Bad jargon hypothesis: {self.hypothesis!r}.")
        if not self.phrase.strip():
            raise OverlayError("Jargon flag needs the flagged phrase.")


@dataclass
class ProbeBrief:
    """The overlay's output: audited ground, tested hypotheses, Take seeds.

    This is a *brief*, not an interrogation result — it is fed into the
    kernel's Diverge phase. The kernel's state artifact stays canonical.
    """

    field: str
    held_tensions: list[str] = field(default_factory=list)
    person_state_sequence: list[str] = field(default_factory=list)
    corrections: list[str] = field(default_factory=list)
    obfuscated_object: str = ""
    obfuscation_support: str = H_INSUFFICIENT
    apparent_function: str = ""
    active_tactics: list[str] = field(default_factory=list)
    jargon_flags: list[JargonFlag] = field(default_factory=list)
    take_seeds: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise OverlayError("Probe brief needs a field name.")
        if self.obfuscation_support not in SUPPORT_STATUSES + (H_INSUFFICIENT,):
            raise OverlayError(f"Bad support status: {self.obfuscation_support!r}.")

    def supported_obfuscation(self) -> bool:
        """True only when the evasion hypothesis has discriminating evidence.

        The OBFUSCATION evidence tag may be used only in this case; anything
        else stays CLAIM with a hypothesis marker.
        """
        return self.obfuscation_support == "supported" and bool(
            self.obfuscated_object.strip()
        )


def ground(held_tensions: list[str], person_states: list[str]) -> dict:
    """GROUND stage: hold contradictions live, time-index person states.

    Contradictions are stated as parallel non-subordinating sentences:
    "X is true. Y is also true." Never "X, but Y".
    """
    for t in held_tensions:
        if not t.strip():
            raise OverlayError("Held tension must not be empty.")
    return {"held_tensions": held_tensions, "person_state_sequence": person_states}


def probe_jargon(phrase: str, evidence_for_obfuscation: str,
                 evidence_for_genuine: str) -> JargonFlag:
    """Run one jargon instance through the hypothesis protocol.

    Both hypotheses are tested against discriminating evidence. When the
    evidence cannot distinguish them, the honest finding is
    insufficient-evidence — never a verdict.
    """
    has_obf = bool(evidence_for_obfuscation.strip())
    has_gen = bool(evidence_for_genuine.strip())
    if has_obf and not has_gen:
        return JargonFlag(phrase, H_OBFUSCATION, evidence_for_obfuscation)
    if has_gen and not has_obf:
        return JargonFlag(phrase, H_GENUINE, evidence_for_genuine)
    if has_obf and has_gen:
        return JargonFlag(
            phrase, H_BOTH,
            f"for obfuscation: {evidence_for_obfuscation}; "
            f"for genuine: {evidence_for_genuine}",
        )
    return JargonFlag(phrase, H_INSUFFICIENT, "no discriminating evidence yet")


def handoff_seeds(brief: ProbeBrief) -> list[str]:
    """HANDOFF stage: 2-3 Take seeds for the kernel's Diverge phase."""
    if not (2 <= len(brief.take_seeds) <= 3):
        raise OverlayError(
            f"Handoff must produce 2-3 Take seeds, got {len(brief.take_seeds)}."
        )
    return list(brief.take_seeds)
