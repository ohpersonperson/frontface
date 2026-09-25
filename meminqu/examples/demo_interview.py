"""Demo: a full scripted interview cycle against a temporary memory store.

No model, no network. Shows the machinery: domain walk, register
rotation, verbatim capture through memdate, skip handling, and
the completion report.

Run from the meminqu directory of the staging tree::

    PYTHONPATH=../memdate/src:src python3 examples/demo_interview.py
"""

from __future__ import annotations

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STAGING = os.path.dirname(HERE)
MEMDATE_SRC = os.path.join(os.path.dirname(STAGING), "memdate", "src")
for path in (os.path.join(STAGING, "meminqu", "src"), MEMDATE_SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    from meminqu import InterviewSession, Response
    from memdate import MemoryConfig, read_raw
except ImportError:
    sys.exit(
        "Could not import meminqu or memdate.\n"
        "Run from the staging tree with:\n"
        "  PYTHONPATH=../memdate/src:src python3 examples/demo_interview.py"
    )

# Canned Q&A per register — what an operator/model would produce live.
# Keyed by register so each domain draws whatever its planned
# registers are; this is also what makes the rotation visible.
SCRIPT = {
    "direct": (
        "What is the single most important fact in this domain right now?",
        "Dentist appointment Thursday at 2pm. Do not reschedule again.",
    ),
    "reflective": (
        "What does this domain feel like from the inside this week?",
        "Stretched thin but oddly calm. Like the week before a trip.",
    ),
    "structural": (
        "Which part of this domain's system is under the most strain?",
        "The handoff between me and Priya — everything queues there.",
    ),
    "irreverent": (
        "Cut the diplomacy: what is actually going on here?",
        "We are busy performing progress instead of making it.",
    ),
    "sparse": (
        "This domain in one sentence.",
        "Half-built, fully loved, zero deadline.",
    ),
    "temporal": (
        "What changed here since the last time you looked?",
        "Sleep is back to normal for the first time in a month.",
    ),
    "contrastive": (
        "What is not true here, though it might look that way?",
        "It looks like the team is aligned. It is not — three people are quietly job-hunting.",
    ),
}


def main() -> None:
    tmp = tempfile.mkdtemp(prefix="interview-demo-")
    config = MemoryConfig(root=tmp, domains=("personal", "work", "projects"))
    session = InterviewSession(config)

    for domain in session.domains:
        registers = session.start_domain(domain)
        print(f"--- {domain} (registers: {', '.join(registers)})")
        responses = [Response(register, *SCRIPT[register]) for register in registers]
        result = session.submit_answers(domain, responses)
        print(f"    captured -> {result.path} ({result.bytes_written} bytes)")

    # Show one raw file as written.
    print("\n=== personal/raw.md (as captured) ===")
    print(read_raw(config, "personal"))

    print("=== completion report ===")
    print(session.render_report())
    print(f"(demo store left at {tmp})")


if __name__ == "__main__":
    main()
