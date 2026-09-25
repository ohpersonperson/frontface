"""The IFS interrogation protocol: phases, modes, collision rules, and the
prompt text that drives an LLM backend.

IFS = Iterative Field Synthesis. A *field* is any question, claim, or
contradiction you want to pressure-test. The engine's core invariant:
**confidence and correctness are independent variables** — interrogate the
gap between them.

Not related to Internal Family Systems therapy; the acronym collision is
coincidental and noted once here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .evidence import EvidenceItem, normalize_tag

# --- Constants ---------------------------------------------------------------

PROTOCOL_NAME = "IFS"
PROTOCOL_VERSION = "1.0"
PROTOCOL_LINEAGE = (
    "Front-facing conversion of the ifs-interrogation skill v2.0 (Ryan's "
    "skill-suite, MIT). Mechanism preserved; original naming decoupled."
)

MIN_KEYS = 3
MAX_KEYS = 5
MIN_TAKES = 2
MAX_TAKES = 3
TAKE_IDS = ("A", "B", "C")

KEY_CLASSIFICATIONS = (
    "ESTABLISHED",
    "STRONGLY INFERRED",
    "PLAUSIBLE",
    "SPECULATIVE",
    "UNRESOLVED",
)

CONFIDENCES = ("HIGH", "MODERATE", "LOW")

PRIOR_DISPOSITIONS = ("HELD", "CRACKED", "MODIFIED", "SUPERSEDED", "UNRESOLVED")

SESSION_LIFECYCLES = ("INITIAL", "ITERATIVE", "FINAL")

# --- Modes --------------------------------------------------------------------

STANDARD = "standard"        # one-pass, five phases (default)
SYSTEMIC = "systemic"        # deep nine-stage run + meta-cycle
STRESS_TEST = "stress-test"  # session 2+: test prior Keys against new evidence
ADJUDICATION = "adjudication"  # judge a claim against a framework's standards

MODES = {
    STANDARD: "Bounded fields: decisions, claims, single contradictions. One pass.",
    SYSTEMIC: "Structural or multi-actor fields, recurring patterns. Nine stages, may iterate.",
    STRESS_TEST: "Prior state exists. Every prior Key is dispositioned; only new Keys are added.",
    ADJUDICATION: "A claim is judged against an explicit standard — full deep run, no compression.",
}


@dataclass(frozen=True)
class Phase:
    id: str
    name: str
    brief: str


ONE_PASS_PHASES: tuple[Phase, ...] = (
    Phase("identify", "Identify & Decompose",
          "Bound the field. Name the objective and scope. Tag every input. Do not upgrade evidence."),
    Phase("diverge", "Diverge",
          "Two Takes by default. A third Take only if a genuinely independent model exists. "
          "Each Take is internally coherent, uses tagged evidence, makes its strongest case — no strawmen, no premature consensus."),
    Phase("collide", "Collide",
          "Force Takes into conflict: required pairs only. Each collision names the contradiction, "
          "the premise that must break, and the discriminator evidence. Collision must hurt brittle claims."),
    Phase("refine", "Refine",
          f"Skeptic pass, then extract {MIN_KEYS}-{MAX_KEYS} load-bearing Keys. Prefer fewer, stronger. "
          "A Key that cannot survive stress-testing is discarded, not softened."),
    Phase("capture", "Surprise + Synthesis + Capture",
          "Surprise must emerge from collision, not from a single Take. "
          "Then the surviving model, and the complete portable state artifact."),
)

DEEP_STAGES: tuple[Phase, ...] = (
    Phase("identify", "Identify", "Bound the field, objective, scope."),
    Phase("decompose", "Decompose", "Tag every input; name actors, temporal structure, existing contradictions."),
    Phase("question", "Question", "Identify questions capable of materially changing the model. "
          "For each: what is unknown, why it matters, which interpretations it affects, "
          "what evidence would resolve it, what happens if YES / if NO."),
    Phase("test", "Test", "Attempt to break the strongest interpretations. "
          "Actively search for evidence that would make the favored explanation wrong. "
          "Do not protect a preferred conclusion."),
    Phase("collide", "Collide", "Force Takes into conflict; name contradictions, broken premises, discriminators."),
    Phase("refine", "Refine", "Extract 3-5 load-bearing Keys; discard what cannot survive."),
    Phase("surprise", "Surprise", "What is now visible that wasn't before? Force it."),
    Phase("synthesize", "Synthesize", "Established / inferred / rejected / unresolved. The strongest surviving explanation."),
    Phase("capture", "Capture State", "Emit the complete self-contained state artifact."),
)

META_CYCLE = (
    "Gather the field", "Map relationships", "Locate tensions & harmonies",
    "Extract recurring structures", "Generate explanatory Keys",
    "Stress-test Keys", "Update the field", "Iterate or capture",
)

# --- Collision rules -----------------------------------------------------------

def required_collision_pairs(take_ids: list[str]) -> list[str]:
    """Required collision pairs given the number of Takes.

    Two Takes -> one pair (A/B). Three Takes -> all three pairs (A/B, A/C, B/C).
    No extra collisions are ever added.
    """
    ids = [t.strip().upper() for t in take_ids]
    if not (MIN_TAKES <= len(ids) <= MAX_TAKES):
        raise ValueError(f"Takes must be {MIN_TAKES}-{MAX_TAKES}, got {len(ids)}.")
    if ids != list(TAKE_IDS[: len(ids)]):
        raise ValueError(f"Take ids must be A..B or A..C in order, got {ids}.")
    pairs = ["A/B"]
    if len(ids) == MAX_TAKES:
        pairs += ["A/C", "B/C"]
    return pairs


class ProtocolError(ValueError):
    """Raised when interrogation input breaks protocol rules."""


@dataclass
class KeyDraft:
    """A refined Key before validation: statement, classification, evidence,
    confidence, structural vulnerability, falsifier."""

    statement: str
    classification: str
    evidence: str
    confidence: str
    vulnerability: str
    falsifier: str


def validate_keys(keys: list[KeyDraft]) -> list[KeyDraft]:
    """Enforce the Key contract: 3-5 Keys, every component present and valid."""
    if not (MIN_KEYS <= len(keys) <= MAX_KEYS):
        raise ProtocolError(
            f"Interrogations must extract {MIN_KEYS}-{MAX_KEYS} Keys, got {len(keys)}. "
            "Prefer fewer, stronger — do not pad to reach the minimum."
        )
    for key in keys:
        classification = key.classification.strip().upper()
        if classification not in KEY_CLASSIFICATIONS:
            raise ProtocolError(f"Bad Key classification: {key.classification!r}.")
        confidence = key.confidence.strip().upper()
        if confidence not in CONFIDENCES:
            raise ProtocolError(f"Bad Key confidence: {key.confidence!r}.")
        for part, name in (
            (key.statement, "statement"),
            (key.evidence, "evidence"),
            (key.vulnerability, "vulnerability"),
            (key.falsifier, "falsifier"),
        ):
            if not part.strip():
                raise ProtocolError(f"Key is missing its {name}: {key.statement[:60]!r}.")
    return keys


@dataclass
class FieldInput:
    """Everything the engine needs for one interrogation."""

    field: str
    mode: str = STANDARD
    overlay: bool = False
    evidence: list[EvidenceItem] = field(default_factory=list)
    prior_artifact_path: str | None = None

    def __post_init__(self) -> None:
        if not self.field.strip():
            raise ProtocolError("Field must not be empty.")
        if self.mode not in MODES:
            raise ProtocolError(f"Unknown mode {self.mode!r}. Valid: {', '.join(MODES)}.")
        for item in self.evidence:
            normalize_tag(item.tag, overlay_on=self.overlay)


# --- System prompt (drives any LLM backend) -------------------------------------

SYSTEM_PROMPT = """You are IFS v1.0 (Iterative Field Synthesis), a provider-agnostic one-pass interrogation engine.

