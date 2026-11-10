# Runbook: [workflow name]

<!--
  Write the draft in this shape, then run:  python -m proofit lint this-file.md
  Fail-closed: ANY violation rejects the draft until fixed.
  One action per Do:. Name exact visible labels in **bold**. No new
  prerequisites after step 1. End with Validation & Closure, never a step.
-->

## Ground Rules & Prerequisites

### Required Baseline

[Exact starting condition: state, setup, preconditions.]

### Routing Architecture

[Delete this whole section if the workflow uses a single service.]

#### Input spec

[Exact format, structure, and constraints of the input.]

#### Service 1: [name]

- **When to use:** [exact condition or trigger]
- **Free-tier limits:** [rate limits, context window, monthly quota]
- **Prompt (verbatim):**
  ```
  [paste the exact prompt — no improvisation at runtime]
  ```
- **Expected output format:** [schema, field names, data types]

#### Service 2: [name]

- **When to use:** [exact condition or trigger]
- **Free-tier limits:** [rate limits, context window, monthly quota]
- **Prompt (verbatim):**
  ```
  [paste the exact prompt]
  ```
- **Expected output format:** [schema, field names, data types]

#### Rate limit handling

[What to do when a free-tier limit is hit: wait time, fallback service, graceful degradation.]

#### Error paths

[What to do if any service fails or returns unexpected data.]

### Needed Tools/Items

- Hardware: [e.g. a laptop with 8 GB RAM]
- Software: [e.g. Chrome, Python 3.12]
- Accounts: [e.g. a free-tier account on each service above — no API keys]
- Permissions: [e.g. admin on the target machine]
- Files: [e.g. ~/data/input.csv]
- Internet access: [e.g. required throughout]

### Expected Outcome

[What will exist after completion, and what it should contain.]

## Step-by-Step Directives

### Step 1: [action name]

**Do:** [exactly ONE action — "Open **Settings**.", never "Open Settings and click Display."]

**Look for:** [exact visual anchor or expected output, including what visibly changes]

**Verify:** [observable success condition — what the screen displays, what exists, what the output contains]

**If wrong:** [the most likely mistake for this step]

**Fix:** [the shortest recovery path — resume the guide instead of restarting when possible]

### Step 2: [action name]

**Do:** [one action]

**Look for:** [visual anchor]

**Verify:** [observable success condition]

**If wrong:** [most likely mistake]

**Fix:** [shortest recovery path]

## Validation & Closure

### Success Condition

[The exact final state. The reader should know with certainty the task succeeded.]

### Consistency Checkpoints

- [ ] All inputs met spec requirements (format, structure, constraints).
- [ ] Each service received the correct prompt and context.
- [ ] Each service's output matched the expected format.
- [ ] Error recovery was never triggered, OR was triggered and resolved correctly.
- [ ] The complete workflow produces the intended result.
