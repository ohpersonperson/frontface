"""Tests for the capture-format contract.

The load-bearing property: answers survive formatting byte-identical —
contradictions, typos, markup, and all. The function may add structure
around the answers; it may never touch them.
"""

import unittest

from meminqu.entry import (
    ENTRY_MARKER,
    Response,
    answers_preserved_verbatim,
    format_entry,
)
from meminqu.registers import RegisterError


def sample_responses():
    return [
        Response(
            register="direct",
            question="State the single most important fact in this domain right now.",
            answer="We lost the Meridian contract on Tuesday. Nobody told me until Friday.",
        ),
        Response(
            register="reflective",
            question="What does this domain feel like from the inside this week?",
            answer="Like treading water in a suit. Heavy. I keep checking my phone.",
        ),
        Response(
            register="contrastive",
            question="What is *not* true here, though it might look that way?",
            # Deliberately messy: typo, contradiction, markdown, unicode.
            answer="Its NOT true that were fine — we're not. Budget says **ok**; reality says ≠ ok. Fix teh report.",
        ),
    ]


class TestFormatEntry(unittest.TestCase):
    def test_header_marker_and_domain(self):
        body = format_entry("work", sample_responses())
        self.assertIn(f"{ENTRY_MARKER} — work", body)

    def test_register_list_matches_questions_asked(self):
        body = format_entry("work", sample_responses())
        first_line = body.splitlines()[0]
        self.assertIn("direct", first_line)
        self.assertIn("reflective", first_line)
        self.assertIn("contrastive", first_line)
        self.assertNotIn("sparse", first_line)

    def test_answers_verbatim(self):
        responses = sample_responses()
        body = format_entry("work", responses)
        self.assertTrue(answers_preserved_verbatim(body, responses))
        for r in responses:
            # Byte-identical containment, not fuzzy matching.
            self.assertIn(r.answer, body)
            self.assertEqual(body.count(r.answer), 1)

    def test_contradiction_and_typos_survive(self):
        messy = Response(
            register="sparse",
            question="Three words. No more.",
            answer="tired tired tyrde",  # typo kept, not "fixed"
        )
        body = format_entry("personal", [messy])
        self.assertIn("tired tired tyrde", body)

    def test_skipped_question_recorded_not_silent(self):
        responses = [
            Response(register="direct", question="Q1?", answer="A1."),
            Response(register="temporal", question="Q2?", answer=""),
            Response(register="temporal", question="Q3?", answer=None),
        ]
        body = format_entry("work", responses)
        self.assertIn("A1.", body)
        self.assertEqual(body.count("_[no answer]_"), 2)

    def test_empty_responses_rejected(self):
        with self.assertRaises(ValueError):
            format_entry("work", [])

    def test_unknown_register_rejected(self):
        with self.assertRaises(RegisterError):
            format_entry("work", [Response("nope", "Q?", "A.")])


if __name__ == "__main__":
    unittest.main()
