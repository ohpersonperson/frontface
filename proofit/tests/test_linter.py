"""End-to-end linter tests: fixtures, ordering, rendering, fail-closed semantics."""
import os
import unittest

from fixtures import CLEAN
from proofit import lint_file, lint_text
from proofit.model import Violation

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.normpath(os.path.join(HERE, "..", "examples"))


class TestLinter(unittest.TestCase):
    def test_clean_passes(self):
        result = lint_text(CLEAN)
        self.assertTrue(result.passed)

    def test_broken_fixture_rejected(self):
        result = lint_file(os.path.join(EXAMPLES, "broken-runbook.md"))
        self.assertFalse(result.passed)
        self.assertEqual(len(result.violations), 18)

    def test_broken_fixture_covers_all_ten_rules(self):
        result = lint_file(os.path.join(EXAMPLES, "broken-runbook.md"))
        self.assertEqual(sorted({v.rule for v in result.violations}),
                         [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    def test_fixed_fixture_passes(self):
        result = lint_file(os.path.join(EXAMPLES, "fixed-runbook.md"))
        self.assertTrue(result.passed)
        self.assertEqual(result.violations, [])

    def test_violations_sorted_by_rule_then_location(self):
        result = lint_text(CLEAN.replace("## Validation & Closure", "## Removed"))
        keys = [(v.rule, v.location) for v in result.violations]
        self.assertEqual(keys, sorted(keys))

    def test_violation_render_format(self):
        v = Violation(rule=3, location="Step 4", message="2 actions in one Do",
                      fix="split into two steps")
        rendered = v.render()
        self.assertIn("RULE 3 [Step 4] ERROR", rendered)
        self.assertIn("2 actions in one Do", rendered)
        self.assertIn("fix: split into two steps", rendered)

    def test_empty_document_rejected(self):
        result = lint_text("")
        self.assertFalse(result.passed)
        self.assertIn(2, {v.rule for v in result.violations})
        self.assertIn(10, {v.rule for v in result.violations})


if __name__ == "__main__":
    unittest.main()
