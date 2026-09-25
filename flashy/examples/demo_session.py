#!/usr/bin/env python3
"""Drive a Flashy session end to end — no model, no network.

Demonstrates the state machine, milestone tracking, dashboard, the
end-of-response gate, and the Quality Gate, on the debate-simulator build
from the worked example.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from flashy import MissionSession, detect_artificial_stop


def main() -> int:
    session = MissionSession(
        "Deliver a functional, usable, in-browser debate simulator.",
        slug="debate-sim",
        implicit_quality_bar="single HTML file, runs end-to-end with no backend",
        scope_boundaries="no user accounts, no persistence beyond save/resume",
    )
    session.plan(["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"])
    session.start_executing()
    session.risks.append("turn-taking logic could tangle with UI state — keep decoupled")

    for milestone in ["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"]:
        # End-of-response gate: keep going while milestones remain.
        assert session.end_of_response_gate() == "continue", milestone
        session.complete_milestone(milestone)
        print(f"--- after {milestone} ---")
        print(session.dashboard())
        print()

    # Nothing remains: verify, don't declare.
    assert session.end_of_response_gate() == "verify"
    session.begin_verification()

    # A draft tried to sneak through: detect the artificial stop first.
    draft_line = "Here's a starting point — you can expand this for scoring."
    hits = detect_artificial_stop(draft_line)
    print(f"Artificial-stop scan on draft line: {hits or 'clean'}")

    session.gate.check_all()
    session.finish()
    print(f"\nFinal state: {session.machine.state} — {session.gate.status()}")
    print("The user has the finished thing, not a starting point.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
