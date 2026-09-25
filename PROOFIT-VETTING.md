# proofit — vetting both design options

Analysis only. Nothing built. Read against the actual skill
(`~/workspace/skill-suite/skills/proofit/SKILL.md`): 10 rules, prose-only,
no code, no evals, no CHANGELOG, no live-use evidence. The skill's own
"Output Format" section already specifies the document shape a runbook
must take — that matters below.

## Rule-by-rule: what is actually codeable

| # | Rule | Codeable? | How |
|---|------|-----------|-----|
| 1 | Remove every assumption | Partial — phrase heuristics | Flag vague references ("the option", "the file", "press Continue" with no label), passive constructions ("is done automatically"). Cannot prove *completeness* — a linter can't know which assumptions the author silently held. |
| 2 | All prerequisites upfront | Yes — structure check | Require a Prerequisites section before step 1; require the 8 named fields (hardware, software, accounts, permissions, files, internet, free-tier limits, starting state). Detect "new prerequisite introduced in step N" by diffing named items per section. |
| 3 | One action per step | Yes — strongest check | Each step has exactly one `Do:` line; flag conjunctions of two verbs ("Open Settings and click Display"). Mechanical and reliable. |
| 4 | Concrete references | Mostly — phrase + format checks | Flag vague nouns ("the option", "select the file"); require visible labels (bold/quoted UI text) in `Do:` and `Look for:` lines. |
| 5 | Explain technical terms | Weak — format check only | Can require the `Term (definition)` pattern when a glossary exists, but detecting *undefined jargon* needs a glossary or a model. A linter can enforce the convention, not the judgment. |
| 6 | Verification after every milestone | Yes — structure check | Every milestone/section must end with a `Verify:` block containing observable language ("displays", "appears", "exists at", "contains"). |
| 7 | Immediate recovery | Yes — structure check | Every step/milestone carries `If wrong:` + `Fix:` blocks. (Which steps "reasonably" need one is judgment; the safe rule is *all of them*.) |
| 8 | Never skip state changes | Weak — verb-list heuristics | Can check that steps mention transitions ("opens", "appears", "closes", "begins"), but a linter cannot know what state changes a step *causes*. Completeness needs the author or a model. |
| 9 | Routing decisions upfront | Yes — schema check | Per named service: "when to use" condition, free-tier limits, verbatim prompt, expected output format/schema. Fully checkable as a structured spec. This is the skill's load-bearing rule and its most valuable check. |
| 10 | Finish with full validation | Yes — structure check | Document must end with success-condition + consistency-checklist section, never with a step. |

Score: **7 of 10 rules are mechanical structure/schema checks** (2, 3, 4, 6, 7, 9, 10).
Rules 1 and 8 degrade to phrase heuristics. Rule 5 is nearly all judgment.

## Option A — linter

**What it is.** Feed it a runbook draft; it emits violations (rule #, location,
description, severity, suggested fix).

**Input format.** This is the linter's unfair advantage: the skill *already
specifies the input*. The "Output Format" section defines the document shape —
Ground Rules & Prerequisites / Step-by-Step Directives (Step N: Do / Look for /
Verify / If wrong) / Validation & Closure. The linter parses Markdown following
that template. Freeform text input would need real NLP and is out of scope;
the honest constraint is "write it in the template, get it checked."

**Output format.** A violation list:
```
RULE 3 [step 4] ERROR — two actions in one Do: "Open Settings and click Display"
  fix: split into two steps
RULE 6 [milestone "Setup"] ERROR — milestone ends without a Verify: block
RULE 9 [service "NotebookLM"] WARNING — no free-tier limits stated
```
Severity: structural violations (missing sections, two-action steps,
no verification) = errors; heuristic flags (possible vague reference,
possible undefined term) = warnings.

**Testability offline.** Excellent — the best of any conversion in this suite.
Deterministic assertions, no model:
- feed a runbook with "Open Settings and click Display" → assert RULE 3 fires
- feed a milestone with no Verify block → assert RULE 6 fires
- feed a routing section naming two services with no limits block → assert RULE 9 fires
- feed a doc ending on a step → assert RULE 10 fires
- feed a clean runbook → assert zero violations

**Effort.** Small-medium. The checks are simple; the work is the Markdown
template parser and the violation catalog (turning 10 prose rules into precise
pass/fail conditions). That catalog *is* the design work.

