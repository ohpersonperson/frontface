# Full-Suite Conversion Assessment
**Date:** 2026-09-24
**Scope:** 8 remaining skills in `~/workspace/skill-suite` (ifs-interrogation already converted — pattern lives at `~/workspace/frontface/ifs/`). FHK is out of scope (stays Ryan's private canon). Assessment only — nothing converted, committed, or pushed.

**Baseline for effort ratings:** the IFS conversion was **medium-large** — stdlib-only Python package (`adversarial_ifs`), 41 offline tests, 3 worked examples, plain-language README, CHANGELOG, MIT LICENSE, pyproject.toml.

---

## 1. metacog

**Mechanism.** A five-step pressure-test for reasoning-in-progress: check whether it's worth firing at all (trigger thresholds: stakes, confidence-without-evidence, uncollided contradiction, premature convergence), steelman the strongest countermodel, isolate load-bearing assumptions (the ones whose failure kills the conclusion), collide the countermodel against each one (survives / weakened / broken), and revise confidence with a before→after delta. Output is a collision record. It never originates analysis — it interrogates analysis that already exists, standalone or as an overlay.

**FHK coupling.** Essentially none. No tarot, no cosmology, no jargon-armor terms. The heaviest "inside" language is "collide/collision" and "surprise check," which the IFS conversion already kept as defined generic jargon. This is the cleanest skill in the suite.

**Conversion work.**
- Rename `metacog` → something a stranger parses instantly, e.g. `confidence-auditor` or `reasoning-pressure-test`.
- Keep the five-step sequence verbatim — it's already plain language.
- Code: the collision record as a small schema (triggers tripped, countermodel, assumption→result map, confidence delta, demotions, surprise) with render/parse + validation tests. Optionally a steelman-quality check (the 2026-09-23 live evals found small models strawman — the assessment from the earlier run flagged this; worth a code-level heuristic or an eval assertion, not just prose).
- Docs: one worked example (a business decision or a code-design call — not an interpersonal conflict, to show it's domain-agnostic).
- Tests: threshold gating (fires / stands down), load-bearing vs structural classification, confidence-delta math, collision-record schema completeness.

**Effort.** Small. Roughly half the IFS conversion — no kernel to reconstruct, no evidence taxonomy, no overlay contract to negotiate.

**Dependencies.** None. Attaches to the IFS kernel optionally, but works standalone and that's the conversion headline.

---

## 2. flashy

**Mechanism.** An execution-discipline layer that prevents an agent from abandoning a build halfway — "a draft is not a delivery." Locks the objective (stated deliverable + implicit quality bar + scope boundaries), expands it into milestones, tracks live execution state, scans for drift after every milestone (still solving the original problem? explaining instead of building?), detects artificial stops ("here's a starting point," "the rest follows similarly") and rewrites them as "continue working," manages checkpoints with resume tokens on interruption, and gates completion on a quality checklist. Per the README, it's a port of a "GPTADHD" execution protocol into the Claude skill format — the origin is a joke name, not a cosmology.

**FHK coupling.** None. Zero. The only renames needed are branding: "GPTADHD," "flashy," the ⚡ emoji. The mechanism is pure project-execution discipline.

**Conversion work.**
- Rename → `finish-mode` or `task-completion-discipline`. Strip emoji from code identifiers (keep one in the README if charm matters).
- The execution state machine (`LOCKED → PLANNING → EXECUTING → VERIFYING → DONE`, `BLOCKED` reachable from EXECUTING/VERIFYING) is genuinely codeable — implement it as a small state machine with the transition rules enforced, plus the checkpoint/resume-token schema. That's the concrete software deliverable; the rest (drift questions, artificial-stop phrase list, quality gate) becomes data + docs.
- Keep the three templates and two examples nearly as-is; replace nothing — they're already generic (debate simulator walkthrough, before/after anti-patterns).
- Tests: state-machine transition rules (no VERIFYING→DONE with unchecked gate boxes, no silent PLANNING re-entry), checkpoint schema round-trip, artificial-stop phrase detection against the before/after pairs.

**Effort.** Small. Mostly repackaging + one small state machine.

**Dependencies.** None.

---

## 3. proofit

**Mechanism.** Locks down a multi-service, free-tier, no-API workflow *before* execution so nothing is improvised mid-stream: remove every assumption (buttons, file locations, terminology, order of operations), declare all prerequisites and free-tier limits upfront, one action per step with concrete visible references, explain unavoidable jargon inline, add objective verification after every milestone, include immediate recovery paths, specify routing decisions per service (exact prompt, expected output schema, rate-limit handling), and finish with a full validation checklist instead of ending on the last action.

**FHK coupling.** None. It's written in plain operational language already. The name "proofit" is opaque but not insider.

**Conversion work.**
- Rename → `workflow-lockdown` or `runbook-spec`. The current name tells a stranger nothing.
- This is the most design-heavy conversion: the skill is prose-only, no evals, no verification, no CHANGELOG evidence of live use. Two honest options: (a) keep it a protocol document with a worked example and a validation-checklist generator (input: runbook draft → output: missing-prerequisite / assumption / unverified-milestone flags), or (b) admit it's a prompt-engineering doc and ship it as such with the validator as the code. Either way, the validator is the testable core: feed it a runbook, assert it catches a missing prerequisite, a combined two-action step, a milestone without verification.
- Worked example: lock down a real free-tier multi-service workflow (e.g., "weekly research digest across three free AI web UIs") so the routing-decision machinery is visible.
- Tests: assumption-detection on sample runbooks, one-action-per-step linting, schema validation of routing specs, the consistency-checkpoint list as an assertion set.

**Effort.** Medium. Not because of coupling — because the code deliverable has to be designed from scratch. Needs one design call from Ryan: validator strictness (linter vs. generator).

**Dependencies.** None.

---

## 4. memdate-v2

**Mechanism.** A provider-agnostic, file-based memory system in plain Markdown with one load-bearing invariant: **CAPTURE preserves, DISTILL interprets, never mix them.** CAPTURE appends timestamped raw records without summary or synthesis; DISTILL consolidates raw into `distilled.md` without touching raw; after any full or multi-domain distill, a cross-domain index (entities→domains, dependencies, open questions, hot zones) is regenerated. Raw is authoritative in any conflict. That's the whole system, and it's genuinely good.

**FHK coupling.** Light and mechanical: the default domain list (`personal`, `fhk`, `tribunal`, `memory-system`, `misc`) and the storage root (`!Memory` on Google Drive) are Ryan's. The machinery doesn't care what the domains are called.

**Conversion work.**
- Make the domain list configurable (a `domains.yaml` or init arg); ship with neutral example domains, not Ryan's.
- Storage adapter seam: local filesystem default, Google Drive adapter optional — no hard Drive dependency in the core. (Current primary location is Drive; the conversion must not assume it.)
- Code: `capture()` (append-only, timestamped, refuses interpretation — the isolation check is codeable: reject entries containing summary markers), `distill()` (consolidate, never mutate raw — enforce by file-mode or by diffing raw before/after and failing the run), `regenerate_index()` (the four required sections, orphan check: every cross-domain entity must appear in ≥2 distilled files).
- Docs: the CAPTURE/DISTILL/INDEX separation is the README's page one; worked example with two neutral domains.
- Tests: append-only enforcement (distill must not alter raw — byte-compare), frontmatter provenance on distilled/index artifacts, index orphan detection, the decision rule (record→CAPTURE, consolidate→DISTILL) as a dispatch test.

**Effort.** Medium. Real code (capture/distill/index as a small library + CLI), but the spec is unusually complete — the isolation checks and index procedure are already written as mechanical steps.

**Dependencies.** None — but **meminqu-memory-interrogation depends on this** (its capture target). memdate converts first.

---

## 5. meminqu-memory-interrogation

**Mechanism.** An interactive interviewer for the memory system: walks each memory domain in fixed order, asks 2–4 questions per domain in deliberately different registers (direct/forensic, reflective, structural, irreverent/cutting, sparse, temporal, contrastive), then captures the answers verbatim into that domain's memdate `raw.md` under pure CAPTURE rules — no synthesis, no interpretation, no analysis unless separately requested.

**FHK coupling.** Light: the fixed domain list includes `fhk` and `tribunal`; one operational note mentions "IFS, FHK reading" as possible follow-up analysis. Both are configuration, not mechanism.

**Conversion work.**
- Domains become configuration inherited from memdate (single source of truth — don't re-declare the list here).
- The registers are the actual IP — keep all seven, they're already plain language. Maybe add 1–2 neutral ones; don't cut.
- Code: a prompt-loop runner (domain → registers → answers → capture call into the memdate library). The valuable testable piece is the capture-format contract: answers preserved verbatim, correct date heading, register list recorded, zero synthesis. A verbatim-preservation test (input with contradictions/typos → output identical) is the load-bearing test.
- Rename → `memory-interviewer` or `guided-capture`. The current name is opaque.
- Docs: one worked cycle on neutral domains showing the register rotation.

**Effort.** Small-medium. Thin runner over the memdate library; the capture-format tests are the real work.

**Dependencies.** **memdate-v2 — hard dependency.** Converts after memdate. Shares memdate's domain config.

---

## 6. responsibility-obfuscation-probe

**Mechanism.** Tests whether evasive-looking communication is actually evading anything — never presumes it. Every candidate evasion marker (therapy-speak, euphemism, fogging, DARVO, projection, victim-offender reversal, grievance layering) becomes competing hypotheses — H-obfuscation / H-genuine / H-both — tested against *discriminating* evidence (observations that would differ between hypotheses: does the language appear only under pressure? followed by accountability or topic change?). "Insufficient evidence to distinguish" is an honest finding. v2.0 explicitly de-biased the v1 probe, which pre-judged therapy-speak as obfuscation and structurally couldn't conclude "no evasion found." Outputs a hypothesis record that feeds the IFS kernel's Diverge phase.

**FHK coupling.** Very light. DARVO/fogging/projection are standard psychology terms, not Ryan-cosmology. "Therapy-speak" framing is interpersonal-domain language, generalizable. The kernel-attachment is architectural, not insider.

**Conversion work.**
- Rename → `evasion-hypothesis-probe` (or `obfuscation-probe` — keep it descriptive). Generalize the jargon protocol beyond therapy-speak: the same H-obfuscation/H-genuine/H-both structure applies to corporate-speak, bureaucratic passive voice, any shield-vocabulary. Ship with 2–3 dialect modules (therapy, corporate, bureaucratic) to prove the generalization.
- Code: this becomes the **shared hypothesis-testing library** for the whole suite (see Shared Infrastructure). Hypothesis record schema (candidate evasion, best-supported hypothesis, discriminating evidence, mechanisms with status, remaining questions) with validation — e.g., a record claiming H-obfuscation must cite ≥1 discriminating evidence item; "insufficient evidence" must not cite verdicts.
- The v1-bias failure modes are already documented as retired — convert them into regression tests (a therapy-speak instance with only accountability-following evidence must NOT yield H-obfuscation).
- Merge with field-forge's Hammer: the Hammer already runs this protocol. One implementation, two consumers — do not convert twice.

**Effort.** Small-medium as a standalone library; the real cost is shared with field-forge.

**Dependencies.** ifs-interrogation (converted ✓) for the overlay feed. No blockers.

---

## 7. field-forge

**Mechanism.** An opt-in pre-interrogation audit overlay on the IFS kernel, in three stages: **Anvil** maps the ground (held tensions as parallel non-subordinating sentences, time-indexed person-state sequences, detail-vs-core-claim correction typing); **Hammer** tests evasion hypotheses (obfuscated-object hypothesis with support status, apparent function, active tactics — each as hypothesis with discriminating evidence, never verdicts; therapy-language instances run the responsibility-obfuscation-probe protocol); **Furnace** hands 2–3 take-seeds plus OBFUSCATION-tagged material directly into the kernel's Diverge phase, then stands down — it never collides, adjudicates, or extracts surprise itself. Six execution disciplines (hold contradictions live, time-indexed person-states, detail vs core corrections, isolate motive, test jargon claims, no softening) plus an 8-tier evidence taxonomy.

**FHK coupling.** Medium — mostly naming and framing, not mechanism: "Anvil / Hammer / Furnace," "the field," "forge brief." The v2.0 rewrite already retired the worst of it (the old standalone Furnace pipeline that duplicated the kernel). The therapy-speak emphasis is domain language, generalizable like the probe's.

**Conversion work.**
- Rename → `evasion-audit-overlay` or `pre-interrogation-audit`. Stage renames: Anvil → `ground-map`, Hammer → `hypothesis-test`, Furnace → `seed-handoff`. "Field" → "case" or "material" throughout; "forge brief" → "audit brief."
- Generalize the Hammer's jargon protocol to multiple dialects using the shared hypothesis library (see #6) — the earlier assessment already prototyped this as `overlay.py` in the IFS package; promote that prototype, don't rewrite it.
- Code-enforce the stand-down rule: the overlay's output type must not contain collision/adjudication/surprise sections (schema-level — a test asserting their absence).
- The six execution disciplines become assertion-ready checks where possible (e.g., subordinating-conjunction scan on held tensions; motive-language scan) — some remain prompt discipline, and that's honest; mark which is which.
- The 8-tier evidence taxonomy here vs the 10-tier taxonomy in the converted IFS package: reconcile once (superset or mapping table), don't ship two competing taxonomies.
- Tests: ground-map schema (held tensions are parallel non-subordinating sentences — testable with a conjunction scan), hypothesis records carry support status, OBFUSCATION tags require discriminating evidence, stand-down enforcement, take-seed count 2–3.

**Effort.** Medium. The prototype exists; the work is rename + generalize + contract enforcement + taxonomy reconciliation.

**Dependencies.** ifs-interrogation (converted ✓) — attaches to its Diverge phase. **Convert together with responsibility-obfuscation-probe** (the Hammer consumes the probe protocol; one hypothesis library, two consumers).

---

## 8. forensic-situational-audit

**Mechanism.** An audit discipline that holds a messy multi-person situation *without resolving it*: five rules — (1) hold contradictions as contradictions in parallel non-subordinating sentences, never synthesize a third thing or flag tension as a problem; (2) track people as time-indexed states, never categorical verdicts; (3) type every correction as detail-vs-core-claim; (4) never supply motive or causality the teller didn't state; (5) self-check every output for softened threat language, supplied generous interpretations, dropped contradictions, resolved ambivalence. Runs as an overlay enforcing these on the IFS kernel's Decompose/Collide phases, or in **direct audit mode** — "don't resolve this, just hold it" — where the kernel doesn't run at all.

**FHK coupling.** Light: "field" language, kernel-phase attachment framing. The five disciplines themselves are plain and immediately legible — a stranger understands all five in one reading. The worked example in the SKILL ("I adored her and I'm furious at her") is already generic.

**Conversion work.**
- Rename → `situation-audit` or `contradiction-ledger`. Lead with **direct audit mode** as the headline — it's the most standalone-understandable piece and needs no kernel.
- Generalize the overlay contract via the shared overlay base (see Shared Infrastructure); the kernel-phase enforcement points (Decompose/Collide) become adapter hooks rather than the skill's identity.
- "Conversational, not a rigid template" is the stated output shape — keep the conversational surface, but the audit *record* (which disciplines were enforced, corrections typed, softening caught) becomes a structured artifact. Design call: how much structure the record carries vs. the conversation. Recommend: record is structured, conversation stays human.
- Tests (several disciplines are genuinely codeable): subordinating-conjunction scan on held tensions; correction-typing (detail vs core-claim) on sample corrections; softening-detection (threat-language downgrade wordlist — "mistake" for "betrayal," etc.); motive-supply detection ("because he panicked" with no teller attribution → flag).
- Docs: worked direct-audit session on a neutral multi-person situation (workplace dispute, not a personal relationship).

**Effort.** Medium. The codeable checks are the differentiator — this converts into a linter-like discipline tool, which is more than prose.

**Dependencies.** ifs-interrogation (converted ✓) for overlay mode; standalone for direct mode. No blockers.

---

## Recommended conversion order

1. **metacog** — smallest, zero coupling, zero dependencies. Quick win; establishes the conversion rhythm.
2. **flashy** — standalone, already front-facing, small. The state machine is a clean second deliverable.
3. **proofit** — standalone, small-medium. Needs the one design call (validator strictness) — get it early while momentum is high.
4. **memdate-v2** — standalone, medium. Unblocks meminqu. The storage-adapter seam is the design point.
5. **meminqu-memory-interrogation** — small-medium. Hard dependency on memdate; shares its domain config. Converts immediately after.
6. **responsibility-obfuscation-probe + field-forge, together** — medium combined. The probe becomes the shared hypothesis library; the forge consumes it. Doing them separately would duplicate the hypothesis protocol — don't.
7. **forensic-situational-audit** — medium. Last: its overlay mode rides the shared overlay contract proven by #6, and its direct mode is independently shippable.

**Dependency logic in one line:** the only hard ordering constraint is memdate → meminqu; everything else is standalone-first, then the kernel-overlay group (which all attach to the already-converted IFS package, so no sequencing risk there). The probe+forge pairing is a do-together, not a sequence.

---

## Shared infrastructure (extract once, reuse)

1. **`brief` artifact schema** — every overlay and controller emits a "brief/record" (forge brief, audit record, collision record, hypothesis record, checkpoint). One schema: frontmatter (`artifact:`, `date:`, `protocol:`, `lifecycle:` — the Phase 1.1 invariant already exists in-repo) + named sections + Markdown render/parse + validation (no placeholders, all required sections present). The IFS package's `artifact.py` is the seed; generalize it.
2. **`OverlayContract` base** — every overlay (field-forge, forensic-audit, responsibility-probe, metacog-as-overlay) declares: attachment points, what it emits, what it never does (stand-down rule), and the "no kernel running → report brief and stop" behavior. Code the stand-down as schema enforcement.
3. **Hypothesis-testing library** — H-target / H-genuine / H-both / insufficient-evidence with discriminating-evidence requirements. Consumed by the probe, the forge's Hammer, metacog's collision step, the audit's correction typing. One implementation.
4. **Evidence-tag validator** — the IFS package's 10-tier taxonomy validator; reconcile field-forge's 8-tier list into it once (superset or mapping table) and share.
5. **CLI shape** — standardize on the IFS package's `examples/run_local.py` pattern: `python -m <pkg> run --input ... --backend [stub|openrouter|ollama]` across all packages.
6. **Test harness pattern** — stdlib `unittest`, fully offline, deterministic stub backend; property-style invariants (schema completeness, no placeholders, append-only enforcement). Copy the pattern, not the tests.
7. **Eval harness pattern** — the IFS `evals/run_evals.py` (free OpenRouter model, LLM-judged assertions, ~12–14 calls per full run against the 50 req/day free-tier cap). Reuse per skill for behavioral baselines — none of the 8 has one yet.

---

## Red flags

1. **No evals or verification anywhere except IFS.** Per skills.json, all 8 show `evals: false` or null; only ifs-interrogation (12/19 baseline) and the superseded ifs-proto lineage have any. Conversion tests will prove machinery, not model behavior — same caveat as the IFS run. Budget one eval-harness pass per skill after conversion if Ryan wants behavioral baselines; each costs ~12–14 free-tier calls.
2. **proofit is prose-only with no live-use evidence.** No CHANGELOG, no verification notes, no evals. The code deliverable (validator/linter) has to be designed from scratch, and there's a real question whether it stays a protocol doc or becomes software. Needs Ryan's design call — don't guess.
3. **Probe + forge overlap is structural, not accidental.** v2.0 of both documents it (Hammer runs the probe protocol). Converting them separately guarantees duplication or drift. They're one work item with two surfaces.
4. **Two competing evidence taxonomies.** IFS package: 10 tiers. field-forge: 8 tiers (slightly different names). Must be reconciled once during the forge conversion — a mapping table at minimum, a superset ideally. Flag it now so it doesn't become a silent fork.
5. **Audit's conversational output vs. structured record.** The skill explicitly says "conversational, not a rigid template." The front-facing version needs both: human conversation + machine-readable audit record. The record's structure is a design call (recommend: structured record, conversational surface).
6. **memdate's Drive-rooted storage.** Current primary location is Ryan's `!Memory` Drive folder. The conversion must ship a local-filesystem default with Drive as an optional adapter — otherwise it's not front-facing, it's Ryan-facing.
7. **flashy's origin spec isn't in the repo.** The README says it's a port of a "GPTADHD" protocol; the original spec's full contents aren't vendored. If the port dropped anything, we can't diff it. Treat the SKILL.md as canonical and note the gap.
8. **Nothing here is undecouplable.** Stated plainly because it matters: unlike FHK, no skill's mechanism requires Ryan's cosmology. The worst coupling found is naming, examples, and Ryan-specific domain/storage defaults. No red flag of the "can't be done honestly" kind exists in this set.

---

## Effort summary

| Skill | Effort | Depends on |
|---|---|---|
| metacog | small | — |
| flashy | small | — |
| proofit | medium (design-heavy) | — (needs 1 design call) |
| memdate-v2 | medium | — (unblocks meminqu) |
| meminqu-memory-interrogation | small-medium | memdate-v2 |
| responsibility-obfuscation-probe | small-medium | ifs-interrogation ✓ converted |
| field-forge | medium | ifs-interrogation ✓ converted; pair with probe |
| forensic-situational-audit | medium | ifs-interrogation ✓ converted |

Total: roughly 2 smalls, 2 small-mediums, 4 mediums — against the IFS medium-large baseline. The standalone group (metacog, flashy, proofit, memdate) is independently shippable and carries no dependency risk.
