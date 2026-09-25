"""Per-rule tests: each rule fires on its violation and stays quiet on clean input."""
import unittest

from fixtures import CLEAN
from proofit import lint_text
from proofit.parser import parse


def rules_of(text):
    return sorted({v.rule for v in lint_text(text).violations})


class TestR1Assumptions(unittest.TestCase):
    def test_bare_press_continue_fires(self):
        doc = CLEAN.replace("Click the **Go** button.", "Press Continue.")
        self.assertIn(1, rules_of(doc))

    def test_labeled_continue_is_clean(self):
        doc = CLEAN.replace(
            "Click the **Go** button.",
            "Click the blue **Continue** button in the bottom-right corner.",
        )
        self.assertNotIn(1, rules_of(doc))

    def test_automaticity_fires(self):
        doc = CLEAN.replace("The results panel.", "The report is generated automatically.")
        self.assertIn(1, rules_of(doc))

    def test_select_the_option_fires(self):
        doc = CLEAN.replace("Click the **Go** button.", "Select the option.")
        self.assertIn(1, rules_of(doc))


class TestR2Prerequisites(unittest.TestCase):
    def test_missing_section_fires(self):
        doc = CLEAN.replace("## Ground Rules & Prerequisites", "## Removed")
        self.assertIn(2, rules_of(doc))

    def test_missing_field_fires(self):
        doc = CLEAN.replace("- Permissions: write access to ~/out/\n", "")
        self.assertIn(2, rules_of(doc))

    def test_prereq_after_steps_fires(self):
        # swap the two sections
        prereq = CLEAN[CLEAN.index("## Ground Rules"):CLEAN.index("## Step-by-Step")]
        rest = CLEAN.replace(prereq, "")
        doc = rest.replace("## Validation & Closure", prereq + "\n## Validation & Closure")
        self.assertIn(2, rules_of(doc))

    def test_all_fields_present_is_clean(self):
        self.assertNotIn(2, rules_of(CLEAN))


class TestR3OneAction(unittest.TestCase):
    def test_two_actions_fire(self):
        doc = CLEAN.replace(
            "Click the **Go** button.", "Open Settings and click Display."
        )
        self.assertIn(3, rules_of(doc))

    def test_then_form_fires(self):
        doc = CLEAN.replace(
            "Click the **Go** button.", "Copy the text, then paste it into the box."
        )
        self.assertIn(3, rules_of(doc))

    def test_compound_noun_does_not_fire(self):
        # "and" joining nouns is one action, not two
        doc = CLEAN.replace(
            "Click the **Go** button.", "Copy the username and password."
        )
        self.assertNotIn(3, rules_of(doc))

    def test_missing_do_fires(self):
        doc = CLEAN.replace("**Do:** Click the **Go** button.\n\n", "")
        self.assertIn(3, rules_of(doc))

    def test_nonsequential_numbers_fire(self):
        doc = CLEAN.replace("### Step 1: Do the thing", "### Step 2: Do the thing")
        self.assertIn(3, rules_of(doc))

    def test_no_steps_fires(self):
        doc = CLEAN.replace("### Step 1: Do the thing", "### Not a step")
        self.assertIn(3, rules_of(doc))


class TestR4ConcreteRefs(unittest.TestCase):
    def test_bare_button_fires(self):
        doc = CLEAN.replace("The results panel.", "The button.")
        self.assertIn(4, rules_of(doc))

    def test_labeled_button_is_clean(self):
        self.assertNotIn(4, rules_of(CLEAN))

    def test_qualified_noun_is_clean(self):
        doc = CLEAN.replace("The results panel.", "A confirmation dialog appears.")
        self.assertNotIn(4, rules_of(doc))

    def test_open_the_file_fires(self):
        doc = CLEAN.replace("Click the **Go** button.", "Open the file.")
        self.assertIn(4, rules_of(doc))

    def test_open_named_file_is_clean(self):
        doc = CLEAN.replace("Click the **Go** button.", 'Open the file named **data.csv**.')
        self.assertNotIn(4, rules_of(doc))


class TestR5Terms(unittest.TestCase):
    GLOSSARY_DOC = CLEAN.replace(
        "## Step-by-Step Directives",
        "### Glossary\n\n{g}\n\n## Step-by-Step Directives",
    )

    def test_undefined_term_fires(self):
        doc = self.GLOSSARY_DOC.format(g="- Webhook: a callback URL")
        self.assertIn(5, rules_of(doc))

    def test_term_definition_pattern_is_clean(self):
        doc = self.GLOSSARY_DOC.format(g="- Webhook (a URL called on completion)")
        self.assertNotIn(5, rules_of(doc))

    def test_no_glossary_no_check(self):
        # detecting undefined jargon without a glossary is out of scope
        self.assertNotIn(5, rules_of(CLEAN))


class TestR6Verification(unittest.TestCase):
    def test_missing_verify_fires(self):
        doc = CLEAN.replace("**Verify:** The panel displays the report.\n\n", "")
        self.assertIn(6, rules_of(doc))

    def test_uncheckable_verify_fires(self):
        doc = CLEAN.replace(
            "The panel displays the report.", "it works."
        )
        self.assertIn(6, rules_of(doc))

    def test_observable_verify_is_clean(self):
        self.assertNotIn(6, rules_of(CLEAN))


