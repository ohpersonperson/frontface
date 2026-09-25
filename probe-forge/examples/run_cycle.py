"""Deterministic end-to-end demo: ground -> probe -> tag -> brief.

No model, no network. Drives the fairit library through the full
overlay cycle on the vendor-memo scenario and prints the rendered brief.

Usage:
    PYTHONPATH=src python3 examples/run_cycle.py
"""

import sys

sys.path.insert(0, "src")

from fairit import (
    AuditBrief,
    Correction,
    DiscriminatingEvidence,
    GroundMap,
    HeldTension,
    HypothesisRecord,
    Mechanism,
    PersonState,
    evidence_tag_for,
    scan_and_test,
)

MEMO = (
    "Regarding the Q3 deliverables: mistakes were made in the scoping "
    "phase. We're going to circle back with stakeholders and leverage "
    "our learnings going forward. The team remains committed to excellence."
)

EVIDENCE = {
    "mistakes were made": (
        "the passive phrasing names no actor; internal emails name the PM "
        "who cut scoping short",
        "",
    ),
    "circle back": (
        "used to end the paragraph about the miss without giving a new date",
        "",
    ),
    "going forward": ("", ""),
}


def main() -> None:
    ground = GroundMap(
        tensions=[
            HeldTension(
                "The contract promised delivery September 1. "
                "Nothing was delivered by October."
            ),
            HeldTension(
                "The memo says the team is committed to excellence. "
                "No named person takes responsibility for the miss."
            ),
        ],
        person_states=[
            PersonState("2026-08-15", "vendor PM", "assuring: 'on track for September'"),
            PersonState("2026-10-03", "vendor PM", "deflecting: memo issued, no new date"),
        ],
        corrections=[
            Correction("core-claim", "first said scoping was complete; now says it failed"),
        ],
    )

    flags = scan_and_test(MEMO, EVIDENCE)
    for flag in flags:
        print(f"[{flag.dialect}] {flag.phrase!r} -> {flag.record.verdict} "
              f"-> tag {evidence_tag_for(flag.record)}")
    print()

    brief = AuditBrief(
        case_name="vendor Q3 delivery miss",
        ground=ground,
        records=[f.record for f in flags],
        seeds=[
            "The vendor is managing the relationship, not the delivery: "
            "language erases actors exactly where accountability would attach.",
            "The 'learnings' frame converts a missed contract into process "
            "improvement — watch whether a new date ever appears.",
        ],
    )
    print(brief.render())


if __name__ == "__main__":
    main()