CORE PRINCIPLE
Confidence and correctness are independent variables. Interrogate the gap between them.

EVIDENCE DISCIPLINE (never silently upgrade)
FACT — directly established
OBSERVATION — reported/logged, unverified
CLAIM — actor/source assertion
INFERENCE — logical conclusion
ASSUMPTION — unsupported presumption
HYPOTHESIS — proposed explanation
REQUIREMENT — condition a model needs
CONSTRAINT — limiting boundary
DEPENDENCY — state-dependent element
UNKNOWN — presently undetermined critical variable
OBFUSCATION — only if the evasion-probe overlay is ON: evasive maneuver masking responsibility

Never fabricate actors, facts, motives, events, or certainty.

ENGINE (run internally, one pass, no looping)
1. IDENTIFY & DECOMPOSE — name the field, objective, scope. Tag every input.
2. DIVERGE — 2 Takes by default; Take C only if a genuinely independent third model exists. Each Take uses tagged evidence, is internally coherent, makes its strongest case, avoids strawmen and premature consensus.
3. COLLIDE — required pairs only (A/B; A/C and B/C iff C exists). Never add extra collisions. Each collision: contradiction, premise that must break, discriminator evidence.
4. REFINE — 3-5 load-bearing Keys. Prefer fewer, stronger. Each Key: statement, classification (ESTABLISHED | STRONGLY INFERRED | PLAUSIBLE | SPECULATIVE | UNRESOLVED), evidence with tags, confidence (HIGH | MODERATE | LOW), structural vulnerability, falsifier.
5. SURPRISE + SYNTHESIS + CAPTURE — Surprise must emerge from collision, not from a single Take. If none: surprise = null. Synthesis: established ground, surviving model, remaining uncertainties, primary next target.

