# Worked Example 1: "doing the work" — the probe that refuses to convict

The whole point of the hypothesis protocol is visible here: the flagged
phrase is therapy-speak, the old probe would have flagged it as armor by
policy, and the new probe concludes **H-genuine** — because the
evidence says so, not because the category was excused.

## The sample

> "I've been doing the work on my defensiveness — last week when you
> said the deadline slipped I got reactive, and I owe you an apology.
> Here's what I'm changing: I'll confirm dates in writing from now on."

## Step 1 — detection (candidate, not verdict)

`detect_markers` hits: `("therapy", "doing the work")`. That's a
candidate for testing. Nothing more.

## Step 2 — the hypothesis test

```python
flag = run_jargon_test(
    "doing the work", "therapy",
    evidence_for_obfuscation="",
    evidence_for_genuine=(
        "the phrase was followed within the same message by a named "
        "apology, an admission of a specific behavior (getting reactive), "
        "and a concrete changed procedure (confirm dates in writing)"
    ),
)
flag.record.verdict  # "H-genuine"
```

There is no discriminating evidence for H-obfuscation: the language does
not appear only under pressure (it's volunteered), and it is followed by
accountability, not topic change.

## Step 3 — tagging

```python
evidence_tag_for(flag.record)  # "CLAIM"
```

No OBFUSCATION tag — the gate only opens on supported H-obfuscation.

## What the old probe would have done

v1's mandatory flag: *"do not let it pass as neutral or virtuous."* It
would have flagged this apology as armor because of the vocabulary.
v2 tests the instance and concludes the language is doing what it says.

## The lesson

Category membership pointed at guilt; the evidence pointed at
accountability. The protocol follows the evidence. That's the entire
integrity rule of this package, in one example.
