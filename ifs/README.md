# IFS — Iterative Field Synthesis

A structured way to pressure-test a claim, decision, or contradiction so it comes out the other side either **load-bearing** or **dead** — with the reasoning preserved in a portable document.

No prerequisites. You don't need to know anything about the project's history, any framework, or any belief system. The mechanism is the whole product.

*(Lineage: this is the front-facing conversion of the `ifs-interrogation` skill from Ryan's skill-suite, MIT. What changed in the conversion is documented in CHANGELOG.md — mechanism kept, original naming removed.)*

## What it does

You hand the engine a **field** — a situation, claim, or contradiction with real stakes and real uncertainty. The engine runs it through a fixed interrogation:

1. **Identify & Decompose** — bound the field, name the objective and scope, tag every input with an evidence tier (FACT, CLAIM, UNKNOWN, …). Evidence is never silently upgraded: a claim stays a claim until it's proven.
2. **Diverge** — build the 2 or 3 strongest internally-coherent cases (Takes). No strawmen, no premature consensus.
3. **Collide** — force the Takes into conflict. Every collision names the contradiction, the premise that must break, and the discriminator evidence that decides it. If the collision doesn't hurt brittle claims, it wasn't a real collision.
4. **Refine** — a skeptic pass, then extract 3–5 **load-bearing Keys**: crisp assertions, each with a classification, the tagged evidence behind it, a confidence level, its structural vulnerability, and its falsifier — the specific evidence that would overturn it. A Key that can't survive is discarded, not softened.
5. **Surprise + Synthesis + Capture** — the non-obvious result that emerged *from the collision* (not from one Take), the surviving model, and the complete **state artifact**: a self-contained Markdown document another person or model can continue from without any of the original conversation.

Core principle: **confidence and correctness are independent variables.** The engine interrogates the gap between them.

## Why it works

Most reasoning failures aren't stupidity — they're structural. Claims quietly upgrade into facts. The first plausible story wins and alternatives never get built. Contradictions get smoothed over with "however." IFS attacks all three mechanically:

- **Evidence tagging** makes silent upgrades impossible — every input carries its tier through every phase.
- **Forced Takes** mean the strongest opposing case gets built with the same care as your own.
- **Named collisions with discriminators** force a decision rule instead of vibes.
- **Keys carry falsifiers**, so the output tells you exactly what would prove it wrong.
- **Prior Keys are stress-tested, never inherited.** In session 2+, every old Key gets a verdict — HELD, CRACKED, MODIFIED, SUPERSEDED, UNRESOLVED — and failures stay visible in the artifact instead of being quietly rewritten.

## Quickstart

Zero dependencies beyond Python 3.10+ and a model to run the engine on.

```bash
cd ifs
python3 -m unittest discover -s tests     # 41 offline tests — prove the machinery first
```

To run a real interrogation, you need a backend — any LLM that can follow the protocol prompt:

```bash
# Fully offline: local Ollama
python3 examples/run_local.py my-field.txt --ollama

# OpenRouter (free-tier models work fine)
OPENROUTER_API_KEY=... OPENROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b:free" \
  python3 examples/run_local.py my-field.txt

# Session 2+: feed the prior artifact back in; old Keys get stress-tested
python3 examples/run_local.py new-evidence.txt --prior interrogation-state-my-field.md --ollama
```

`my-field.txt` is just prose: the situation, the conflicting accounts, the stakes. The engine returns `interrogation-state-<slug>.md` — the portable artifact.

Or use it as a library:

```python
from pressit import FieldInput, EvidenceItem, run, OllamaBackend

field = FieldInput(
    field="Q3 revenue is up 41%. The owner calls it a turnaround. Is it?",
    evidence=[
        EvidenceItem("Q3 revenue $48k; Q2 $34k (POS records)", "FACT"),
        EvidenceItem("A July estate sale moved ~2,100 rare books", "FACT"),
        EvidenceItem("Owner: 'new regulars are driving it'", "CLAIM"),
        EvidenceItem("Q4 inventory pipeline", "UNKNOWN"),
    ],
)
result = run(field, OllamaBackend())
assert result.ok
print(result.artifact["surprise"])
```

## The four modes

| Mode | When |
|---|---|
| `standard` (default) | Bounded fields: decisions, claims, single contradictions. One pass, never loops. |
| `systemic` | Structural/multi-actor fields, recurring patterns. Nine stages; may iterate across sessions. |
| `stress-test` | Prior state exists. Every prior Key is dispositioned; only genuinely new Keys are added. |
| `adjudication` | A claim is judged against an explicit standard (a contract, a policy, a spec). Full deep run, no compression. |

The optional **evasion-probe overlay** (off by default) handles interpersonal fields where language may be doing evasive work: it maps the observable ground, tests evasion hypotheses (never presumes them — jargon is tested as H-obfuscation / H-genuine / H-both), and feeds Take seeds into Diverge. It never replaces the engine.

## Inputs, outputs

- **Input:** a field description (prose), optional tagged evidence, optional prior artifact, optional overlay.
- **Output:** a normalized artifact dict, or a rendered `interrogation-state-<slug>.md` — complete, self-contained, no placeholders, no TODOs.
- **The engine never writes files and never claims external persistence.** Your code saves the artifact; the engine's job ends when it's emitted. That's the persistence boundary, and it's deliberate.

## Worked examples

Three complete runs a stranger can follow, in `examples/`:

1. `example-1-corner-books.md` — standard one-pass: is a bookstore's revenue jump a turnaround or a blip?
2. `example-2-corner-books-session-2.md` — stress-test mode: new evidence meets old Keys; watch a Key get CRACKED and preserved visibly.
3. `example-3-sla-adjudication.md` — adjudication mode: a vendor's SLA claim judged against the contract text.

*All three fields are constructed for teaching — they show the engine's shape, not real findings.*

## FAQ

**Is this related to Internal Family Systems therapy?** No. The acronym collision is coincidental; this is an interrogation engine, not a therapeutic method.

**Does it need an internet connection?** Only for the model call, and only the backend you choose. With Ollama it's fully offline. The 41 unit tests never touch the network.

**What does it cost?** The package is free and dependency-free. The model call costs whatever your provider charges — free-tier models work; the engine was evaluated on them.

## License

MIT. See LICENSE.
