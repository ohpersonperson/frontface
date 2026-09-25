"""The evidence taxonomy this package uses.

The audit never invented its own evidence tiers — it tracks claims,
states, and corrections, not tagged evidence. Where the audit record
carries evidence items, it uses the ONE authoritative taxonomy shared
across this conversion project:

- `adversarial_ifs` (the interrogation engine, `ifs/` conversion):
  11 tags — 10 core tiers plus overlay-only OBFUSCATION.
- `evasion_audit` (the probe+forge conversion, `probe-forge/`):
  the same 11 tags, vendored with a fork guard.

This module vendors the same set a third time, with the same guard:
`check_matches_engine()` asserts the taxonomies are identical when
`adversarial_ifs` is importable, and skips when it isn't. Three
vendored copies plus two guards is clunkier than one shared
dependency — it is deliberate. Every package in this suite stays
stdlib-only and installable alone; the guards, not imports, keep the
taxonomies from silently forking.

There is no second taxonomy here. There never was one in the skill.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- The authoritative taxonomy (11 tags) -----------------------------------

FACT = "FACT"
OBSERVATION = "OBSERVATION"
CLAIM = "CLAIM"
INFERENCE = "INFERENCE"
ASSUMPTION = "ASSUMPTION"
HYPOTHESIS = "HYPOTHESIS"
REQUIREMENT = "REQUIREMENT"
CONSTRAINT = "CONSTRAINT"
DEPENDENCY = "DEPENDENCY"
UNKNOWN = "UNKNOWN"
# Overlay-only: set only when the evasion probe ran AND the evasion
# hypothesis is supported by discriminating evidence.
OBFUSCATION = "OBFUSCATION"

TAXONOMY: dict[str, str] = {
    FACT: "Directly established, unassailable ground truth.",
    OBSERVATION: "Reported or logged, but not independently verified.",
    CLAIM: "An explicit assertion made by an actor or source.",
    INFERENCE: "A conclusion logically drawn from facts or verified observations.",
    ASSUMPTION: "Presumed true without adequate supporting evidence.",
    HYPOTHESIS: "A proposed explanatory model that still needs stress-testing.",
    REQUIREMENT: "A condition that must be true for a model to hold.",
    CONSTRAINT: "A boundary condition limiting viable outcomes.",
    DEPENDENCY: "An element relying directly on the state of another.",
    UNKNOWN: "A critical variable that cannot presently be determined.",
    OBFUSCATION: (
        # Definition text is identical to adversarial_ifs.evidence on
        # purpose — check_matches_engine() enforces byte-identical
        # definitions so the taxonomies can never silently fork.
        "Evasive maneuver or jargon shield masking responsibility. "
        "Tag ONLY when the evasion-probe overlay is active and the evasion "
        "hypothesis is supported by discriminating evidence."
    ),
}

CORE_TAGS = frozenset(
    {FACT, OBSERVATION, CLAIM, INFERENCE, ASSUMPTION, HYPOTHESIS,
     REQUIREMENT, CONSTRAINT, DEPENDENCY, UNKNOWN}
)


class EvidenceError(ValueError):
    """Raised when an evidence item breaks the taxonomy rules."""


@dataclass(frozen=True)
class EvidenceItem:
    """One tagged input to the audit."""

    text: str
    tag: str

    def __post_init__(self) -> None:
        tag = self.tag.strip().upper()
        if tag not in TAXONOMY:
            raise EvidenceError(
                f"Unknown evidence tag {self.tag!r}. "
                f"Valid tags: {', '.join(sorted(TAXONOMY))}."
            )
        if not self.text.strip():
            raise EvidenceError("Evidence item text must not be empty.")


def normalize_tag(tag: str, *, probe_ran: bool = False) -> str:
    """Validate and normalize a tag. OBFUSCATION needs the probe.

    The audit does not run the evasion probe itself. If a record claims
    OBFUSCATION, the caller must pass probe_ran=True — meaning the probe
    ran elsewhere and H-obfuscation was supported by discriminating
    evidence. Suspected-but-untested evasion stays CLAIM.
    """
    normalized = tag.strip().upper()
    if normalized not in TAXONOMY:
        raise EvidenceError(f"Unknown evidence tag {tag!r}.")
    if normalized == OBFUSCATION and not probe_ran:
        raise EvidenceError(
            "OBFUSCATION is overlay-only: it may be tagged only when the "
            "evasion probe ran and H-obfuscation is supported by "
            "discriminating evidence. Use CLAIM with a hypothesis marker "
            "for suspected-but-untested evasion."
        )
    return normalized


def check_matches_engine() -> str:
    """Assert this taxonomy matches adversarial_ifs' — guard against forks.

    Returns "matches" on success. Skips (returns "skipped: adversarial_ifs
    not importable") when the sibling package isn't on the path — the
    vendored copy above remains authoritative either way.
    """
    try:
        import adversarial_ifs.evidence as engine_evidence
    except ImportError:
        return "skipped: adversarial_ifs not importable"
    ours = set(TAXONOMY)
    theirs = set(engine_evidence.TAXONOMY)
    if ours != theirs:
        raise EvidenceError(
            "Taxonomy fork detected: postmo and adversarial_ifs "
            f"disagree. Only here: {sorted(ours - theirs)}; "
            f"only in engine: {sorted(theirs - ours)}. "
            "Reconcile before shipping."
        )
    for tag in ours:
        if TAXONOMY[tag] != engine_evidence.TAXONOMY[tag]:
            raise EvidenceError(
                f"Taxonomy fork detected: definition of {tag} differs "
                "between postmo and adversarial_ifs. Reconcile "
                "before shipping."
            )
    return "matches"


def tag_list() -> list[str]:
    """All valid tags, in canonical order."""
    return list(TAXONOMY)
