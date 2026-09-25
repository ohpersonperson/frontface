"""flashy — front-facing conversion of the flashy execution skill.

Persistent execution discipline for long tasks: lock the objective,
expand it into milestones, track live state, detect drift and artificial
stopping points, checkpoint honestly on genuine limits, and gate
completion on a quality checklist. A draft is not a delivery.

No prerequisites. The mechanism is the whole product.
See README.md for the plain-language version. See CHANGELOG.md for what
was decoupled from the original skill.
"""

from . import checkpoints, detectors, quality_gate, session, state_machine
from .checkpoints import (
    Checkpoint, CheckpointError, make_resume_token, parse_resume_token,
)
from .detectors import (
    ARTIFICIAL_STOP_PHRASES, PERMISSION_PHRASES, DRIFT_QUESTIONS,
    DRIFT_CORRECTION, HIGH, MEDIUM, LOW, CONFIDENCE_LEVELS,
    CONFIDENCE_GUIDANCE, DetectorError, detect_artificial_stop,
    asks_permission_to_continue, should_pause, is_implementation_changing,
)
from .quality_gate import QualityGate, GateError, GATE_ITEMS
from .session import MissionSession, Milestone
from .state_machine import (
    ExecutionStateMachine, TransitionError,
    LOCKED, PLANNING, EXECUTING, VERIFYING, DONE, BLOCKED,
)

__version__ = "1.0.0"
__all__ = [
    "checkpoints", "detectors", "quality_gate", "session", "state_machine",
    "Checkpoint", "CheckpointError", "make_resume_token", "parse_resume_token",
    "ARTIFICIAL_STOP_PHRASES", "PERMISSION_PHRASES", "DRIFT_QUESTIONS",
    "DRIFT_CORRECTION", "HIGH", "MEDIUM", "LOW", "CONFIDENCE_LEVELS",
    "CONFIDENCE_GUIDANCE", "DetectorError", "detect_artificial_stop",
    "asks_permission_to_continue", "should_pause", "is_implementation_changing",
    "QualityGate", "GateError", "GATE_ITEMS",
    "MissionSession", "Milestone",
    "ExecutionStateMachine", "TransitionError",
    "LOCKED", "PLANNING", "EXECUTING", "VERIFYING", "DONE", "BLOCKED",
]
