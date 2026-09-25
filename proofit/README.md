# proofit — fail-closed linter for locked-down runbooks

A runbook is a step-by-step procedure written so tightly that two different
people following it do the same thing and get the same result. proofit checks
a runbook draft against ten rules of workflow discipline — and **rejects the
draft if any rule is violated**. No warnings, no advisories. Fail-closed:
exit 1 until it's fixed, exit 0 when it's locked down.

No prerequisites. You don't need to know anything about this project's
history or any framework. The mechanism is the whole product.

*(Lineage: this is the front-facing conversion of the `proofit` skill from
Ryan's skill-suite, MIT. What changed in the conversion is documented in
CHANGELOG.md.)*

## What it does

You write the runbook as Markdown in the template shape
(`templates/runbook-template.md` — or print it with `python -m proofit
template`):

- **Ground Rules & Prerequisites** — baseline, routing specs per service,
  tools/items, expected outcome
- **Step-by-Step Directives** — numbered steps, each with **Do:** /
  **Look for:** / **Verify:** / **If wrong:** / **Fix:**
- **Validation & Closure** — success condition plus consistency checkpoints

The linter parses that shape and runs ten checks:

| # | Rule | How it's checked |
|---|------|------------------|
| 1 | Remove every assumption | Heuristic: flags bare unlabeled directives ("Press Continue") and claims of automatic behavior ("is done automatically"). Narrow by design — see below. |
| 2 | All prerequisites upfront | Structure: the section must exist before step 1 and cover all eight fields (hardware, software, accounts, permissions, files, internet access, free-tier limits, starting state). |
| 3 | One action per step | Structure: each `Do:` holds exactly one verb-led action; steps numbered 1..N. |
| 4 | Concrete references | Flags bare UI nouns ("the button") and vague references ("open the file") with no visible label. Qualified nouns ("a confirmation dialog") don't fire. |
| 5 | Explain technical terms | Convention: where a glossary exists, every entry must match `Term (definition)`. Detecting undefined jargon *without* a glossary is out of scope — stated, not pretended. |
| 6 | Verification after every milestone | Structure: every step ends with a `Verify:` block in observable language ("displays", "exists", "contains"). |
| 7 | Immediate recovery | Structure: every step carries `If wrong:` + `Fix:`. |
| 8 | Never skip state changes | Heuristic: a `Do:` starting with a state-changing verb (open, close, install, …) must describe the resulting state in transition language ("a dialog appears"). Narrow by design. |
| 9 | Routing decisions upfront | Schema: per named service — when to use, free-tier limits, verbatim prompt, expected output format — plus rate-limit handling and error paths. |
| 10 | Finish with full validation | Structure: the document ends with Validation & Closure (never a step), with a success condition and a checklist. |

## Why it works

Most workflow failures are specification failures, not execution failures.
Someone improvises mid-stream because the routing decision was never written
down. Someone skips a prerequisite because it was revealed in step 9. Someone
combines two actions in one step and does them in the wrong order. The ten
rules attack exactly these failure modes, and the linter makes them
mechanical: the rules that can be checked as structure *are* checked as
structure, so compliance isn't a matter of discipline — it's a matter of
passing the gate.

Two rules (1 and 8) are phrase-list heuristics — tripwires, not proof. Under
fail-closed they still block, so they are deliberately narrow: they fire only
on clear hits. A foolproof gate that misfires on good drafts isn't foolproof,
it's a tax. The narrowness is documented in the code and tested.

## Quickstart

Zero dependencies beyond Python 3.10+.

```bash
cd proofit
PYTHONPATH=src python3 -m unittest discover -s tests   # 65 offline tests
```

Lint a draft:

```bash
PYTHONPATH=src python3 -m proofit lint my-runbook.md
# violations listed as RULE n [location] ERROR — message + fix
# exit 1: REJECTED — fix and re-run
# exit 0: PASS — the runbook is locked down
```

Print the blank template:

```bash
PYTHONPATH=src python3 -m proofit template > my-runbook.md
```

Or use it as a library:

```python
from proofit import lint_text

result = lint_text(open("my-runbook.md").read())
if not result.passed:
    for v in result.violations:
        print(v.render())
```

See `examples/run_local.py` for the full cycle (broken draft rejected,
fixed draft passes).

## Inputs, outputs

- **Input:** a runbook draft in Markdown following the template shape.
- **Output:** a list of violations (`RULE n [location] ERROR — message`
  plus a `fix:` line), and an exit code: 1 if any violation exists, 0 if
  clean. Fail-closed — there is no warning level.

## Worked example

`examples/example-1-lint-cycle.md` — the same workflow as a broken draft
(18 violations, rejected) and a fixed draft (passes). The fixture files
`examples/broken-runbook.md` and `examples/fixed-runbook.md` are the
actual inputs; the test suite asserts the broken one yields exactly 18
violations across all ten rules and the fixed one yields zero.

## FAQ

**Does it check whether the runbook is *correct*?** No. It checks the
runbook's shape, not its truth — it can't tell whether a stated rate limit
is right or a recovery path works. It guarantees the workflow is fully
specified, not that it is wise.

**What if a heuristic fires on a good draft?** Rules 1 and 8 are narrow by
design, but false positives are possible (documented in `checks.py`). If
one blocks a draft you believe is correct, the honest move is to reword past
the tripwire — the rewording is usually clearer anyway — not to fork the
linter.

**Why fail-closed instead of warnings?** Because the skill's promise is
"unbreakable, zero-assumption directive." A warning you can ignore is the
opposite of idiot-proof. The gate is the product.

**Single-service workflow — do I need the routing section?** No. Rule 9 is
vacuous when no services are named. Delete the Routing Architecture section
and the check passes silently.

## License

MIT. See LICENSE.