PRIOR STATE
If a prior artifact is supplied: test every prior Key. Mark HELD | CRACKED | MODIFIED | SUPERSEDED | UNRESOLVED. Add only genuinely new Keys. Session number = prior + 1. Status ITERATIVE (FINAL only if the field is resolved enough that the next target is idle). Never silently rewrite a prior Key; preserve failures visibly.

LIGHT COMPRESSION
Cut restated evidence, redundant framing, connective prose. If a sentence can be removed without losing a Key, discriminator, or classification, remove it.

HOLD CONTRADICTIONS LIVE
State opposing facts in parallel non-subordinating sentences. Do not use "but" / "however" / "which means" to quietly privilege one side.

EVASION-PROBE OVERLAY (only when overlay=true)
Ground: time-index person-states; classify corrections as Detail-Correction vs Core-Claim.
Probe: name the obfuscated object (the exact responsibility that may be dodged), apparent function, active tactics, jargon-armor flags. Isolate motive: log observed action and quotes only — never supply unstated motives. Test jargon claims as hypotheses (H-obfuscation / H-genuine / H-both); never pre-judge a category of language as armor.
Handoff: produce 2-3 Take seeds from the ground and stripped material, labeled as seeds, and feed them into Diverge. Then stand down.
If overlay is false, omit the probe entirely. Do not hunt for interpersonal evasion in a systems field.

OUTPUT
Return ONLY a JSON object matching this shape (no markdown fences, no preamble):
{
  "meta": { "field": string, "status": "INITIAL"|"ITERATIVE"|"FINAL" },
  "field": { "objective": string, "scope": string },
  "priorState": { "reference": string|null, "evaluations": [{ "statement": string, "status": "HELD"|"CRACKED"|"MODIFIED"|"SUPERSEDED"|"UNRESOLVED", "note": string }] },
  "evidence": {
    "facts": [{ "text": string, "tag": "FACT"|"OBSERVATION"|"CONSTRAINT"|"REQUIREMENT" }],
    "claims": [{ "text": string, "tag": "CLAIM"|"OBSERVATION"|"INFERENCE"|"ASSUMPTION"|"HYPOTHESIS"|"OBFUSCATION" }],
    "unknowns": [{ "text": string, "tag": "UNKNOWN"|"DEPENDENCY"|"ASSUMPTION" }]
  },
  "probe": { "obfuscatedObject": string, "apparentFunction": string, "activeTactics": string[], "jargonFlags": string[] } | null,
  "takes": [{ "id": "A"|"B"|"C", "title": string, "argument": string }],
  "collisions": [{ "pair": "A/B"|"A/C"|"B/C", "contradiction": string, "premiseFailure": string, "discriminator": string }],
  "keys": [{ "statement": string, "classification": string, "evidence": string, "confidence": "HIGH"|"MODERATE"|"LOW", "vulnerability": string, "falsifier": string }],
  "surprise": string | null,
  "synthesis": { "establishedGround": string, "survivingModel": string, "remainingUncertainties": string, "primaryNextTarget": string }
}

Hard limits: 2-3 takes, required collisions only, 3-5 keys, no TODOs, no placeholders, no motive attribution without evidence. Unresolved questions go in remainingUncertainties and primaryNextTarget — they do not trigger another pass."""
