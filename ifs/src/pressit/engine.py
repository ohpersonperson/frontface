"""Engine: LLM backend interface and the interrogation runner.

The runner is provider-agnostic: any model that can follow the protocol
prompt works. Backends are swappable — see backends.py. The runner:

1. Builds the user message from the field, overlay flag, and prior artifact.
2. Calls the backend.
3. Parses the model's JSON (fences tolerated).
4. Normalizes: takes filtered to A/B/C, collisions restricted to required
   pairs, keys capped at 5, probe dropped when the overlay is off.
5. Returns a normalized artifact dict the caller can render with
   artifact.render().

No network happens here; the backend decides how the call is made.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .protocol import SYSTEM_PROMPT, FieldInput, required_collision_pairs


class EngineError(RuntimeError):
    """The model call failed or returned an unreadable artifact."""


@runtime_checkable
class LLMBackend(Protocol):
    """Anything that can take (system, user) and return raw model text."""

    name: str

    def complete(self, system: str, user: str) -> str: ...


def build_user_message(field_text: str, *, overlay: bool,
                       prior_json: str | None) -> str:
    parts = [f"OVERLAY: {'ON' if overlay else 'OFF'}"]
    if prior_json:
        parts.append(
            "PRIOR ARTIFACT (test these Keys, do not inherit Takes as authority):\n"
            + prior_json
        )
    else:
        parts.append("PRIOR ARTIFACT: none")
    parts.append(f"FIELD:\n{field_text}")
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
            "The engine did not return a state artifact. "
            "Try a tighter field or a larger model."
        )
    try:
        return json.loads(body[start: end + 1])
    except json.JSONDecodeError as exc:
        raise EngineError(f"The engine returned unreadable JSON: {exc}") from exc


def normalize(field_text: str, *, overlay: bool, prior_session: int | None,
              model: dict) -> dict:
    """Normalize raw model output into a validated artifact dict.

    Enforces the hard limits in code: valid Take ids, required collision
    pairs only, at most 5 Keys, probe dropped unless the overlay is on.
    """
    takes = [t for t in model.get("takes", []) if t.get("id") in ("A", "B", "C")]
    if len(takes) < 2:
        raise EngineError(
            f"The engine returned {len(takes)} valid Takes; the protocol requires 2-3."
        )
    pairs = required_collision_pairs([t["id"] for t in takes])
    collisions = [c for c in model.get("collisions", []) if c.get("pair") in pairs]
    keys = model.get("keys", [])
    if len(keys) > 5:
        keys = keys[:5]
    if len(keys) < 3:
        raise EngineError(
            f"The engine returned only {len(keys)} Keys; the protocol requires 3-5."
        )
    meta = model.get("meta", {})
    probe = model.get("probe") if overlay else None

    session = (prior_session + 1) if prior_session is not None else 1
    return {
        "meta": {
            "field": meta.get("field") or field_text[:80],
            "status": meta.get("status") or ("ITERATIVE" if prior_session else "INITIAL"),
            "session": session,
        },
        "field": model.get("field", {"objective": "", "scope": ""}),
        "priorState": model.get("priorState", {"reference": None, "evaluations": []}),
        "evidence": model.get("evidence", {"facts": [], "claims": [], "unknowns": []}),
        "probe": probe,
        "takes": takes,
        "collisions": collisions,
        "keys": keys,
        "surprise": model.get("surprise"),
        "synthesis": model.get("synthesis", {}),
        "overlay": overlay,
    }


@dataclass
class RunResult:
    ok: bool
    artifact: dict | None = None
    error: str | None = None


def run(field_input: FieldInput, backend: LLMBackend,
        *, prior_json: str | None = None,
        prior_session: int | None = None) -> RunResult:
    """Run one interrogation against a backend. One pass, never loops."""
    FieldInput(
        field=field_input.field, mode=field_input.mode,
        overlay=field_input.overlay, evidence=field_input.evidence,
    )  # re-validate
    user = build_user_message(field_input.field, overlay=field_input.overlay,
                              prior_json=prior_json)
    try:
        raw = backend.complete(SYSTEM_PROMPT, user)
    except Exception as exc:  # backend errors surface as engine errors
        return RunResult(ok=False, error=f"Backend {backend.name} failed: {exc}")
    try:
        model = parse_model_json(raw)
        artifact = normalize(field_input.field, overlay=field_input.overlay,
                             prior_session=prior_session, model=model)
    except EngineError as exc:
        return RunResult(ok=False, error=str(exc))
    return RunResult(ok=True, artifact=artifact)
