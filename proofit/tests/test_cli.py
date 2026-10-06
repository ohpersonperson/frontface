"""CLI tests: exit codes are the fail-closed contract."""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, ".."))
EXAMPLES = os.path.join(PKG, "examples")

# Isolate the ledger: CLI test runs must not touch the user's real ledger.
ENV = dict(os.environ, PYTHONPATH=os.path.join(PKG, "src"),
           FRONTFACE_LEDGER_DIR=tempfile.mkdtemp(prefix="proofit-cli-test-"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "proofit", *args],
        capture_output=True, text=True, env=ENV,
    )


class TestCLI(unittest.TestCase):
    def test_lint_broken_exits_1(self):
        r = run_cli("lint", os.path.join(EXAMPLES, "broken-runbook.md"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECTED", r.stdout)
        self.assertIn("RULE 3", r.stdout)

    def test_lint_fixed_exits_0(self):
        r = run_cli("lint", os.path.join(EXAMPLES, "fixed-runbook.md"))
        self.assertEqual(r.returncode, 0)
        self.assertIn("PASS", r.stdout)

    def test_lint_missing_file_exits_2(self):
        r = run_cli("lint", os.path.join(EXAMPLES, "no-such-file.md"))
        self.assertEqual(r.returncode, 2)

    def test_template_prints(self):
        r = run_cli("template")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Step 1", r.stdout)
        self.assertIn("**Do:**", r.stdout)

    def test_help_exits_0(self):
        r = run_cli("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("lint", r.stdout)


# PARAM-PROOFIT-001: WARNINGs pass by default, fail under --strict;
# ERRORs fail in both modes.
R1_ONLY = """# Runbook: test

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

**Do:** Press Continue.

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

R3_ONLY = R1_ONLY.replace("**Do:** Press Continue.",
                          "**Do:** Click the **Go** button and export the report.")


class TestSeverityCLI(unittest.TestCase):
    def _write(self, content):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        tmp.write(content)
        tmp.close()
        self.addCleanup(os.unlink, tmp.name)
        return tmp.name

    def test_warnings_only_exit_0_by_default(self):
        r = run_cli("lint", self._write(R1_ONLY))
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARNING", r.stdout)
        self.assertIn("WARNINGS", r.stdout)

    def test_warnings_only_exit_1_with_strict(self):
        r = run_cli("lint", "--strict", self._write(R1_ONLY))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECTED", r.stdout)

    def test_errors_exit_1_in_both_modes(self):
        path = self._write(R3_ONLY)
        for args in (("lint", path), ("lint", "--strict", path)):
            r = run_cli(*args)
            self.assertEqual(r.returncode, 1, args)
            self.assertIn("REJECTED", r.stdout)
            self.assertIn("ERROR", r.stdout)


# PARAM-PROOFIT-002: sanctioned, auditable waiver via CLI.
R3_WAIVED = R3_ONLY + "\n# waiver(3): the click and the export are one operator gesture\n"
R3_WAIVER_NOREASON = R3_ONLY + "\n# waiver(3):\n"


class TestWaiverCLI(unittest.TestCase):
    def _write(self, content):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False)
        tmp.write(content)
        tmp.close()
        self.addCleanup(os.unlink, tmp.name)
        return tmp.name

    def test_waiver_exits_0_reason_visible(self):
        for args in (("lint",), ("lint", "--strict")):
            r = run_cli(*args, self._write(R3_WAIVED))
            self.assertEqual(r.returncode, 0, args)
            self.assertIn("WAIVER", r.stdout)
            self.assertIn("one operator gesture", r.stdout)

    def test_no_waiver_exits_1(self):
        r = run_cli("lint", self._write(R3_ONLY))
        self.assertEqual(r.returncode, 1)

    def test_waiver_without_reason_exits_1(self):
        r = run_cli("lint", self._write(R3_WAIVER_NOREASON))
        self.assertEqual(r.returncode, 1)
        self.assertIn("REJECTED", r.stdout)
        self.assertIn("INVALID", r.stdout)


if __name__ == "__main__":
    unittest.main()
