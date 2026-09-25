# Worked example: the lint cycle (broken → rejected → fixed → passes)

A runbook draft for a weekly changelog workflow, checked with:

```
python -m proofit lint broken-runbook.md
```

## 1. The broken draft

`broken-runbook.md` is a plausible first draft. It reads fine. The linter
rejects it with **18 violations across all ten rules**:

```
RULE 1 [Step 1 (look_for)] ERROR — assumes automatic behavior: "The draft text. Formatting is done automatically."
RULE 1 [Step 3 (do)] ERROR — unlabeled directive assumes the reader knows where/what: "Press Continue."
RULE 2 [Ground Rules & Prerequisites] ERROR — required prerequisite field missing: permissions
RULE 2 [Ground Rules & Prerequisites] ERROR — required prerequisite field missing: internet access
RULE 3 [Step 1] ERROR — 2 actions in one Do: "Open the editor and load the draft file."
RULE 4 [Step 3 (look_for)] ERROR — UI element named without a visible label: "The button."
RULE 5 [glossary (line 3)] ERROR — term without an inline definition: "- Webhook: a callback URL"
RULE 6 [Step 2 (Verify)] ERROR — verification is not objectively checkable: "it works."
RULE 6 [Step 3] ERROR — step ends without a Verify: block
RULE 7 [Step 2] ERROR — step has no If wrong: block
RULE 7 [Step 2] ERROR — step has no Fix: block
RULE 8 [Step 1] ERROR — state-changing action with no described state change
RULE 9 [Routing / Service 1: ChangelogGen] ERROR — service spec missing: free-tier limits
RULE 9 [Routing Architecture] ERROR — no rate-limit handling
RULE 9 [Routing Architecture] ERROR — no error paths
RULE 10 [Validation & Closure] ERROR — no Success Condition
RULE 10 [Validation & Closure] ERROR — no consistency checklist
RULE 10 [document] ERROR — a step appears after Validation & Closure

REJECTED: 18 violations — fix and re-run.
```

Exit code 1. Nothing about this draft passes until every violation is fixed —
that is the fail-closed contract.

A few worth noticing:

- **RULE 3** catches the classic: "Open the editor and load the draft file"
  is two actions wearing one step's clothes.
- **RULE 10** catches the structural sin the author didn't notice: a
  `### Step 4` heading sitting *after* Validation & Closure, so the document
  ends on an action.
- **RULE 6** rejects "it works." as a verification — it is not observable,
  not checkable, and proves nothing.

## 2. The fixed draft

`fixed-runbook.md` is the same workflow rewritten against the violations:
prerequisites completed, steps split to one action each, every label named
in bold, every step carrying Look for / Verify / If wrong / Fix, both
services fully specified with rate-limit handling and error paths, and the
document ending on Validation & Closure with a success condition and a
checklist.

```
$ python -m proofit lint fixed-runbook.md
PASS: no violations — the runbook is locked down.
```

Exit code 0.

## 3. What the linter does not do

It checks the runbook's **shape**, not its **truth**. It cannot tell whether
the stated rate limit is correct, whether the recovery path actually works,
or whether the verbatim prompt is any good. A draft can pass all ten rules
and still describe a bad workflow — the linter guarantees the workflow is
*fully specified*, not that it is *wise*.
