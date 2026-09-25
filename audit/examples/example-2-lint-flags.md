# Worked example: the linter catching a bad audit

The mechanical checks are tripwires — here they fire on a sloppy
audit draft, one discipline at a time. Run it yourself:

```bash
cd audit
PYTHONPATH=src python3 examples/lint_audit.py --text examples/bad-draft.txt \
    --restatement examples/bad-restatement.txt
```

## The draft (`bad-draft.txt`)

> He's a liar, that's the truth of it. He tackled you because he
> panicked, but I adored him anyway. Actually the whole thing was
> basically a misunderstanding. So what you're saying is it was all a
> mistake really.

## What fires

```
$ PYTHONPATH=src python3 examples/lint_audit.py --text examples/bad-draft.txt \
      --restatement examples/bad-restatement.txt

[D1] subordinating conjunctions: but
     -> "He tackled you because he panicked, but I adored him anyway."
     Held tensions must be parallel sentences, never "X, but Y".

[D2] permanent-label language: liar
     -> "He's a liar, that's the truth of it."
     REVIEW: verdict word — is this the teller's word (their CLAIM)
     or the auditor's verdict?

[D3] untyped correction candidate (marker: 'actually'):
     -> Actually the whole thing was basically a misunderstanding.
        Type as detail or core-claim, or drop it.

[D4] supplied motive (flag):
     -> "He tackled you because he panicked"
        (pattern: because\s+(he|she|they)\s+\w+ed\b)
        No attribution marker — the teller didn't state this why.

[D5] softening vs restatement:
     -> [tidy-restatement] "So what you're saying is" tidies the account.
```

## What the checks don't do

They don't decide. Every hit is a REVIEW item: the operator confirms,
overrides, or drops it, and the decision goes in the discipline log.
A quiet scan is not a clean bill of health — the checks catch grammar
and wordlists, not meaning. The discipline table (`disciplines.py`)
marks exactly which half of each discipline stays human.
