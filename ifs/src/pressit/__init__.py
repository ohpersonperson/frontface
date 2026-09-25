"""pressit — front-facing conversion of the IFS interrogation engine.

IFS = Iterative Field Synthesis: structured adversarial interrogation of
contradictory or uncertain fields. See README.md for the plain-language
version. See CHANGELOG.md for what was decoupled from the original skill.
"""

from . import artifact, backends, engine, evidence, overlay, protocol
from .artifact import (
    StateArtifact, Take, Collision, Synthesis, PriorKeyEvaluation,
    slugify_field, render, render_frontmatter, check_sections, load_prior,
)
from .backends import StubBackend, OpenRouterBackend, OllamaBackend
from .engine import LLMBackend, RunResult, build_user_message, parse_model_json, normalize, run
from .evidence import EvidenceItem, TAXONOMY, normalize_tag, EvidenceError
from .overlay import (
    ProbeBrief, JargonFlag, ground, probe_jargon, handoff_seeds,
    H_OBFUSCATION, H_GENUINE, H_BOTH, H_INSUFFICIENT,
)
from .protocol import (
    SYSTEM_PROMPT, FieldInput, KeyDraft, ProtocolError,
    required_collision_pairs, validate_keys,
    STANDARD, SYSTEMIC, STRESS_TEST, ADJUDICATION,
)

__version__ = "1.0.0"
__all__ = [
    "artifact", "backends", "engine", "evidence", "overlay", "protocol",
    "StateArtifact", "Take", "Collision", "Synthesis", "PriorKeyEvaluation",
    "slugify_field", "render", "render_frontmatter", "check_sections", "load_prior",
    "StubBackend", "OpenRouterBackend", "OllamaBackend",
    "LLMBackend", "RunResult", "build_user_message", "parse_model_json",
    "normalize", "run",
    "EvidenceItem", "TAXONOMY", "normalize_tag", "EvidenceError",
    "ProbeBrief", "JargonFlag", "ground", "probe_jargon", "handoff_seeds",
    "H_OBFUSCATION", "H_GENUINE", "H_BOTH", "H_INSUFFICIENT",
    "SYSTEM_PROMPT", "FieldInput", "KeyDraft", "ProtocolError",
    "required_collision_pairs", "validate_keys",
    "STANDARD", "SYSTEMIC", "STRESS_TEST", "ADJUDICATION",
]
