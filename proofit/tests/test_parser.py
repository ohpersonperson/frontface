"""Parser tests: the template-shaped Markdown reader."""
import unittest

from fixtures import CLEAN
from proofit.parser import parse


class TestParser(unittest.TestCase):
    def test_clean_parses_with_all_sections(self):
        rb = parse(CLEAN)
        self.assertTrue(rb.prereq_present)
        self.assertTrue(rb.steps_present)
        self.assertTrue(rb.validation_present)
        self.assertFalse(rb.glossary_present)
        self.assertEqual(len(rb.steps), 1)
        self.assertEqual(rb.steps[0].number, 1)
        self.assertEqual(rb.steps[0].do, "Click the **Go** button.")
        self.assertEqual(rb.steps[0].look_for, "The results panel.")
        self.assertEqual(rb.steps[0].verify, "The panel displays the report.")
        self.assertEqual(rb.steps[0].if_wrong, "Nothing loads.")
        self.assertEqual(rb.steps[0].fix, "Click **Go** again.")

    def test_section_order_recorded(self):
        rb = parse(CLEAN)
        kinds = [k for k, _, _ in rb.section_order]
        # the "# Runbook: test" H1 classifies as "other"; the three
        # template sections must follow in order
        self.assertEqual(kinds[1:], ["prereq", "steps", "validation"])

    def test_services_extracted_not_steps(self):
        doc = """# Runbook: x

## Ground Rules & Prerequisites

### Routing Architecture

#### Service 1: Alpha

- **When to use:** always
- **Free-tier limits:** 10 per day
- **Prompt (verbatim):**
  ```
  hi
  ```
- **Expected output format:** text

### Needed Tools/Items

- Hardware: a laptop

## Step-by-Step Directives

### Step 1: Go

**Do:** Click **Go**.

**Look for:** It loads.

**Verify:** The screen displays done.

**If wrong:** Stuck.

**Fix:** Retry.

## Validation & Closure

### Success Condition

Done.

### Consistency Checkpoints

- [ ] Done.
"""
        rb = parse(doc)
        self.assertEqual(len(rb.services), 1)
        self.assertEqual(rb.services[0].name, "Service 1: Alpha")
        self.assertIn("When to use", rb.services[0].body)

    def test_glossary_captured_as_section(self):
        doc = CLEAN.replace(
            "## Step-by-Step Directives",
            "### Glossary\n\n- Widget (a thing)\n\n## Step-by-Step Directives",
        )
        rb = parse(doc)
        self.assertTrue(rb.glossary_present)
        self.assertIn("Widget (a thing)", rb.glossary_text)

    def test_empty_document(self):
        rb = parse("")
        self.assertFalse(rb.prereq_present)
        self.assertFalse(rb.steps_present)
        self.assertFalse(rb.validation_present)
        self.assertEqual(rb.steps, [])

    def test_multiline_field_continuation(self):
        doc = CLEAN.replace(
            "**Do:** Click the **Go** button.",
            "**Do:** Click the\n**Go** button.",
        )
        rb = parse(doc)
        self.assertIn("Click the", rb.steps[0].do)
        self.assertIn("**Go** button.", rb.steps[0].do)

    def test_case_insensitive_field_names(self):
        doc = CLEAN.replace("**Do:**", "**do:**").replace("**Verify:**", "**VERIFY:**")
        rb = parse(doc)
        self.assertEqual(rb.steps[0].do, "Click the **Go** button.")
        self.assertEqual(rb.steps[0].verify, "The panel displays the report.")


if __name__ == "__main__":
    unittest.main()
