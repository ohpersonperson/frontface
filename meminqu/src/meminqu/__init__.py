"""meminqu — guided capture interviews for a memory store.

Walks each memory domain, asks questions in deliberately different
registers (direct, reflective, structural, irreverent, sparse,
temporal, contrastive), and captures the answers verbatim into the
domain's raw.md through memdate's pure CAPTURE rules. No
synthesis, no interpretation, no analysis.

Front-facing conversion of the ``meminqu-memory-interrogation`` skill
(Ryan's skill-suite, MIT). The domain list is inherited from the
memdate config — this package declares none of its own.
"""

from .entry import ENTRY_MARKER, Response, answers_preserved_verbatim, format_entry
from .registers import (
    REGISTERS,
    Register,
    RegisterError,
    get_register,
    plan_cycle,
    validate_register_set,
)
from .session import InterviewSession, SessionError

__all__ = [
    "InterviewSession",
    "SessionError",
    "Response",
    "Register",
    "RegisterError",
    "REGISTERS",
    "get_register",
    "plan_cycle",
    "validate_register_set",
    "format_entry",
    "answers_preserved_verbatim",
    "ENTRY_MARKER",
]

__version__ = "1.0.0"