**What breaks in translation.** The linter checks the runbook's *shape*, not its
*truth*: it can't tell whether the stated rate limit is correct, whether the
recovery path actually works, or whether the verbatim prompt is any good.
Rules 1, 5, 8 become phrase-list heuristics — useful tripwires, not proof.
Risk: compliance goes mechanical — authors write to satisfy the linter rather
than to actually remove assumptions.

## Option B — generator

**What it is.** Feed it a loose workflow description; it emits a locked-down
runbook skeleton with empty slots.

**Input format.** Free text or a small structured form: workflow name, list of
services, rough milestones/steps, known free-tier limits.

**Output format.** Markdown following the skill's Output Format with blank
slots and inline guidance comments:
```
### Step 1: [action name — ONE action only]
**Do:** [exactly one action; name the exact visible label]
**Look for:** [what the user should see]
**Verify:** [observable success condition]
**If wrong:** [most likely mistake] / **Fix:** [shortest recovery]
```
Plus a routing-spec block per named service and the validation checklist.

**Testability offline.** Moderate, but weak tests. You can assert the output
has all required sections in order, every step slot has all four fields,
every service gets a full routing block. But those assert *template
completeness* — the value lives in the filled-in content, which the generator
doesn't produce. The tests prove the form printed correctly.

**Effort.** Small. Dominated by template design. Honest assessment: this is a
static Markdown template with a CLI wrapper. Ship the template as a file and
you get ~90% of the value with none of the code.

**What breaks in translation.** A skeleton enforces nothing. The user can write
"Open Settings and click Display" in the `Do:` slot and the generator is
satisfied. It front-loads structure but the proofit promise — *zero-assumption,
verified, locked-down* — is entirely unenforced. Without a checker behind it,
it's a blank form with good headings.

## The dependency question

**Does the generator genuinely need the linter's rules implemented first?**
Not the linter's *code* — the linter's *rule catalog*. Both options need the
same design artifact: the 10 prose rules turned into a precise, machine-readable
spec (which sections exist, which fields are required, what a valid step looks
like). The linter implements that spec as checks; the generator implements it
as template structure. They share the catalog, not the implementation.

So "linter-first" is a sequencing convenience, not a technical dependency —
but it's still the right order, for three concrete reasons:
1. The linter is independently useful: it checks *existing* runbooks, including
   ones not written from any template. The generator only helps at authoring time.
2. The generator alone has near-zero enforcement value (see above). The linter
   is what makes the rules real.
3. Writing the linter's checks is what forces the rule catalog into existence.
   That catalog is the actual hard design work; the generator's template then
   falls out of it nearly for free.

**Third shape worth considering.** The genuinely best UX is probably neither
pure option: an **interactive authoring checklist** (wizard) — it emits the
skeleton like the generator *and* checks each field as it's filled like the
linter ("Step 3's Do field — one action or two?"). That's linter + generator
in an authoring loop. It's also the biggest build (interactive CLI, session
state). The cheap version of the same idea: **static template file + linter**.
Ship the Markdown template as a file (no generator code needed), point the
linter at drafts. That pair covers both options' value at the cost of one.

## Recommendation

**Build the linter (Option A), ship the template as a static file, skip the
generator as a code artifact.** Reasons:
- The linter is the only option that *enforces* anything; enforcement is the
  whole point of proofit.
- It's the most testable conversion in the suite — fully offline, deterministic,
  strong assertions.
- The input format is already specified by the skill itself; no format design
  needed.
- The generator's value collapses to a static file once the template exists.
- The rule catalog produced as a side effect is reusable (it's the spec the
  audit-record work and any future validator need).

## Sharpest remaining question for Ryan

Not linter-vs-generator anymore — that's settled by the evidence above.
The surviving question is the original one, sharpened: **how strict should the
linter be?** (a) **Fail-closed** — any structural violation (missing Verify
block, two-action step, incomplete routing spec) fails the draft until fixed;
(b) **advisory** — violations are warnings, the author decides. Fail-closed is
the honest translation of "unbreakable, zero-assumption directive," but it's
also the form-filling tax. Advisory is friendlier and risks becoming ignorable.
Secondary: is the interactive wizard worth the bigger build, or is
linter + static template enough?
