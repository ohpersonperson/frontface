# Worked Example: a Flashy session, start to DONE

A stranger-readable walkthrough of one session driving a build to
completion. The build is the debate simulator from the ported walkthrough;
what's new here is the *machinery* — every transition, gate, and checkpoint
shown as the code enforces it.

*(Run `python3 examples/demo_session.py` to watch this execute for real —
no model, no network.)*

## 1. Lock the objective

```python
session = MissionSession(
    "Deliver a functional, usable, in-browser debate simulator.",
    slug="debate-sim",
    implicit_quality_bar="single HTML file, runs end-to-end with no backend",
    scope_boundaries="no user accounts, no persistence beyond save/resume",
)
```

The objective is the *finished thing*, not the artifact type. Not "generate
HTML" — a functional simulator the user can open and run.

## 2. Expand into milestones, enter the state machine

```python
session.plan(["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"])
session.start_executing()
# state: LOCKED -> PLANNING -> EXECUTING
```

`plan()` runs once, from LOCKED. The first milestone becomes active.

## 3. The dashboard, refreshed after every milestone

```
OBJECTIVE  -> Deliver a functional, usable, in-browser debate simulator.
NOW        -> Logic
DONE       -> Architecture, UI
NEXT       -> Continue: Logic
BLOCKERS   -> none
```

NEXT is always exactly one action — never a pile of possible futures.

## 4. The end-of-response gate

After each milestone: is the objective complete? No → can useful progress
still be made? Yes → keep executing. The gate returns `"continue"` until
no milestones remain, then `"verify"` — never "done" on its own authority.

## 5. Drift, caught mid-task

Midway through Logic, output starts reading like an essay comparing
debate-simulator architectures instead of building one. The four drift
questions:

- Am I still solving the original problem? → **No. Drifted into explanation.**

Correction, per the snap-back rule: discard the essay, restate the locked
objective, resume from the last verified milestone. No apology theater.

## 6. An artificial stop, caught by the detector

A draft line sneaks in: *"Here's a starting point — you can expand this
for scoring."*

```python
>>> detect_artificial_stop("Here's a starting point — you can expand this for scoring.")
["here's a starting point", "you can expand this"]
```

Internally rewritten as: **Continue Working.** The scoring gets built.

## 7. A genuine limit, checkpointed honestly

Suppose the session actually hits a context limit during Testing. This is
the *only* honest stop:

```
FLASHY CHECKPOINT
OBJECTIVE  -> Deliver a functional, usable, in-browser debate simulator.
DONE       -> Architecture, UI, Logic, Persistence
CURRENT    -> Testing
REMAINING  -> Testing, Delivery
NEXT       -> Continue: Testing
RESUME     -> finish:debate-sim-m4

Continuing...
```

The checkpoint is emitted, the session blocks, and on resume the token
`finish:debate-sim-m4` reconstructs where things stood — no re-explaining.

## 8. Verification: the Quality Gate, no partial credit

```python
session.begin_verification()   # EXECUTING -> VERIFYING
session.gate.check_all()       # all seven boxes
session.finish()               # VERIFYING -> DONE
```

Try `session.finish()` with a box unchecked and it raises — status stays
IN PROGRESS. There is no "mostly done."

## What this example shows a stranger

1. **The state machine is the discipline.** The rules (no silent
   re-planning, no DONE without the gate, no resume without a checkpoint)
   are enforced in code, not suggested in prose.
2. **Detection is codeable; judgment stays explicit.** Artificial-stop
   phrases are a string scan. Drift is four questions the operator runs —
   the package carries the questions and the snap-back rule.
3. **Checkpoints are for genuine limits only.** Fatigue and "feels done"
   are failures, not checkpoints.
4. **Only Low confidence pauses.** High and Medium keep moving. "Continue?"
   is never a valid stopping point.
