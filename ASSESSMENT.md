# Assessment — converting the rest of the FHK-coupled skills

Assessment only. Nothing below was converted; IFS was the conversion pattern
(see `ifs/`). For each system: the mechanism in one paragraph, what's coupled
to his private framing, and what conversion would take. All three are far cleaner
than "FHK-coupled" suggests — the couplings are naming and lineage, not
cosmology.

---

## 1. metacog

**The mechanism.** An operational metacognitive controller: it takes
reasoning-in-progress as input and returns a collision record with revised
confidence. Five fixed steps — Trigger Thresholds (only fire when stakes,
unsupported confidence, uncollided contradiction, premature convergence, or
explicit invocation trip a threshold; standing down is a valid output) →
Strongest Countermodel (steelman only, specific, no strawmen) → Load-Bearing
Assumptions (only assumptions whose falsity kills the conclusion go forward) →
Collision (countermodel attacks each load-bearing assumption; result is
survives / weakened / broken; emergence is the proof of friction) → Confidence
Revision (report confidence before → after per assumption; broken assumptions
demote conclusions to hypotheses). Cross-cutting: it attaches as an overlay to
other skills (IFS kernel, debate engines) or runs standalone; it never
originates analysis, never supplies domain evidence, never persists state.

**FHK coupling.** Essentially none. There is no tarot, no astrology, no
personal cosmology anywhere in the skill — it is pure reasoning discipline.
The only friction is incidental: the term "controller" and the name "metacog"
itself read academic rather than mystical. The overlay contract references the
IFS kernel and debate engines by their internal names, which a stranger would
need translated once.

**What conversion would take.** The smallest of the three — mostly a packaging
job:

1. Rename for a stranger: `metacog` → something like `confidence-auditor` or
   `reasoning-pressure-test`; keep `metacog` as a documented alias.
2. Generalize the overlay contract: "attaches to any analysis pipeline that
   produces takes and collisions" instead of naming IFS internals.
3. Package shape mirrors IFS: `protocol.py` (the five steps, trigger
   thresholds as code), a countermodel-quality rubric, and a collision-record
   renderer; backends identical to IFS's.
4. One genuinely new piece of work: a testable steelman-quality check. The
   live-model evals found that small models strawman the countermodel (theater
   instead of collision) — the conversion should encode countermodel
   specificity requirements (named premises, named evidence, named mechanism)
   as validation, not just prompt text.
