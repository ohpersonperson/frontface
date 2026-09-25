"""Shared fixtures for the proofit test suite."""
import unittest

CLEAN = """# Runbook: test

## Ground Rules & Prerequisites

### Required Baseline

Starting state: clean machine.

### Needed Tools/Items

- Hardware: a laptop
- Software: a browser
- Accounts: a free account
- Permissions: write access to ~/out/
- Files: ~/in/data.csv
- Internet access: required throughout
- Free-tier limits: 100 requests per day

### Expected Outcome

A report exists.

## Step-by-Step Directives

### Step 1: Do the thing

**Do:** Click the **Go** button.

**Look for:** The results panel.

**Verify:** The panel displays the report.

**If wrong:** Nothing loads.

**Fix:** Click **Go** again.

## Validation & Closure

### Success Condition

The report exists at ~/out/report.md.

### Consistency Checkpoints

- [ ] The input met the spec.
- [ ] The workflow produced the intended result.
"""
