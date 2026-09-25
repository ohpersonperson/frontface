#!/usr/bin/env python3
"""Run a reasoning pressure test from the command line.

Usage:
    python3 examples/run_local.py reasoning.txt            # stub backend (demo)
    python3 examples/run_local.py reasoning.txt --ollama   # local Ollama
    OPENROUTER_API_KEY=... OPENROUTER_MODEL="model-id" \
        python3 examples/run_local.py reasoning.txt --openrouter

reasoning.txt is plain prose:
    CONCLUSION: <the claim or decision>
    REASONING: <the reasoning-in-progress, prose>
    EVIDENCE: one item per line (optional)
    CONFIDENCE: 0-100 (optional)

Output: a rendered collision-record Markdown document.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from metacog import (
    ReasoningInput, run, to_collision_record, StubBackend,
)


def parse_input(path: str) -> ReasoningInput:
    text = open(path, encoding="utf-8").read()
    conclusion, reasoning, evidence, confidence = "", "", [], None
    section = None
    for line in text.splitlines():
        upper = line.strip().upper()
        if upper.startswith("CONCLUSION:"):
            conclusion = line.split(":", 1)[1].strip()
            section = "conclusion"
        elif upper.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
            section = "reasoning"
        elif upper.startswith("EVIDENCE:"):
            section = "evidence"
        elif upper.startswith("CONFIDENCE:"):
            try:
                confidence = int(line.split(":", 1)[1].strip())
            except ValueError:
                confidence = None
            section = None
        elif section == "evidence" and line.strip():
            evidence.append(line.strip().lstrip("- "))
        elif section == "reasoning" and line.strip():
            reasoning += " " + line.strip()
        elif section == "conclusion" and line.strip():
            conclusion += " " + line.strip()
    return ReasoningInput(
        conclusion=conclusion, reasoning=reasoning,
        evidence=evidence, stated_confidence=confidence,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Pressure-test a reasoning-in-progress.")
    ap.add_argument("input", help="Reasoning file (CONCLUSION/REASONING/EVIDENCE/CONFIDENCE).")
    ap.add_argument("--ollama", action="store_true", help="Use local Ollama backend.")
    ap.add_argument("--openrouter", action="store_true", help="Use OpenRouter backend.")
    ap.add_argument("--model", default=None, help="Model id (ollama/openrouter).")
    args = ap.parse_args()

    from metacog import backends as _b  # noqa: F401  (keeps CLI slim)

    if args.ollama:
        from metacog import OllamaBackend
        backend = OllamaBackend(model=args.model or "llama3.1")
    elif args.openrouter:
        from metacog import OpenRouterBackend
        backend = OpenRouterBackend(model=args.model)
    else:
        print("NOTE: no backend selected — stub backend returns a canned demo record.",
              file=sys.stderr)
        backend = StubBackend({
            "triggers": ["explicit-invocation"],
            "countermodel": "DEMO: run with --ollama or --openrouter for a real test.",
            "assumptions": [],
            "collisions": [],
            "confidence_before": 0,
            "confidence_after": 0,
            "demotions": [],
            "surprise": "",
        })

    result = run(parse_input(args.input), backend)
    if not result.ok:
        print(f"RUN FAILED: {result.error}", file=sys.stderr)
        return 1
    if result.record.get("stand_down"):
        print(result.record["report"])
        return 0
    print(to_collision_record(result.record).render())
    return 0


if __name__ == "__main__":
    sys.exit(main())
