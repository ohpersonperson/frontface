"""The authoritative evidence taxonomy for this package.

Lineage: the interrogation engine (`adversarial_ifs`, in the sibling
`ifs/` conversion) defines an 11-tag taxonomy — 10 core tiers plus one
overlay-only tag (OBFUSCATION). field-forge shipped its own 8-tier list.
This module is the ONE authoritative mapping: field-forge's 8 tiers map
1:1 onto the engine's taxonomy, and the 3 tiers the forge never named
(HYPOTHESIS, REQUIREMENT, DEPENDENCY) are documented as recognized —
not as a second taxonomy.

The authoritative set is vendored here (with the lineage note above) so
this package stays standalone, stdlib-only, with no path dependency on
its sibling. `check_matches_engine()` guards against silent forks: if
`adversarial_ifs` is importable, it asserts the two taxonomies are
identical; if it isn't, the check skips and the vendored copy stands.
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
        # definitions so the two taxonomies can never silently fork.
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

    The probe-run requirement is the taxonomy-level twin of the
    hypothesis gate in `hypotheses.py`: the tag may exist on paper,
    but it may only be *used* when H-obfuscation was actually supported.
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


# --- The field-forge reconciliation ------------------------------------------
#
# field-forge's 8-tier list (from its SKILL.md), mapped onto the
# authoritative taxonomy. Every forge tier maps 1:1 — no renames, no
# splits. The 3 tiers the forge never named are listed as RECOGNIZED:
# valid tags the forge simply didn't use, now available everywhere.
#
#   forge FACT        -> FACT
#   forge OBSERVATION -> OBSERVATION
#   forge CLAIM       -> CLAIM
#   forge OBFUSCATION -> OBFUSCATION (same overlay-only rule)
#   forge INFERENCE   -> INFERENCE
#   forge ASSUMPTION  -> ASSUMPTION
#   forge CONSTRAINT  -> CONSTRAINT
#   forge UNKNOWN     -> UNKNOWN
#   (not named by forge) HYPOTHESIS, REQUIREMENT, DEPENDENCY -> RECOGNIZED

FORGE_TIERS = frozenset(
    {"FACT", "OBSERVATION", "CLAIM", "OBFUSCATION", "INFERENCE",
     "ASSUMPTION", "CONSTRAINT", "UNKNOWN"}
)

FORGE_MISSING = frozenset({"HYPOTHESIS", "REQUIREMENT", "DEPENDENCY"})


def forge_mapping_table() -> str:
    """The reconciliation, as a human-readable table."""
    lines = [
        "| field-forge 8-tier | authoritative tag | status |",
        "|--------------------|-------------------|--------|",
    ]
    for tier in sorted(FORGE_TIERS):
        lines.append(f"| {tier} | {tier} | 1:1 map |")
    for tier in sorted(FORGE_MISSING):
        lines.append(f"| (not named) | {tier} | recognized |")
    return "\n".join(lines)


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
            "Taxonomy fork detected: fairit and adversarial_ifs "
            f"disagree. Only here: {sorted(ours - theirs)}; "
            f"only in engine: {sorted(theirs - ours)}. "
            "Reconcile before shipping."
        )
    for tag in ours:
        if TAXONOMY[tag] != engine_evidence.TAXONOMY[tag]:
            raise EvidenceError(
                f"Taxonomy fork detected: definition of {tag} differs "
                "between fairit and adversarial_ifs. Reconcile "
                "before shipping."
            )
    return "matches"


def tag_list() -> list[str]:
    """All valid tags, in canonical order."""
    return list(TAXONOMY)
