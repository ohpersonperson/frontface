"""The five-step pressure-test protocol: sequence, data shapes, and the
prompt text that drives an LLM backend.

Steps run in order and are never reordered — evaluating before colliding
is the most common failure mode (you polish claims that should have died).

1. Trigger Thresholds — see triggers.py; the controller fires only when a
   threshold trips.
2. Strongest Countermodel — steelman only; checked by steelman.py.
3. Load-Bearing Assumptions — only load-bearing ones go to collision.
4. Collision — countermodel vs. each load-bearing assumption: one of
   SURVIVES / WEAKENED / BROKEN. Contradictions held in parallel
   non-subordinating sentences; the surprise check proves real friction.
5. Confidence Revision — before→after per assumption and overall. A broken
   load-bearing assumption demotes the conclusion to a hypothesis pending
   new evidence.

Core invariant: confidence and correctness are independent variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Constants ---------------------------------------------------------------

PROTOCOL_NAME = "metacog"
PROTOCOL_VERSION = "1.0"
PROTOCOL_LINEAGE = (
    "Front-facing conversion of the metacog skill v2.0 (Ryan's skill-suite, "
    "MIT). Mechanism preserved; name decoupled for stranger legibility."
)

LOAD_BEARING = "load-bearing"
STRUCTURAL = "structural"
ASSUMPTION_KINDS = (LOAD_BEARING, STRUCTURAL)

SURVIVES = "survives"
WEAKENED = "weakened"
BROKEN = "broken"
COLLISION_RESULTS = (SURVIVES, WEAKENED, BROKEN)


class ProtocolError(ValueError):
    """The protocol was violated: bad ordering, bad classification, bad math."""


# --- Data shapes -------------------------------------------------------------


@dataclass
class Countermodel:
    text: str
    strength: str = "strong"
    flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.strength not in ("strong", "weak", "unopposed"):
            raise ProtocolError(f"Bad countermodel strength: {self.strength!r}")
        if self.strength == "weak":
            raise ProtocolError(
                "A weak countermodel makes the collision theater. "
                f"Flags: {self.flags}. Rebuild the steelman or record 'unopposed'."
            )


@dataclass
class Assumption:
    text: str
    kind: str

    def __post_init__(self) -> None:
        if self.kind not in ASSUMPTION_KINDS:
            raise ProtocolError(
                f"Assumption kind must be one of {ASSUMPTION_KINDS}, got {self.kind!r}"
            )

    @property
    def load_bearing(self) -> bool:
        return self.kind == LOAD_BEARING


@dataclass
class CollisionResult:
    assumption: str
    attack: str
    result: str

    def __post_init__(self) -> None:
        if self.result not in COLLISION_RESULTS:
            raise ProtocolError(
                f"Collision result must be one of {COLLISION_RESULTS}, got {self.result!r}"
            )
        if not self.attack.strip():
            raise ProtocolError("Collision requires a stated attack, not just a verdict.")


@dataclass
class ConfidenceRevision:
    before: int
    after: int
    per_assumption: dict[str, tuple[int, int]] = field(default_factory=dict)
    demotions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name, value in (("before", self.before), ("after", self.after)):
            if not 0 <= value <= 100:
                raise ProtocolError(f"Confidence {name} must be 0-100, got {value!r}")

    @property
    def delta(self) -> int:
        return self.after - self.before


def apply_demotions(conclusion: str, collisions: list[CollisionResult]) -> list[str]:
    """A broken load-bearing assumption does not merely lower confidence —
    it demotes the conclusion to a hypothesis pending new evidence."""
    if any(c.result == BROKEN for c in collisions):
        return [f"{conclusion} — demoted to hypothesis pending new evidence"]
    return []


# --- The system prompt -------------------------------------------------------

SYSTEM_PROMPT = """You are a reasoning pressure-tester. You never originate analysis; you interrogate reasoning-in-progress. Core invariant: confidence and correctness are independent variables — you interrogate the gap between them.

Execute the five steps IN ORDER. Do not skip. Do not reorder — evaluating before colliding polishes claims that should have died.

STEP 1 — TRIGGER THRESHOLDS
Fire only if at least one trips: stakes (hard-to-reverse decision or high-consequence claim); confidence-without-evidence (confidence stated above what evidence supports); contradiction-present (credible counter-take exists, uncollided); premature-convergence (fast convergence, single unchallenged take, no alternative generated and rejected); explicit-invocation (user asked). If none trips, output {"stand_down": true} and stop.

STEP 2 — STRONGEST COUNTERMODEL
Build the strongest internally-coherent case AGAINST the current conclusion. Steelman only — no strawmen, no "someone might disagree." Name premises, name evidence, name the mechanism. If you cannot build a strong countermodel, say so explicitly — that is a finding, not a failure.

STEP 3 — LOAD-BEARING ASSUMPTIONS
List the assumptions the conclusion depends on. Mark each "load-bearing" (if false, the conclusion falls) or "structural" (supports it, but the conclusion survives without it). Only load-bearing assumptions go to collision.

STEP 4 — COLLISION
Collide the countermodel against each load-bearing assumption, one at a time. State the assumption, the countermodel's attack, and the result: survives / weakened / broken. Hold contradictions in parallel non-subordinating sentences ("X is true. Y is also true." — never "X, however Y"). SURPRISE CHECK: if the collision produced nothing neither side contained alone, it was not a real collision — run it again, harder.

STEP 5 — CONFIDENCE REVISION
Revise confidence: report before→after per load-bearing assumption and overall. The delta is the output. A broken load-bearing assumption demotes the conclusion to a hypothesis pending new evidence. Distinguish "I am less confident" (self-report) from "the assumption broke under the countermodel" (finding). Report findings.

Output JSON: {"triggers": [...], "countermodel": "...", "assumptions": [{"text": "...", "kind": "load-bearing|structural"}], "collisions": [{"assumption": "...", "attack": "...", "result": "survives|weakened|broken"}], "confidence_before": N, "confidence_after": N, "demotions": [...], "surprise": "..."}.
"""
