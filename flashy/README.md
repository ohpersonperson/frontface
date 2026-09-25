# Flashy — persistent execution discipline

Prevents an agent from abandoning a build halfway. Locks the objective,
expands it into milestones, tracks live execution state, scans for drift
after every milestone, detects artificial stops ("here's a starting
point"), checkpoints honestly on genuine limits, and gates completion on
a quality checklist.

Mission rule: **a draft is not a delivery.** Completion is measured by
whether the user actually received the usable thing they asked for.

No prerequisites. The mechanism is the whole product.

*(Lineage: this is the front-facing conversion of the `flashy` skill from
Ryan's skill-suite, MIT — itself a port of an execution-discipline
protocol into skill format. What changed in the conversion is documented
in CHANGELOG.md.)*

## What it does

For any substantial build/create/write task, run the core loop — **lock,
move, verify**:

1. **Lock the objective.** Extract three things from the request: the
   stated deliverable, the implicit quality bar ("a login form" implies
   validation and error states even if unsaid), and the implicit scope
   boundaries. Once locked, the objective is immutable for the rest of the
   task: subtasks don't replace the mission, explanations don't replace
   execution, planning doesn't replace progress.
2. **Expand into milestones.** Objective → Major Milestones → Subtasks →
   Implementation Steps → Verification → Delivery.
3. **Track execution state.** A real state machine —
   `LOCKED → PLANNING → EXECUTING → VERIFYING → DONE`, with `BLOCKED`
   reachable from `EXECUTING`/`VERIFYING` — enforces the transition rules
   in code: no `VERIFYING → DONE` without every Quality Gate box checked,
   no silent `EXECUTING → PLANNING` without an explicit user-driven scope
   change, no `BLOCKED → EXECUTING` without an emitted checkpoint.
4. **Scan for drift after every milestone.** Four questions: still solving
   the original problem? wandered into explanation instead of building?
   forgot earlier requirements? would the user call this finished? On
   drift: discard the thread, restate the objective, resume from the last
   verified milestone.
5. **Detect artificial stops.** "Here's a starting point," "the rest follows
   similarly," "due to space..." — these are execution failures, not
   conclusions. The package scans output for the phrase list and flags
   them; the operator rewrites the impulse as **Continue Working.**
6. **Checkpoint honestly on genuine limits.** Context cutoff, tool error,
   or a low-confidence blocker with no safe default — emit a checkpoint
   with a resume token (`finish:<slug>-m<N>`) and continue next turn.
   Fatigue and "this feels done" are failures, not checkpoints.
7. **Verify before done.** The seven-box Quality Gate is a hard gate, not
   a vibe check. Any unchecked box = IN PROGRESS.

**Execution bias: build before briefing.** Build → Verify → Polish →
Explain. Understanding the problem well enough to act is the signal to
stop analyzing and start executing. And the end-of-response gate: a
response ending is not a task ending — if useful progress can still be
made, keep executing; don't hand the turn back for permission.

**Pause only for implementation-changing decisions** — choice of
database/language/framework, deployment target, a required credential, or
an ambiguity where two reasonable interpretations produce meaningfully
different deliverables. "Continue?" / "Should I keep going?" are never
valid stopping points.

## Why it works

Most abandoned builds don't fail — they *decay*. The objective quietly
gets replaced by a subtask. Explanation replaces execution. A response
"feels long enough" and stops. Flashy attacks the decay mechanically:

- **The state machine** makes the rules structural: you cannot declare
  done without the gate, cannot silently re-plan, cannot resume from a
  block without a checkpoint. The failure modes are `TransitionError`s,
  not suggestions.
- **Artificial-stop detection** catches the exact phrases long tasks die
  on — as a string scan, in code, every time.
- **The confidence engine** (High/Medium/Low) resolves ambiguity without
  blocking: High proceeds silently, Medium proceeds stating the
  assumption inline, only Low pauses. Most ambiguity never surfaces as a
  stop.
- **Checkpoints with resume tokens** make interruption recoverable without
  the user re-explaining anything — which removes the incentive to
  quietly abandon a task at a session break.

## Quickstart

Zero dependencies beyond Python 3.10+. No model, no network — this
package is pure discipline machinery.

```bash
cd flashy
python3 -m unittest discover -s tests     # 41 offline tests — prove the machinery first
python3 examples/demo_session.py          # watch a session run LOCKED -> DONE
```

Or use it as a library:

```python
from flashy import MissionSession

session = MissionSession(
    "Deliver a functional, usable, in-browser debate simulator.",
    slug="debate-sim",
)
session.plan(["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"])
session.start_executing()

for milestone in ["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"]:
    assert session.end_of_response_gate() == "continue"
    session.complete_milestone(milestone)
    print(session.dashboard())

session.begin_verification()
session.gate.check_all()
session.finish()  # raises unless every box is checked
assert session.machine.state == "DONE"
```

## Inputs, outputs

- **Input:** a locked objective (the finished thing, not the artifact
  type), milestones, constraints, pending decisions.
- **Output:** a driven session — dashboard state, checkpoints with resume
  tokens, and a DONE that actually means done. The package never writes
  files; your harness owns persistence.

## Worked examples

Three in `examples/`, a stranger can follow all of them:

1. `example-1-debate-simulator-walkthrough.md` — the full loop end to end
   on a browser debate simulator (ported from the original skill, unchanged).
2. `example-2-anti-patterns.md` — before/after pairs: artificial-stop
   language vs. the corrected continuation (ported, unchanged).
3. `example-3-flashy-session.md` — the machinery itself: every
   transition, gate, and checkpoint shown as the code enforces it. Run
   `demo_session.py` to watch it execute.

*All fields are constructed for teaching — they show the discipline's
shape, not real findings.*

## FAQ

**Does this make the model smarter?** No. It makes it finish things.
Execution discipline, not reasoning quality.

**Does it need an internet connection?** No. No model calls at all — the
41 unit tests and the demo run fully offline.

**What does it cost?** Nothing. Free, dependency-free, offline.

**When should it *not* fire?** Trivial tasks (a single short answer),
genuine user decisions pending, safety constraints, or real platform
limits. Never deactivate because a response "feels long enough."

## License

MIT. See LICENSE.
