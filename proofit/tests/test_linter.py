"""End-to-end linter tests: fixtures, ordering, rendering, fail-closed semantics."""
import os
import unittest

from fixtures import CLEAN
from proofit import lint_file, lint_text
from proofit import parser
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


# PARAM-PROOFIT-001: heuristic (R1, R8) and convention (R5) violations are
# WARNINGs — listed, never fail-closed. Structural rules stay ERROR.
R1_ONLY = CLEAN.replace(
    "**Do:** Click the **Go** button.", "**Do:** Press Continue.")
R3_ONLY = CLEAN.replace(
    "**Do:** Click the **Go** button.",
    "**Do:** Click the **Go** button and export the report.")


class TestSeverity(unittest.TestCase):
    def test_heuristic_rules_are_warnings(self):
        for rule in (1, 5, 8):
            v = Violation(rule=rule, location="x", message="m", fix="f")
            self.assertEqual(v.severity, "WARNING", f"rule {rule}")

    def test_structural_rules_are_errors(self):
        for rule in (2, 3, 4, 6, 7, 9, 10):
            v = Violation(rule=rule, location="x", message="m", fix="f")
            self.assertEqual(v.severity, "ERROR", f"rule {rule}")

    def test_render_shows_severity(self):
        v = Violation(rule=1, location="Step 1", message="m", fix="f")
        self.assertIn("WARNING", v.render())
        self.assertNotIn("ERROR", v.render())

    def test_warnings_only_pass_by_default(self):
        result = lint_text(R1_ONLY)
        self.assertEqual([v.rule for v in result.violations], [1])
        self.assertEqual([v.severity for v in result.violations], ["WARNING"])
        self.assertTrue(result.passed)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 1)

    def test_warnings_only_fail_when_strict(self):
        result = lint_text(R1_ONLY, strict=True)
        self.assertFalse(result.passed)

    def test_structural_fails_in_both_modes(self):
        for strict in (False, True):
            result = lint_text(R3_ONLY, strict=strict)
            self.assertFalse(result.passed)
            self.assertEqual([v.severity for v in result.violations], ["ERROR"])


# PARAM-PROOFIT-002: sanctioned, auditable waiver.
R3_WAIVED = R3_ONLY + "\n# waiver(3): the click and the export are one operator gesture\n"
R3_WAIVER_NOREASON = R3_ONLY + "\n# waiver(3):\n"
R1_WAIVED = R1_ONLY + "\n# waiver(1): assumptions are explicit in the prereq baseline\n"


class TestWaiver(unittest.TestCase):
    def test_valid_waiver_excuses_error(self):
        result = lint_text(R3_WAIVED)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.violations), 1)
        v = result.violations[0]
        self.assertTrue(v.waived)
        self.assertIn("one operator gesture", v.waiver_reason)
        # Severity still renders — the waiver excuses, it doesn't regrade.
        self.assertEqual(v.severity, "ERROR")
        self.assertIn("ERROR", v.render())
        self.assertIn("waived", v.render())

    def test_valid_waiver_excuses_in_strict_mode(self):
        result = lint_text(R3_WAIVED, strict=True)
        self.assertTrue(result.passed)

    def test_waiver_logged_in_lint_record(self):
        result = lint_text(R3_WAIVED)
        self.assertEqual(len(result.waivers), 1)
        w = result.waivers[0]
        self.assertTrue(w.valid)
        self.assertEqual(w.rule, 3)
        rendered = result.render()
        self.assertIn("WAIVER rule 3", rendered)
        self.assertIn("one operator gesture", rendered)

    def test_no_waiver_still_fails(self):
        result = lint_text(R3_ONLY)
        self.assertFalse(result.passed)
        self.assertFalse(result.violations[0].waived)

    def test_waiver_without_reason_rejected(self):
        result = lint_text(R3_WAIVER_NOREASON)
        self.assertFalse(result.passed)
        self.assertEqual(len(result.waivers), 1)
        self.assertFalse(result.waivers[0].valid)
        self.assertFalse(result.violations[0].waived)
        self.assertIn("INVALID", result.render())

    def test_waiver_excuses_warning_too(self):
        for strict in (False, True):
            result = lint_text(R1_WAIVED, strict=strict)
            self.assertTrue(result.passed)
            self.assertTrue(result.violations[0].waived)

    def test_unmatched_waiver_is_valid_but_unused(self):
        result = lint_text(R1_ONLY + "\n# waiver(9): no routing issue here\n")
        self.assertTrue(result.waivers[0].valid)
        self.assertFalse(result.violations[0].waived)
        self.assertTrue(result.passed)  # R1 is WARNING: passes anyway

    def test_trailing_waiver_line_is_metadata_not_structure(self):
        # Regression (found during implementation): a trailing `# waiver(3)`
        # line matches HEADING_RE and was parsed as an H1, tripping rule 10.
        # Waiver lines are metadata, never document structure.
        rb = parser.parse(R3_WAIVED)
        titles = [t for _, t, _ in rb.section_order]
        self.assertNotIn(
            "waiver(3): the click and the export are one operator gesture",
            titles,
        )
        result = lint_text(R3_WAIVED)
        self.assertNotIn(10, {v.rule for v in result.violations})


if __name__ == "__main__":
    unittest.main()