5. 2–3 worked examples: one on a business decision (e.g., "should we ship
   this?"), one as an overlay on an IFS artifact, one standalone on a
   reasoning transcript. The existing skill's failure-mode list is already
   front-facing and ports directly.

Estimate: half the work of the IFS conversion — the mechanism is already
written; it needs a rename, a contract generalization, and the steelman check.

---

## 2. field-forge

**The mechanism.** An opt-in overlay on the IFS kernel for hostile or evasive
fields — never a standalone pipeline. Three stages: (1) ground mapping:
hold contradictions live as parallel non-subordinating sentences, time-index
person-states (people as sequences of states, never fixed moral categories),
classify corrections as detail vs core-claim changes; (2) evasion-hypothesis
testing: name the responsibility that *may* be dodged with a support status
(supported / contested / unsupported), its apparent function, active tactics
(fogging, DARVO, jargon armor) each with discriminating evidence — and a
hypothesis protocol for shield-vocabulary (H-obfuscation / H-genuine / H-both;
"insufficient evidence to distinguish" is an honest finding); (3) handoff:
build 2–3 Take seeds from the audited ground and feed them into the kernel's
Diverge phase, then stand down. Six execution disciplines (hold contradictions
live, time-indexed person-states, detail-vs-core corrections, isolate motive,
test jargon claims, no softening) and a compact brief template. Only material
where evasion is *supported by discriminating evidence* gets the OBFUSCATION
tag; suspected-but-untested stays CLAIM.

**FHK coupling.** Light but real, and it's the layer Ryan named:
"Field Forge" with its Anvil/Hammer/Furnace stage names carries workshop
mystique, and the Hammer lineage traces to a `responsibility-obfuscation-probe`
skill built for therapy-speak armor in Ryan's personal context. The IFS
conversion already proved the decoupling pattern works: the mechanism is
general-purpose adversarial sociology; only the stage names and the
therapy-speak-centric framing needed replacing.

**What conversion would take.** A straightforward second conversion reusing the
IFS pattern:

1. Rename: `field-forge` → `evasion-probe` (done in the IFS package's overlay
   module as a preview); stage names Ground / Probe / Handoff (also previewed).
2. Generalize the jargon protocol: the current skill centers therapeutic
   vocabulary ("dysregulated," "holding space," "trauma response"); the
   front-facing version treats it as *one dialect among several* — corporate
   euphemism, legal fog, wellness-speak, therapy-speak — each run through the
   same H-obfuscation / H-genuine / H-both protocol. The de-biasing discipline
   (test, never pre-judge) is the load-bearing part and ports verbatim.
3. Keep the overlay contract honest: it stays an overlay on an interrogation
   kernel and refuses to run standalone — that architectural restraint is a
   feature, not a limitation, and should be code-enforced (raise if no kernel
   is attached).
4. Worked examples: one corporate-evasion field, one interpersonal field, one
   mixed. The Dana example from the IFS skill ports directly.
5. Tests: hypothesis-protocol state transitions (already prototyped in the IFS
   overlay tests — 5 green), plus contract tests for the stand-down rule.

Estimate: comparable to the IFS conversion's overlay portion — the hard
decisions (renames, generalization, hypothesis discipline) were already made
and validated in the IFS package's `overlay.py`.

---

## 3. FHK (Field Harmonic Key to the Thoth Tarot)

**The mechanism.** As best can be assessed from the repo (no FHK source files
exist locally — the canon lives in Ryan's Drive: the Paragon Chief SKILL.md,
the v5 blueprint, the Paragon register): FHK is a structured interpretive
framework for Thoth Tarot readings — named harmonic keys, spread conformance
rules (e.g., every position maps to a key, every position names its falsifier,
spreads close with synthesis not advice), and a Tribunal adjudication process
for conformance claims. The portable mechanism inside it is genuinely
interesting: **a versioned conformance framework with falsifiable
interpretation slots** — the falsifier-per-position requirement is a real
epistemic discipline most divination systems lack.

**FHK coupling.** Deep and structural, unlike the other two. FHK *is*
the private project: its ontology (harmonic keys, the Paragon, elemental
progressions) is Ryan's personal cosmology, and its conformance rules only make
sense inside that cosmology. The IFS skill's Tribunal example showed the
coupling precisely: adjudicating a tarot spread against FHK v5.0 canon is
meaningful only to someone inside the framework. You cannot extract FHK's
mechanism without either (a) dragging the cosmology along, or (b) abstracting
the framework *about* the framework.

**What conversion would take.** The (b) route is the only honest one, and it's
a design project, not a packaging job:

1. Abstract the portable idea: **"falsifiable interpretation frameworks"** —
   a schema for any interpretive practice (tarot, yes, but also scenario
   planning, red-team gaming, futures work) that requires named slots,
   per-position falsifiers, versioned canon, and conformance adjudication.
   The FHK v5.0 rules R1/R2/R3 become an *instance* of the schema, not the
   schema itself.
2. This requires Ryan's direct input on what generalizes and what doesn't —
   which parts of the harmonic-key ontology are load-bearing vs decorative.
   Only he can make those calls; the assistant should not invent the
   abstraction from outside.
3. The Tribunal/adjudication machinery from the IFS conversion provides the
   judging engine for free — conformance claims against any framework's
   stated standards are already covered by adjudication mode.
4. Do not attempt before the FHK canon is stable and Ryan has named what is
   canonical vs experimental. The Drive review (2026-09-23/24) deliberately
   left FHK-CANON frozen — respect that.

Estimate: the largest of the three by far, and gated on Ryan's design calls.
Recommended order: metacog next (smallest), field-forge after (pattern proven),
FHK last and only when he asks.
