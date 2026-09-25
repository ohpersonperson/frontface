"""Engine: LLM backend interface and the pressure-test runner.

The runner is provider-agnostic: any model that can follow the protocol
prompt works. Backends are swappable — see backends.py. The runner:

1. Builds the user message from the reasoning-in-progress.
2. Calls the backend.
3. Parses the model's JSON (fences tolerated).
4. Normalizes: triggers must have fired, assumptions classified, collisions
   restricted to load-bearing assumptions, the countermodel checked by the
   steelman heuristics, demotions derived from broken assumptions.
5. Returns a normalized record dict the caller can render with
   record.CollisionRecord.

No network happens here; the backend decides how the call is made.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .protocol import (
    SYSTEM_PROMPT,
    Assumption,
    CollisionResult,
    Countermodel,
    ProtocolError,
    apply_demotions,
)
from .record import CollisionRecord
from .steelman import check_countermodel
from .triggers import TriggerEvaluation


class EngineError(RuntimeError):
    """The model call failed or returned an unreadable record."""


@runtime_checkable
class LLMBackend(Protocol):
    """Anything that can take (system, user) and return raw model text."""

    name: str

    def complete(self, system: str, user: str) -> str: ...


@dataclass
class ReasoningInput:
    """The reasoning-in-progress to pressure-test."""

    conclusion: str
    reasoning: str
    evidence: list[str]
    stated_confidence: int | None = None
    triggers: list[str] | None = None


def build_user_message(inp: ReasoningInput) -> str:
    parts = [f"CONCLUSION:\n{inp.conclusion}", f"REASONING:\n{inp.reasoning}"]
    if inp.evidence:
        parts.append("EVIDENCE:\n" + "\n".join(f"- {e}" for e in inp.evidence))
    if inp.stated_confidence is not None:
        parts.append(f"STATED CONFIDENCE: {inp.stated_confidence}/100")
    if inp.triggers:
        parts.append("TRIGGERS CLAIMED: " + ", ".join(inp.triggers))
    return "\n\n".join(parts)


def parse_model_json(raw: str) -> dict:
    """Extract the JSON object from model output; fences tolerated."""
    text = raw.strip()
    fenced = text.split("```")
    body = fenced[1] if len(fenced) >= 3 else text
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        raise EngineError(
            "The engine did not return a collision record. "
            "Try tighter reasoning or a larger model."
        )
    try:
        return json.loads(body[start: end + 1])
    except json.JSONDecodeError as exc:
        raise EngineError(f"The engine returned unreadable JSON: {exc}") from exc


def normalize(inp: ReasoningInput, model: dict) -> dict:
    """Normalize raw model output into a validated record dict."""
    if model.get("stand_down"):
        return {"stand_down": True, "report": "No thresholds tripped. Standing down."}

    triggers = TriggerEvaluation(tripped=model.get("triggers", []))
    if not triggers.fires:
        raise EngineError(
            "The engine returned no tripped triggers. A controller that always "
            "fires is noise — the run is invalid."
        )

    # Countermodel + steelman check: a weak countermodel fails the run.
    cm_text = model.get("countermodel", "")
    report = check_countermodel(cm_text, inp.conclusion)
    if not report.ok:
        raise EngineError(
            "The engine's countermodel failed the steelman check "
            f"({report.strength}): {'; '.join(report.flags)}. "
            "The collision would be theater; the run is invalid."
        )
    countermodel = {
        "text": cm_text,
        "strength": report.strength,
        "flags": report.flags,
    }

    assumptions = []
    for a in model.get("assumptions", []):
        try:
            assumptions.append({"text": a["text"], "kind": a["kind"]})
        except KeyError as exc:
            raise EngineError(f"Malformed assumption entry: {a!r} ({exc})") from exc
    load_bearing_texts = {a["text"] for a in assumptions if a["kind"] == "load-bearing"}

    collisions = []
    for c in model.get("collisions", []):
        if c.get("assumption") not in load_bearing_texts:
            raise EngineError(
                f"Collision targets non-load-bearing assumption: {c.get('assumption')!r}. "
                "Only load-bearing assumptions change conclusions."
            )
        collisions.append(c)

    broken = [c for c in collisions if c.get("result") == "broken"]
    demotions = (
        [f"{inp.conclusion} — demoted to hypothesis pending new evidence"]
        if broken
        else list(model.get("demotions", []))
    )

    before = model.get("confidence_before", inp.stated_confidence or 0)
    after = model.get("confidence_after", before)
    for name, value in (("confidence_before", before), ("confidence_after", after)):
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise EngineError(f"{name} must be an int 0-100, got {value!r}")

    return {
        "stand_down": False,
        "triggers": triggers.tripped,
        "countermodel": countermodel,
        "assumptions": assumptions,
        "collisions": collisions,
        "confidence_before": before,
        "confidence_after": after,
        "confidence_delta": after - before,
        "demotions": demotions,
        "surprise": model.get("surprise", ""),
    }


@dataclass
class RunResult:
    ok: bool
    record: dict | None = None
    error: str | None = None


def run(inp: ReasoningInput, backend: LLMBackend) -> RunResult:
    """Run one pressure test against a backend. Never loops."""
    user = build_user_message(inp)
    try:
        raw = backend.complete(SYSTEM_PROMPT, user)
    except Exception as exc:  # backend errors surface as engine errors
        return RunResult(ok=False, error=f"Backend {backend.name} failed: {exc}")
    try:
        model = parse_model_json(raw)
        record = normalize(inp, model)
    except (EngineError, ProtocolError) as exc:
        return RunResult(ok=False, error=str(exc))
    return RunResult(ok=True, record=record)


def to_collision_record(rec: dict) -> CollisionRecord:
    """Convert a normalized record dict into a renderable CollisionRecord."""
    cm = rec["countermodel"]
    return CollisionRecord(
        triggers=TriggerEvaluation(tripped=rec["triggers"]),
        countermodel=Countermodel(
            text=cm["text"], strength=cm["strength"], flags=cm["flags"]
        ),
        assumptions=[
            Assumption(text=a["text"], kind=a["kind"]) for a in rec["assumptions"]
        ],
        collisions=[
            CollisionResult(
                assumption=c["assumption"], attack=c["attack"], result=c["result"]
            )
            for c in rec["collisions"]
        ],
        confidence_before=rec["confidence_before"],
        confidence_after=rec["confidence_after"],
        demotions=rec["demotions"],
        surprise=rec["surprise"],
    )
