"""The execution state machine: the one codeable core of Flashy.

States: LOCKED -> PLANNING -> EXECUTING -> VERIFYING -> DONE, with BLOCKED
reachable from EXECUTING or VERIFYING. The rules are the point — they are
what stops a long task from quietly degrading into "here's a starting
point":

- VERIFYING -> DONE is forbidden unless every Quality Gate box is checked.
- EXECUTING -> PLANNING is forbidden without an explicit, user-driven
  scope change. Silent re-planning is how objectives get replaced.
- BLOCKED -> EXECUTING is forbidden until a checkpoint has been emitted.
  A blocked session that resumes with no checkpoint is a session that
  forgot where it was.
- DONE is terminal. Nothing transitions out of DONE.
"""

from __future__ import annotations

LOCKED = "LOCKED"
PLANNING = "PLANNING"
EXECUTING = "EXECUTING"
VERIFYING = "VERIFYING"
DONE = "DONE"
BLOCKED = "BLOCKED"

STATES = (LOCKED, PLANNING, EXECUTING, VERIFYING, DONE, BLOCKED)

_ALLOWED = {
    LOCKED: {PLANNING},
    PLANNING: {EXECUTING},
    EXECUTING: {VERIFYING, BLOCKED, PLANNING},
    VERIFYING: {DONE, EXECUTING, BLOCKED},
    BLOCKED: {EXECUTING},
    DONE: set(),
}


class TransitionError(ValueError):
    """An illegal state transition was attempted."""


class ExecutionStateMachine:
    """Tracks one task's execution state and enforces the transition rules."""

    def __init__(self, objective: str) -> None:
        if not objective.strip():
            raise TransitionError("An execution state machine needs a locked objective.")
        self.objective = objective
        self.state = LOCKED
        self.history: list[tuple[str, str]] = [(LOCKED, "objective locked")]
        self._checkpoint_emitted = False
        self._block_reason = ""

    def transition(self, target: str, *, scope_change: bool = False,
                   quality_gate: object | None = None) -> str:
        """Move to a new state, enforcing the rules. Returns the new state."""
        if target not in STATES:
            raise TransitionError(f"Unknown state: {target!r}")
        if target not in _ALLOWED[self.state]:
            raise TransitionError(
                f"Illegal transition: {self.state} -> {target}. "
                f"Allowed: {sorted(_ALLOWED[self.state]) or 'none (terminal)'}."
            )
        if self.state == EXECUTING and target == PLANNING and not scope_change:
            raise TransitionError(
                "EXECUTING -> PLANNING requires an explicit user-driven scope "
                "change (scope_change=True). Silent re-planning is how the "
                "objective gets replaced."
            )
        if self.state == VERIFYING and target == DONE:
            gate = quality_gate
            if gate is None or not gate.all_checked():
                missing = (
                    gate.missing() if gate is not None else ["no quality gate supplied"]
                )
                raise TransitionError(
                    "VERIFYING -> DONE requires every Quality Gate box checked. "
                    f"Missing: {missing}."
                )
        if self.state == BLOCKED and target == EXECUTING:
            if not self._checkpoint_emitted:
                raise TransitionError(
                    "BLOCKED -> EXECUTING requires a checkpoint to have been "
                    "emitted first. Call emit_checkpoint() (see checkpoints.py)."
                )
            self._checkpoint_emitted = False  # checkpoint consumed by the resume

        reason = ""
        if target == BLOCKED:
            reason = "blocked"
        self.state = target
        self.history.append((target, reason))
        return self.state

    def block(self, reason: str) -> str:
        """Enter BLOCKED with a recorded reason."""
        if not reason.strip():
            raise TransitionError("Blocking requires a stated reason.")
        self._block_reason = reason
        return self.transition(BLOCKED)

    def emit_checkpoint(self) -> None:
        """Record that a checkpoint was emitted (see checkpoints.py).

        The checkpoint content itself lives in checkpoints.py; the machine
        only tracks that one was emitted, which unblocks BLOCKED -> EXECUTING.
        """
        self._checkpoint_emitted = True
        self.history.append((self.state, "checkpoint emitted"))

    @property
    def block_reason(self) -> str:
        return self._block_reason

    @property
    def is_terminal(self) -> bool:
        return self.state == DONE