class TestR7Recovery(unittest.TestCase):
    def test_missing_if_wrong_fires(self):
        doc = CLEAN.replace("**If wrong:** Nothing loads.\n\n", "")
        self.assertIn(7, rules_of(doc))

    def test_missing_fix_fires(self):
        doc = CLEAN.replace("**Fix:** Click **Go** again.\n", "")
        self.assertIn(7, rules_of(doc))

    def test_both_present_is_clean(self):
        self.assertNotIn(7, rules_of(CLEAN))


class TestR8StateChanges(unittest.TestCase):
    def test_undescribed_state_change_fires(self):
        doc = CLEAN.replace(
            "Click the **Go** button.", "Open the **Dashboard**."
        ).replace(
            "The results panel.", "The dashboard."
        ).replace(
            "The panel displays the report.", "The dashboard shows data."
        )
        # "shows" is observable (R6 clean) but not a transition word -> R8 fires
        self.assertIn(8, rules_of(doc))
        self.assertNotIn(6, rules_of(doc))

    def test_described_state_change_is_clean(self):
        doc = CLEAN.replace(
            "Click the **Go** button.", "Open the **Dashboard**."
        ).replace("The results panel.", "The dashboard window opens.")
        self.assertNotIn(8, rules_of(doc))

    def test_non_state_verb_skipped(self):
        self.assertNotIn(8, rules_of(CLEAN))


class TestR9Routing(unittest.TestCase):
    ROUTING = """
### Routing Architecture

#### Input spec

Text.

#### Service 1: Alpha

{alpha}

#### Service 2: Beta

- **When to use:** always
- **Free-tier limits:** 10 per day
- **Prompt (verbatim):**
  ```
  hi
  ```
- **Expected output format:** text

#### Rate limit handling

Wait an hour.

#### Error paths

Retry once.
"""
    ALPHA_FULL = """- **When to use:** always
- **Free-tier limits:** 10 per day
- **Prompt (verbatim):**
  ```
  hi
  ```
- **Expected output format:** text"""

    def _doc_with_routing(self, alpha):
        routing = self.ROUTING.format(alpha=alpha)
        return CLEAN.replace("### Expected Outcome", routing + "\n### Expected Outcome")

    def test_complete_specs_are_clean(self):
        self.assertNotIn(9, rules_of(self._doc_with_routing(self.ALPHA_FULL)))

    def test_missing_limits_fires(self):
        alpha = self.ALPHA_FULL.replace("- **Free-tier limits:** 10 per day\n", "")
        self.assertIn(9, rules_of(self._doc_with_routing(alpha)))

    def test_missing_prompt_fires(self):
        alpha = "\n".join(
            l for l in self.ALPHA_FULL.splitlines() if "Prompt" not in l and "hi" not in l
        )
        self.assertIn(9, rules_of(self._doc_with_routing(alpha)))

    def test_missing_rate_limit_handling_fires(self):
        doc = self._doc_with_routing(self.ALPHA_FULL).replace(
            "#### Rate limit handling\n\nWait an hour.\n\n", ""
        )
        self.assertIn(9, rules_of(doc))

    def test_no_services_no_check(self):
        self.assertNotIn(9, rules_of(CLEAN))


class TestR10Validation(unittest.TestCase):
    def test_missing_section_fires(self):
        doc = CLEAN.replace("## Validation & Closure", "## Removed")
        self.assertIn(10, rules_of(doc))

    def test_ending_on_step_fires(self):
        doc = CLEAN + "\n### Step 2: Extra\n\n**Do:** Click **X**.\n"
        self.assertIn(10, rules_of(doc))

    def test_missing_success_condition_fires(self):
        doc = CLEAN.replace("### Success Condition\n\n", "")
        self.assertIn(10, rules_of(doc))

    def test_missing_checklist_fires(self):
        doc = CLEAN.replace("- [ ] The input met the spec.\n", "").replace(
            "- [ ] The workflow produced the intended result.\n", ""
        )
        self.assertIn(10, rules_of(doc))

    def test_complete_validation_is_clean(self):
        self.assertNotIn(10, rules_of(CLEAN))


class TestVettingSketches(unittest.TestCase):
    """The exact scenarios from the design vetting."""

    def test_open_settings_and_click_display(self):
        doc = CLEAN.replace("Click the **Go** button.", "Open Settings and click Display.")
        violations = [v for v in lint_text(doc).violations if v.rule == 3]
        self.assertTrue(violations)
        self.assertIn("2 actions", violations[0].message)

    def test_milestone_without_verify(self):
        doc = CLEAN.replace("**Verify:** The panel displays the report.\n\n", "")
        self.assertTrue([v for v in lint_text(doc).violations if v.rule == 6])

    def test_two_services_no_limits(self):
        doc = CLEAN.replace(
            "### Expected Outcome",
            "### Routing Architecture\n\n"
            "#### Service 1: A\n\n- **When to use:** x\n\n"
            "#### Service 2: B\n\n- **When to use:** y\n\n"
            "### Expected Outcome",
        )
        r9 = [v for v in lint_text(doc).violations if v.rule == 9]
        self.assertTrue(any("free-tier limits" in v.message for v in r9))

    def test_doc_ending_on_step(self):
        doc = CLEAN + "\n### Step 9: Last\n"
        self.assertTrue([v for v in lint_text(doc).violations if v.rule == 10])

    def test_clean_runbook_zero_violations(self):
        result = lint_text(CLEAN)
        self.assertTrue(result.passed)
        self.assertEqual(result.violations, [])


if __name__ == "__main__":
    unittest.main()
