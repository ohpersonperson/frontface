"""fairit — pre-interrogation ground mapping and evasion testing.

Map the ground (held tensions, time-indexed states, typed corrections),
test evasion hypotheses (never presume them), and hand off 2-3 seed
frames to whatever comes next. The package never collides, adjudicates,
refines, or extracts surprise — it audits and hands off.
"""

from .brief import AuditBrief, BriefError, check_stand_down, parse
from .dialects import DIALECTS, SHIELD_MARKERS, detect_markers
from .evidence import (
    TAXONOMY,
    EvidenceError,
    EvidenceItem,
    check_matches_engine,
    forge_mapping_table,
    normalize_tag,
    tag_list,
)
from .ground import (
    Correction,
    GroundError,
    GroundMap,
    HeldTension,
    PersonState,
    find_subordinators,
)
from .hypotheses import (
    H_BOTH,
    H_GENUINE,
    H_OBFUSCATION,
    INSUFFICIENT_EVIDENCE,
    SUPPORT_STATUSES,
    VERDICTS,
    CategoryPresumptionError,
    DiscriminatingEvidence,
    HypothesisError,
    HypothesisRecord,
    Mechanism,
)
from .overlay import (
    JargonFlag,
    ObfuscatedObject,
    ProbeError,
    evidence_tag_for,
    run_jargon_test,
    scan_and_test,
)

__all__ = [
    "AuditBrief", "BriefError", "check_stand_down", "parse",
    "DIALECTS", "SHIELD_MARKERS", "detect_markers",
    "TAXONOMY", "EvidenceError", "EvidenceItem", "check_matches_engine",
    "forge_mapping_table", "normalize_tag", "tag_list",
    "Correction", "GroundError", "GroundMap", "HeldTension", "PersonState",
    "find_subordinators",
    "H_BOTH", "H_GENUINE", "H_OBFUSCATION", "INSUFFICIENT_EVIDENCE",
    "SUPPORT_STATUSES", "VERDICTS", "CategoryPresumptionError",
    "DiscriminatingEvidence", "HypothesisError", "HypothesisRecord", "Mechanism",
    "JargonFlag", "ObfuscatedObject", "ProbeError", "evidence_tag_for",
    "run_jargon_test", "scan_and_test",
]

__version__ = "1.0.0"
