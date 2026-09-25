# Changelog — metacog (front-facing metacog)

All notable changes. The package converts the `metacog` skill v2.0 (Ryan's
skill-suite, MIT) into front-facing, production-ready code. This changelog
doubles as the decoupling record: every entry names what was changed and why.

## 1.0.0 — 2026-09-24

### What was built

- `metacog` Python package, stdlib-only (no third-party
  dependencies): `triggers`, `steelman`, `protocol`, `record`, `engine`,
  `backends`.
- Provider-agnostic runner: any LLM backend works. Shipped backends:
  OpenRouter (documented chat-completions endpoint, key from
  `OPENROUTER_API_KEY` at call time), local Ollama (fully offline),
  deterministic stub (tests/demos).
- 39 offline unit tests, all passing — they prove the machinery, not just
  the prose.
- 1 worked example a stranger can follow (a business decision, annotated
  step by step). `examples/run_local.py` CLI for real runs.
- Plain-language README: what it does, inputs, outputs, why it works,
  quickstart, zero prerequisites.

### Decoupling decisions (mechanism kept, framing removed)

1. **Renamed `metacog` → `metacog`.** The mechanism was already
   plain language; only the name was opaque. "Metacog" parses as insider
   jargon to a stranger; "confidence auditor" says what it does. This was
   the single biggest coupling point in the cleanest skill in the suite —
   which tells you how clean it was.
2. **Kept "collision / collision record" as defined jargon.** It's generic
   systems language, defined on page one of the README, and consistent
   with the converted IFS package's terminology. Renaming it would have
   churned the schema for no gain.
3. **"Controller" kept, demoted.** The skill called metacog a "controller";
   the package keeps the word in one README line ("a controller that
   always fires is noise") and otherwise says "pressure test," which is
   what a stranger pictures.
4. **Trigger gating moved from prose into code.** The skill described the
   five thresholds; the package enforces them — a run with no tripped
   trigger fails validation, and the engine returns an explicit stand-down
   instead of a hollow record.
5. **The steelman check moved from prose into code.** The skill said
   "steelman only, no strawmen"; the package's `steelman.py` checks the
   countermodel mechanically (length, named premises/evidence/mechanism,
   hedge-phrase detection, restatement detection). A weak countermodel
   fails the run. The honest "I can't build a strong one" remains a valid
   finding ("unopposed"), not a failure.
6. **The demotion rule moved from prose into code.** A broken load-bearing
   assumption demotes the conclusion to a hypothesis — derived in the
   engine, not left to the model's discretion.
7. **Invocation triggers rewritten as a CLI.** The skill's overlay/standalone
   modes become `run_local.py` and the `run()` library function. Same
   contract, production shape.
8. **Persistence boundary made explicit.** The skill already said the
   controller never persists; the package enforces it architecturally —
   the engine returns a dict, the caller saves it. No file writes inside
   the engine.

### What was NOT changed

- The five-step sequence (Trigger Thresholds → Strongest Countermodel →
  Load-Bearing Assumptions → Collision → Confidence Revision): untouched,
  including the no-reorder rule.
- The load-bearing vs. structural assumption classification: untouched,
  and now code-enforced (collisions on structural assumptions are rejected).
- The three collision outcomes (survives / weakened / broken): untouched.
- The surprise check as proof of real friction: untouched, carried as a
  required record section.
- The overlay contract (attaches at IFS Collide→Refine, runs
  post-Diverge/pre-Adjudicate on debate engines, or standalone): preserved
  in the README; the package is standalone-first by design.

### Known limits (honest)

- The engine's *behavior* is prompt-level; the 39 tests prove the machinery
  (validation, normalization, schema, steelman heuristics) runs, not that
  any particular model reasons well. The steelman heuristics catch the
  known small-model failure mode (strawmanning) but cannot prove a
  countermodel is strong — strength remains a judgment the model makes.
- No live-model evals exist for this skill (per skills.json, evals: false).
  A behavioral baseline on a free-tier model would cost ~12–14 calls and
  is the obvious next step if one is wanted.
