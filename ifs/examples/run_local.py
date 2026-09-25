#!/usr/bin/env python3
"""Run one interrogation from a field text file and save the state artifact.

Usage:
    python3 run_local.py field.txt [--mode standard] [--overlay] [--model MODEL] [--ollama]

Backends (in order of preference):
    --ollama           local Ollama server, fully offline (default model llama3.1)
    (default)          OpenRouter — needs OPENROUTER_API_KEY and OPENROUTER_MODEL set
    --model MODEL      pick the OpenRouter model explicitly

Examples:
    python3 run_local.py field.txt --ollama
    OPENROUTER_API_KEY=... OPENROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b:free" \\
        python3 run_local.py field.txt
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pressit import (
    FieldInput, EvidenceItem, run, artifact as art, protocol as proto,
    StubBackend, OpenRouterBackend, OllamaBackend,
)


def load_prior_json(path: Path) -> tuple[str, int] | tuple[None, None]:
    prior = art.load_prior(path.read_text())
    return json.dumps({"interrogation": prior["interrogation"],
                       "keys": prior["keys"]}), prior["interrogation"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Run one IFS interrogation.")
    ap.add_argument("field_file", help="text file containing the field description")
    ap.add_argument("--mode", default=proto.STANDARD,
                    choices=list(proto.MODES), help="interrogation mode")
    ap.add_argument("--overlay", action="store_true",
                    help="turn on the evasion-probe overlay (opt-in)")
    ap.add_argument("--model", default=None, help="OpenRouter model id")
    ap.add_argument("--ollama", action="store_true", help="use local Ollama")
    ap.add_argument("--ollama-model", default="llama3.1")
    ap.add_argument("--prior", default=None,
                    help="path to a prior state artifact for session 2+")
    args = ap.parse_args()

    field_text = Path(args.field_file).read_text().strip()
    if not field_text:
        print("Field file is empty.", file=sys.stderr)
        return 2

    if args.ollama:
        backend = OllamaBackend(model=args.ollama_model)
    elif args.model or os.environ.get("OPENROUTER_MODEL"):
        backend = OpenRouterBackend(model=args.model)
    else:
        print("No backend selected. Use --ollama or set OPENROUTER_MODEL "
              "(and OPENROUTER_API_KEY).", file=sys.stderr)
        return 2

    prior_json, prior_session = None, None
    if args.prior:
        prior_json, prior_session = load_prior_json(Path(args.prior))

    field = FieldInput(field=field_text, mode=args.mode, overlay=args.overlay)
    result = run(field, backend, prior_json=prior_json,
                 prior_session=prior_session)
    if not result.ok:
        print(f"Interrogation failed: {result.error}", file=sys.stderr)
        return 1

    a = result.artifact
    keys = [proto.KeyDraft(statement=k["statement"],
                           classification=k["classification"],
                           evidence=k["evidence"], confidence=k["confidence"],
                           vulnerability=k["vulnerability"],
                           falsifier=k["falsifier"]) for k in a["keys"]]
    s = a["synthesis"] or {}
    state = art.StateArtifact(
        field=a["meta"]["field"], session=a["meta"]["session"],
        date=datetime.date.today().isoformat(), depth=args.mode,
        trigger_context=f"CLI run ({args.mode})",
        lifecycle=a["meta"]["status"],
        prior_interrogation=prior_session, prior_date=None, prior_keys=[],
        takes=[art.Take(t["id"], t["title"], t["argument"]) for t in a["takes"]],
        collisions=[art.Collision(c["pair"], c["contradiction"],
                                  c["premiseFailure"], c["discriminator"])
                    for c in a["collisions"]],
        keys=keys, surprise=a["surprise"],
        synthesis=art.Synthesis(
            established_ground=s.get("establishedGround", ""),
            surviving_model=s.get("survivingModel", ""),
            remaining_uncertainties=s.get("remainingUncertainties", ""),
            primary_next_target=s.get("primaryNextTarget", "")),
        interrogation=a["meta"]["session"],
    )

    out = Path(state.filename)
    out.write_text(art.render(state))
    print(f"Saved {out} ({len(a['keys'])} Keys, "
          f"{len(a['takes'])} Takes, {len(a['collisions'])} collisions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
