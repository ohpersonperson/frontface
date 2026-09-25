# Confidence Auditor — five-step reasoning pressure test

Interrogation, not supervision. You hand it reasoning-in-progress; it
returns a **collision record** with a revised confidence — before→after,
per load-bearing assumption and overall. It never originates analysis.
It pressure-tests analysis that already exists.

No prerequisites. You don't need to know anything about the project's
history, any framework, or any belief system. The mechanism is the whole
product.

*(Lineage: this is the front-facing conversion of the `metacog` skill from
Ryan's skill-suite, MIT. What changed in the conversion is documented in
CHANGELOG.md — the name and nothing else, really; this was already the
cleanest skill in the suite.)*

## What it does

Five steps, in order, never reordered — evaluating before colliding is
the most common failure mode (you polish claims that should have died):

1. **Trigger Thresholds** — decide whether it's worth firing at all.
   Fires on: stakes (hard-to-reverse decision), confidence-without-evidence,
   contradiction-present (an uncollided counter-take exists),
   premature-convergence (one take survived unchallenged), or explicit
   invocation. No tripped threshold = stand down, honestly. A controller
   that always fires is noise.
2. **Strongest Countermodel** — the strongest internally-coherent case
   *against* the current conclusion. Steelman only: named premises, named
   evidence, named mechanism. The package checks the countermodel
   mechanically (see "Why it works") — a strawman fails the run. An
   honest "I can't build a strong one" is a finding, not a failure.
3. **Load-Bearing Assumptions** — every assumption the conclusion depends
   on, marked **load-bearing** (if false, the conclusion falls) or
   **structural** (supports it, but it survives without it). Only
   load-bearing assumptions go to collision.
4. **Collision** — the countermodel attacks each load-bearing assumption,
   one at a time: **survives / weakened / broken**. Contradictions are
   held in parallel non-subordinating sentences ("X is true. Y is also
   true." — never "X, however Y"). The **surprise check**: if the
   collision produced nothing neither side contained alone, it wasn't a
   real collision — run it again, harder.
5. **Confidence Revision** — before→after per assumption and overall.
   The delta is the output. A broken load-bearing assumption doesn't
   merely lower confidence — it **demotes the conclusion to a hypothesis**
   pending new evidence. "I feel less sure" (self-report) is distinguished
   from "the assumption broke under the countermodel" (finding).

Core principle: **confidence and correctness are independent variables.**
This tool interrogates the gap between them.

## Why it works

Most reasoning failures are structural, not intellectual. Confidence
quietly outruns evidence. The first plausible story wins and alternatives
never get built. Contradictions get smoothed with "however." The audit
attacks all three mechanically:

- **Trigger gating** means it only fires when the stakes or the
  contradiction warrant it — no theater runs.
- **The steelman check** (`steelman.py`) catches weak countermodels by
  their mechanical signatures: too short to be specific, hedge phrases
  with no named premises ("some might disagree..."), no evidence or
  mechanism named, or a restatement of the conclusion in contrast
  clothing. A weak countermodel fails the run before the collision can
  be theater. This is the failure mode live-model evals found in small
  models — checked in code, not just in prose.
- **Load-bearing classification** focuses the collision where it can
  change the conclusion. Colliding structural assumptions is motion
  without effect.
- **The demotion rule** makes broken assumptions costly: the conclusion
  doesn't get a softer number, it gets demoted to a hypothesis.

## Quickstart

Zero dependencies beyond Python 3.10+ and a model to run the engine on.

```bash
cd metacog
python3 -m unittest discover -s tests     # 39 offline tests — prove the machinery first
```

To run a real pressure test, you need a backend — any LLM that can follow
the protocol prompt:

```bash
# Fully offline: local Ollama
python3 examples/run_local.py reasoning.txt --ollama

# OpenRouter (free-tier models work fine)
OPENROUTER_API_KEY=... OPENROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b:free" \
  python3 examples/run_local.py reasoning.txt --openrouter
```

`reasoning.txt` is plain prose:

```
CONCLUSION: Migrate billing to the new provider now
REASONING: Costs are lower and churn will drop.
EVIDENCE:
- Quote: $38k migration
- Q1 cohort churn 3.8%
CONFIDENCE: 80
```

The engine returns a rendered collision record — the portable artifact.
The engine never writes files and never claims external persistence:
your code saves the record.

Or use it as a library:

```python
from metacog import (
    ReasoningInput, run, to_collision_record, OllamaBackend,
)

result = run(
    ReasoningInput(
        conclusion="Migrate billing to the new provider now",
        reasoning="Costs are lower and churn will drop.",
        evidence=["Quote: $38k migration", "Q1 cohort churn 3.8%"],
        stated_confidence=80,
        triggers=["stakes", "contradiction-present"],
    ),
    OllamaBackend(),
)
assert result.ok
print(to_collision_record(result.record).render())
```

## Inputs, outputs

- **Input:** a conclusion, the reasoning behind it (prose), optional
  evidence, optional stated confidence, optional claimed triggers.
- **Output:** a normalized record dict, or a rendered `collision-record`
  Markdown document — complete, self-contained, no placeholders.

## Worked example

`examples/example-1-billing-migration.md` — a complete collision record
for a business decision (migrate billing providers?), annotated so a
stranger can follow each step.

*The field is constructed for teaching — it shows the audit's shape, not
real findings.*

## FAQ

**Does it replace the IFS interrogation engine?** No. It pressure-tests
reasoning that already exists; IFS interrogates a field from scratch.
They attach cleanly (the audit runs at the Collide→Refine boundary), but
each works standalone.

**Does it need an internet connection?** Only for the model call, and
only the backend you choose. With Ollama it's fully offline. The 30 unit
tests never touch the network.

**What does it cost?** The package is free and dependency-free. The model
call costs whatever your provider charges — free-tier models work.

## License

MIT. See LICENSE.
