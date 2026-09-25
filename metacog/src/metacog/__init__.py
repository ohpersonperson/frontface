"""metacog — front-facing conversion of the metacog skill.

A five-step reasoning pressure test: check whether it is worth firing at
all (trigger thresholds), steelman the strongest countermodel, isolate
load-bearing assumptions, collide the countermodel against each one, and
revise confidence with a before→after delta.

Core invariant: confidence and correctness are independent variables.
See README.md for the plain-language version. See CHANGELOG.md for what
was decoupled from the original skill.
"""

from . import backends, engine, protocol, record, steelman, triggers
from .backends import StubBackend, OpenRouterBackend, OllamaBackend
from .engine import (
    LLMBackend, RunResult, ReasoningInput, build_user_message,
    parse_model_json, normalize, run, to_collision_record,
)
from .protocol import (
    SYSTEM_PROMPT, Countermodel, Assumption, CollisionResult,
    ConfidenceRevision, ProtocolError, apply_demotions,
    LOAD_BEARING, STRUCTURAL, SURVIVES, WEAKENED, BROKEN,
)
from .record import CollisionRecord, RecordError
from .steelman import SteelmanReport, check_countermodel
from .triggers import TriggerEvaluation, TriggerError, TRIGGERS

__version__ = "1.0.0"
__all__ = [
    "backends", "engine", "protocol", "record", "steelman", "triggers",
    "StubBackend", "OpenRouterBackend", "OllamaBackend",
    "LLMBackend", "RunResult", "ReasoningInput", "build_user_message",
    "parse_model_json", "normalize", "run", "to_collision_record",
    "SYSTEM_PROMPT", "Countermodel", "Assumption", "CollisionResult",
    "ConfidenceRevision", "ProtocolError", "apply_demotions",
    "LOAD_BEARING", "STRUCTURAL", "SURVIVES", "WEAKENED", "BROKEN",
    "CollisionRecord", "RecordError",
    "SteelmanReport", "check_countermodel",
    "TriggerEvaluation", "TriggerError", "TRIGGERS",
]
