# Changelog — flashy (front-facing flashy)

All notable changes. The package converts the `flashy` skill (Ryan's
skill-suite, MIT — itself a port of an execution-discipline protocol into
skill format) into front-facing, production-ready code. This changelog
doubles as the decoupling record: every entry names what was changed and why.

## 1.0.0 — 2026-09-24

### What was built

- `flashy` Python package, stdlib-only (no third-party dependencies):
  `state_machine`, `quality_gate`, `checkpoints`, `detectors`, `session`.
- The execution state machine implemented as actual code with enforced
  transition rules — the genuinely codeable core of the skill.
- Quality Gate as a seven-box checklist object; checkpoint + resume-token
  schema with render/parse round-trip; artificial-stop phrase detection;
  drift questions + snap-back rule; confidence engine (High/Medium/Low)
  with the only-Low-pauses rule; mission session binding it all with the
  dashboard and the end-of-response gate.
- 41 offline unit tests, all passing — they prove the machinery, not just
  the prose.
- 3 worked examples a stranger can follow (two ported unchanged from the
  original skill, one new showing the machinery itself).
  `examples/demo_session.py` drives a full LOCKED → DONE run with no
  model and no network.
- Plain-language README: what it does, inputs, outputs, why it works,
  quickstart, zero prerequisites.

### Decoupling decisions (mechanism kept, framing removed)

1. **Renamed `flashy` → `flashy`.** "Flashy" is branding; a stranger
   can't parse it. "Finish mode" is what the original protocol's own
   tagline said it was.
2. **Dropped the "GPTADHD" origin name everywhere.** It was a joke name
   from the ported protocol, not a cosmology — but it tells a stranger
   nothing and reads as insider humor. The lineage is documented here, in
   the CHANGELOG, where it belongs.
3. **Stripped emoji from code identifiers and rendered output.** The
   original checkpoint format (`⚡ FLASHY CHECKPOINT`, `🎯 OBJECTIVE → …`)
   renders here as plain `FLASHY CHECKPOINT` / `OBJECTIVE -> …`.
   One ⚡ survives in the README's prose, for charm.
4. **Resume tokens re-prefixed `flashy:` → `finish:`.** Same shape
   (`finish:<slug>-m<N>`), no stale branding in machine-readable output.
5. **The state machine moved from prose into code.** The skill described
   the states and rules; the package enforces them — illegal transitions
   raise `TransitionError`. This is the conversion's main value-add: the
   discipline is now structural, not advisory.
6. **Artificial-stop detection moved from prose into code.** The skill
   listed the phrases; `detect_artificial_stop()` scans for them. The
   phrase list is ported verbatim (9 phrases) so the port can't silently
   narrow the detector.
7. **Kept the two ported examples byte-identical.** The debate-simulator
   walkthrough and the anti-patterns pairs were already generic — no
   example needed replacing, so none was. Porting them unchanged is the
   honest record that the mechanism needed no translation.
8. **Drift detection and the confidence engine stay operator-run.** Four
   drift questions and three confidence levels are carried as data with
   the snap-back rule and the only-Low-pauses rule stated once. Judging
   drift is not codeable without a model in the loop; the package is
   honest about which parts are machinery and which are discipline.

### What was NOT changed

- The mission rule ("a draft is not a delivery"): untouched, now the
  package docstring.
- The seven Quality Gate boxes: untouched, ported verbatim.
- The core loop (lock → milestones → state → drift scan → verify):
  untouched.
- The failure-recovery typology (context cutoff / tool error /
  mid-task contradiction / safety stop): preserved in the README; the
  checkpoint path is code, the judgment calls are documented.
- The "never deactivate because a response feels long enough" rule:
  untouched.

### Known limits (honest)

- The package is discipline machinery, not an agent harness — it tracks
  and enforces, but the *work* between milestones is still the operator's.
  It cannot make a model build; it can only make the stopping rules
  structural.
- Drift judgment and confidence ratings need an operator (human or model)
  in the loop; the package carries the questions and the rules, not the
  judgment.
- The original protocol spec ("GPTADHD") is not vendored in the
  skill-suite repo — if the port dropped anything from the original, this
  conversion can't diff it. The skill's SKILL.md is treated as canonical;
  the gap is noted, not papered over.
