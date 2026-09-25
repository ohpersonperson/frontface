# Changelog — pressit (front-facing IFS)

All notable changes. The package converts the `ifs-interrogation` skill v2.0 (Ryan's skill-suite, MIT) into front-facing, production-ready code. This changelog doubles as the decoupling record: every entry names what was changed and why.

## 1.0.0 — 2026-09-24

### What was built

- `pressit` Python package, stdlib-only (no third-party dependencies): `evidence`, `protocol`, `artifact`, `overlay`, `engine`, `backends`.
- Provider-agnostic runner: any LLM backend works. Shipped backends: OpenRouter (documented chat-completions endpoint, key from `OPENROUTER_API_KEY` at call time), local Ollama (fully offline), deterministic stub (tests/demos).
- 41 offline unit tests, all passing — they prove the mechanism's machinery, not just its prose.
- 3 worked examples a stranger can follow. `examples/run_local.py` CLI for real runs.
- Plain-language README: what it does, inputs, outputs, why it works, quickstart, zero insider prerequisites.

### Decoupling decisions (mechanism kept, framing removed)

1. **"Tribunal" mode → "adjudication" mode.** The mechanism is "judge a claim against a framework's explicit standards." The original worked example adjudicated a tarot spread against FHK v5.0 canon — the most tightly coupled artifact in the skill. Replaced with a vendor-SLA conformance adjudication against contract text. A stranger understands it immediately.
2. **Field Forge overlay → evasion-probe overlay.** The mechanism (map observable ground, test evasion hypotheses, feed Take seeds into Diverge) is general-purpose adversarial sociology. The workshop stage names Anvil/Hammer/Furnace were replaced with what each stage does: Ground / Probe / Handoff. Jargon-armor testing generalized beyond therapy-speak to any shield-vocabulary (corporate, legal, therapeutic, wellness) — still tested, never presumed (H-obfuscation / H-genuine / H-both).
3. **"The Bloom" → compounding across sessions.** The mechanism (sessions compound; incompatibilities lock together by the fifth) is kept as plain language. The poetic name is dropped.
4. **Acronym disclaimed, not hidden.** "IFS = Iterative Field Synthesis" is defined on page one of the README, with a one-line note that the Internal Family Systems therapy acronym collision is coincidental.
5. **Invocation triggers rewritten as a CLI.** The skill's chat triggers (`/ifs`, `interrogate [field]`) become `run_local.py` and the `run()` library function. Same contract, production shape.
6. **Persistence boundary made explicit.** The skill already said the engine never persists; the package enforces it architecturally — the engine returns a dict, the caller saves it. No file writes inside the engine.
7. **"Field" kept as defined jargon.** It's the one term that reads insider at first glance, but it's defined plainly in the README ("any question, claim, or contradiction you want to pressure-test") and is generic systems language — replacing it would have meant renaming the schema for no gain.

### What was NOT changed

- The five-phase engine and nine-stage deep run: untouched.
- The 10-tier evidence taxonomy plus overlay-only OBFUSCATION: untouched, including the rule that OBFUSCATION requires discriminating evidence and the overlay on.
- The five prior-Key dispositions (HELD / CRACKED / MODIFIED / SUPERSEDED / UNRESOLVED) and historical-integrity rules: untouched.
- The canonical state-artifact schema: section-for-section preserved; filename prefix changed from `ifs-state-` to `interrogation-state-` for stranger legibility.
- The six-component Key contract (statement / classification / evidence / confidence / vulnerability / falsifier): untouched, and now code-enforced.
- The hard limits (2–3 Takes, required collision pairs only, 3–5 Keys, no looping on the one-pass path): moved from prompt-only into code validation.

### Known limits (honest)

- The engine's *behavior* is prompt-level; the 41 tests prove the machinery (validation, normalization, schema, overlay protocol) runs, not that any particular model reasons well. The skill's live-model evals (12/19 baseline on a free-tier model, 2026-09-23) are the behavioral evidence, and their findings — small models under-extract Keys, motive-isolation leaks, missing UNKNOWN tags — still apply. They are named in the README's FAQ-adjacent notes rather than hidden.
- No FHK, tarot, or astrology content was carried over. The conversion is deliberately mechanism-only.
