"""Mission session: the objective, its milestones, and the live dashboard.

A session binds the three codeable pieces together — the state machine,
the quality gate, and checkpoints — around one locked objective. It also
carries the mission dashboard (objective / now / done / next / blockers)
and the end-of-response gate: a response ending is not a task ending.

Mission rule: a draft is not a delivery. Completion is measured by whether
the user actually received the usable thing they asked for.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .checkpoints import Checkpoint, make_resume_token
from .quality_gate import QualityGate
from .state_machine import (
    BLOCKED, DONE, EXECUTING, LOCKED, PLANNING, VERIFYING,
    ExecutionStateMachine, TransitionError,
)

PENDING = "pending"
ACTIVE = "active"
MILESTONE_DONE = "done"
DESCOPED = "descoped"


@dataclass
class Milestone:
    name: str
    status: str = PENDING

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise TransitionError("Milestones need names.")
        if self.status not in (PENDING, ACTIVE, MILESTONE_DONE, DESCOPED):
            raise TransitionError(f"Bad milestone status: {self.status!r}")


class MissionSession:
    """One locked objective, driven through the state machine to DONE."""

    def __init__(self, objective: str, *, slug: str,
                 implicit_quality_bar: str = "",
                 scope_boundaries: str = "") -> None:
        self.machine = ExecutionStateMachine(objective)
        self.slug = slug
        self.implicit_quality_bar = implicit_quality_bar
        self.scope_boundaries = scope_boundaries
        self.milestones: list[Milestone] = []
        self.gate = QualityGate()
        self.constraints: list[str] = []
        self.pending_decisions: list[str] = []
        self.risks: list[str] = []

    # -- planning -----------------------------------------------------------

    def plan(self, milestones: list[str]) -> None:
        """Expand the objective into milestones and enter PLANNING."""
        if self.machine.state != LOCKED:
            raise TransitionError("plan() runs once, from LOCKED.")
        self.milestones = [Milestone(name=m) for m in milestones]
        if self.milestones:
            self.milestones[0].status = ACTIVE
        self.machine.transition(PLANNING)

    def start_executing(self) -> None:
        self.machine.transition(EXECUTING)

    # -- execution ----------------------------------------------------------

    @property
    def current_milestone(self) -> Milestone | None:
        for m in self.milestones:
            if m.status == ACTIVE:
                return m
        return None

    def complete_milestone(self, name: str) -> None:
        """Mark a milestone done and advance to the next pending one."""
        target = next((m for m in self.milestones if m.name == name), None)
        if target is None:
            raise TransitionError(f"Unknown milestone: {name!r}")
        target.status = MILESTONE_DONE
        nxt = next((m for m in self.milestones if m.status == PENDING), None)
        if nxt is not None:
            nxt.status = ACTIVE

    def descope(self, name: str) -> None:
        """Explicit user descope only — milestones never silently shrink."""
        target = next((m for m in self.milestones if m.name == name), None)
        if target is None:
            raise TransitionError(f"Unknown milestone: {name!r}")
        target.status = DESCOPED
        nxt = next((m for m in self.milestones if m.status == PENDING), None)
        if nxt is not None and self.current_milestone is None:
            nxt.status = ACTIVE

    def remaining(self) -> list[str]:
        return [m.name for m in self.milestones
                if m.status in (PENDING, ACTIVE)]

    def completed(self) -> list[str]:
        return [m.name for m in self.milestones if m.status == MILESTONE_DONE]

    # -- dashboard ----------------------------------------------------------

    def dashboard(self) -> str:
        """The compact mission dashboard, refreshed after every milestone."""
        current = self.current_milestone
        lines = [
            f"OBJECTIVE  -> {self.machine.objective}",
            f"NOW        -> {current.name if current else '(none — all milestones resolved)'}",
            f"DONE       -> {', '.join(self.completed()) or '(none yet)'}",
            f"NEXT       -> {self.next_action()}",
            f"BLOCKERS   -> {', '.join(self.pending_decisions) or 'none'}",
        ]
        return "\n".join(lines)

    def next_action(self) -> str:
        current = self.current_milestone
        if current:
            return f"Continue: {current.name}"
        if self.remaining():
            return f"Continue: {self.remaining()[0]}"
        return "Verify against the Quality Gate"

    # -- end-of-response gate -----------------------------------------------

    def end_of_response_gate(self) -> str:
        """A response ending is not a task ending. Returns the verdict:

        - "verify" — no milestones remain; run the Quality Gate.
        - "continue" — useful progress can still be made; keep executing.
        - "checkpoint" — genuinely blocked; emit a checkpoint.
        """
        if self.machine.state == BLOCKED:
            return "checkpoint"
        if not self.remaining():
            return "verify"
        return "continue"

    def checkpoint(self, milestone_index: int) -> Checkpoint:
        """Emit an honest checkpoint for a genuine limit. Never a soft stop."""
        return Checkpoint(
            objective=self.machine.objective,
            done=self.completed(),
            current=self.current_milestone.name if self.current_milestone else "",
            remaining=self.remaining(),
            next_action=self.next_action(),
            resume_token=make_resume_token(self.slug, milestone_index),
            blockers=list(self.pending_decisions),
        )

    # -- verification -------------------------------------------------------

    def begin_verification(self) -> None:
        self.machine.transition(VERIFYING)

    def finish(self) -> None:
        """VERIFYING -> DONE. Raises unless every Quality Gate box is checked."""
        self.machine.transition(DONE, quality_gate=self.gate)
