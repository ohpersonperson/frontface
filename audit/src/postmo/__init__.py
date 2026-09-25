"""postmo — hold a messy situation without resolving it.

Five audit disciplines, enforced as a linter where they're mechanical
and as explicit operator protocol where they need judgment:

1. Hold contradictions as contradictions (parallel sentences, never "X, but Y").
2. Track people as time-indexed states, never categorical verdicts.
3. Type every correction: detail vs core-claim.
4. Never supply motive or causality the teller didn't state.
5. Self-check every output for softened threat language, supplied
   generous interpretations, dropped contradictions, resolved ambivalence.

Two modes: direct audit (the headline — "don't resolve this, just hold
it", no engine needed) and overlay on the interrogation engine's
Decompose/Collide phases. Either way the canonical artifact is the
audit record: full structured data the next session can load, with
timestamps. The audit never resolves — the record schema rejects
synthesis/resolution/verdict sections.
"""

from .disciplines import DISCIPLINES, D1, D2, D3, D4, D5, discipline_name
from .evidence import (
    EvidenceError, EvidenceItem, check_matches_engine, normalize_tag, tag_list,
)
from .overlay import NEVER, attachment_for, describe_contract
from .record import (
    PROTOCOL, AuditRecord, DisciplineEntry, RecordError, check_stand_down, parse,
    utc_now,
)
from .scans import (
    Correction, CorrectionCandidate, HeldTension, MotiveFlag, PersonState,
    ScanError, ScanReport, SofteningFlag, VerdictWordHit,
    detect_softening, detect_supplied_motive, find_correction_candidates,
    find_subordinators, find_verdict_words, scan_text,
)

__all__ = [
    "DISCIPLINES", "D1", "D2", "D3", "D4", "D5", "discipline_name",
    "EvidenceError", "EvidenceItem", "check_matches_engine",
    "normalize_tag", "tag_list",
    "NEVER", "attachment_for", "describe_contract",
    "PROTOCOL", "AuditRecord", "DisciplineEntry", "RecordError",
    "check_stand_down", "parse", "utc_now",
    "Correction", "CorrectionCandidate", "HeldTension", "MotiveFlag",
    "PersonState", "ScanError", "ScanReport", "SofteningFlag",
    "VerdictWordHit", "detect_softening", "detect_supplied_motive",
    "find_correction_candidates", "find_subordinators", "find_verdict_words",
    "scan_text",
]
