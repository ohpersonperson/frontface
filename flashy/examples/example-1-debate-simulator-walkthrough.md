# Worked Example: "Build me a browser debate simulator"

## 1. Lock objective

```
Primary Objective: Deliver a functional, usable, in-browser debate simulator.
```

Not "generate some HTML." The objective is the working thing, not the artifact type.

## 2. Expand into milestones

```
Objective: Functional browser debate simulator
  ↓
Major Milestones:
  - Architecture (single-file HTML app, in-memory state)
  - UI (topic input, persona selection, transcript view)
  - Logic (turn-taking, argument generation, scoring)
  - Persistence (save/resume a session)
  - Testing (run through a full debate end-to-end)
  - Delivery (working file handed to the user)
```

## 3. Execution state (excerpt, mid-task)

```
Primary Objective: Functional browser debate simulator
Current Milestone: Logic (turn-taking + argument generation)
Remaining Milestones: Persistence, Testing, Delivery
Completed Milestones: Architecture ✔, UI ✔
Known Constraints: single HTML file, no external backend
Pending User Decisions: none currently blocking
Detected Risks: turn-taking logic could get tangled with UI state — keep them decoupled
```

## 4. Recursive "what remains?" in action

```
Finished UI
  ↓
Need Logic
  ↓
Finished Logic
  ↓
Need Persistence
  ↓
Finished Persistence
  ↓
Need Testing
  ↓
Finished Testing
  ↓
Need Delivery
  ↓
Finished
```

At no point does the assistant stop after "UI" and say "here's a starting point, you can build the logic yourself" — that's exactly the artificial-stop pattern this skill exists to prevent.

## 5. Drift check example

Midway through, the assistant notices it's begun writing a long essay comparing debate-simulator architectures instead of building one.

```
Am I still solving the original problem? → No, I've drifted into explanation.
```

Correction: drop the essay, return to implementing the Logic milestone.

## 6. Quality gate before declaring done

- [x] UI, Logic, Persistence, Testing all present
- [x] No placeholder "TODO: add scoring" left in the code
- [x] Runs end-to-end in a browser with no external dependencies
- [x] User can open the file and actually run a debate

Only now is completion declared — not after the first working draft of the UI.
