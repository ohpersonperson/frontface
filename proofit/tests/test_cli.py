"""CLI tests: exit codes are the fail-closed contract."""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.normpath(os.path.join(HERE, ".."))
EXAMPLES = os.path.join(PKG, "examples")

ENV = dict(os.environ, PYTHONPATH=os.path.join(PKG, "src"))


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


if __name__ == "__main__":
    unittest.main()
