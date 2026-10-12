"""Tests for the interview session against memdate.

Run with both packages importable, e.g. from this staging tree::

    PYTHONPATH=../memdate/src:src python3 -m unittest discover -s tests

The session is a thin runner over memdate: these tests prove the
wiring — domains inherited from the config, verbatim capture through
the library, skips, reassignment, and the completion report.
"""

import os
import tempfile
import unittest

from meminqu.entry import ENTRY_MARKER, Response
from meminqu.session import InterviewSession, SessionError

from memdate import (
    ConfigError,
    InterpretationError,
    MemoryConfig,
    capture,
    read_raw,
)


def make_config(tmpdir, **kwargs):
    return MemoryConfig(root=tmpdir, **kwargs)


def responses_for(registers):
    return [
        Response(
            register=reg,
            question=f"Sample question in the {reg} register?",
            answer=f"Sample verbatim answer for {reg}. Kept exactly: teh typo stays.",
        )
        for reg in registers
    ]


class SessionTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config = make_config(self.tmp.name)


class TestDomainInheritance(SessionTestCase):
    def test_domains_come_from_config(self):
        session = InterviewSession(self.config)
        # memdate's neutral defaults — no domain list declared here.
        self.assertEqual(session.domains, self.config.domains)
        self.assertNotIn("fhk", session.domains)
        self.assertNotIn("tribunal", session.domains)

    def test_custom_config_domains_used(self):
        config = make_config(
            self.tmp.name, domains=("alpha", "beta")
        )
        session = InterviewSession(config)
        self.assertEqual(session.domains, ("alpha", "beta"))

    def test_cycle_subset_must_be_config_known(self):
        with self.assertRaises(ConfigError):
            InterviewSession(self.config, domains=("work", "nope"))

    def test_start_unknown_domain_rejected(self):
        session = InterviewSession(self.config)
        with self.assertRaises(ConfigError):
            session.start_domain("fhk")

    def test_start_domain_outside_cycle_rejected(self):
        session = InterviewSession(self.config, domains=("work",))
        with self.assertRaises(SessionError):
            session.start_domain("personal")


class TestCaptureWiring(SessionTestCase):
    def test_full_cycle_writes_raw_files(self):
        session = InterviewSession(self.config, domains=("personal", "work"))
        for domain in ("personal", "work"):
            registers = session.start_domain(domain)
            result = session.submit_answers(domain, responses_for(registers), capture_mode="VERBATIM")
            self.assertTrue(result.path.endswith(f"{domain}/raw.md"))
        for domain in ("personal", "work"):
            raw = read_raw(self.config, domain)
            self.assertIsNotNone(raw)
            self.assertIn(f"{ENTRY_MARKER} — {domain}", raw)

    def test_answers_verbatim_in_raw(self):
        session = InterviewSession(self.config, domains=("work",))
        registers = session.start_domain("work")
        answers = responses_for(registers)
        session.submit_answers("work", answers, capture_mode="VERBATIM")
        raw = read_raw(self.config, "work")
        for resp in answers:
            self.assertIn(resp.answer, raw)

    def test_start_domain_suggests_planned_registers(self):
        session = InterviewSession(self.config, domains=("personal", "work"))
        first = session.start_domain("personal")
        second = session.start_domain("work")
        self.assertEqual(len(first), 3)
        self.assertNotEqual(first, second)

    def test_skip_writes_nothing(self):
        session = InterviewSession(self.config, domains=("personal", "work"))
        session.start_domain("personal")
        session.skip_domain("personal")
        self.assertIsNone(read_raw(self.config, "personal"))
        report = session.completion_report()
        self.assertIn("personal", report["domains_skipped"])
        self.assertNotIn("personal", report["domains_captured"])

    def test_reassignment_captures_under_other_domain(self):
        session = InterviewSession(self.config, domains=("personal", "work"))
        registers = session.start_domain("work")
        result = session.submit_answers(
            "work",
            responses_for(registers),
            capture_domain="personal",
            capture_mode="VERBATIM",
        )
        self.assertTrue(result.path.endswith("personal/raw.md"))
        self.assertIsNone(read_raw(self.config, "work"))
        raw = read_raw(self.config, "personal")
        self.assertIn(f"{ENTRY_MARKER} — work", raw)

    def test_reassignment_to_unknown_domain_rejected(self):
        session = InterviewSession(self.config, domains=("work",))
        session.start_domain("work")
        with self.assertRaises(ConfigError):
            session.submit_answers(
                "work",
                responses_for(["direct"]),
                capture_domain="nope",
                capture_mode="VERBATIM",
            )

    def test_interpretation_marker_propagates(self):
        # Pure CAPTURE is enforced by the library: a synthesizing answer
        # is refused rather than quietly captured.
        session = InterviewSession(self.config, domains=("work",))
        session.start_domain("work")
        bad = [Response("direct", "Q?", "In summary, everything is fine.")]
        with self.assertRaises(InterpretationError):
            session.submit_answers("work", bad, capture_mode="VERBATIM")


class TestCompletionReport(SessionTestCase):
    def test_report_lists_paths_and_skips(self):
        session = InterviewSession(
            self.config, domains=("personal", "work", "projects")
        )
        session.start_domain("personal")
        session.submit_answers("personal", responses_for(["direct", "sparse"]), capture_mode="VERBATIM")
        session.skip_domain("work")
        report = session.completion_report()
        self.assertEqual(report["domains_captured"], ["personal"])
        self.assertEqual(
            report["paths"], {"personal": "personal/raw.md"}
        )
        self.assertEqual(report["domains_skipped"], ["work"])
        self.assertEqual(report["domains_untouched"], ["projects"])

    def test_rendered_report_is_readable(self):
        session = InterviewSession(self.config, domains=("personal",))
        session.start_domain("personal")
        session.submit_answers("personal", responses_for(["direct"]), capture_mode="VERBATIM")
        text = session.render_report()
        self.assertIn("personal/raw.md", text)
        self.assertIn("distill", text)  # next-action offer present


class TestCaptureModeRequired(SessionTestCase):
    """PARAM-MEMINQU-004: capture_mode mandatory at record time."""

    def test_submit_without_mode_raises(self):
        session = InterviewSession(self.config, domains=("work",))
        session.start_domain("work")
        with self.assertRaises(ValueError):
            session.submit_answers("work", responses_for(["direct"]))

    def test_mode_stored_in_raw(self):
        session = InterviewSession(self.config, domains=("work",))
        session.start_domain("work")
        session.submit_answers(
            "work", responses_for(["direct"]), capture_mode="PARAPHRASE"
        )
        raw = read_raw(self.config, "work")
        self.assertIn("capture_mode: PARAPHRASE", raw)

    def test_invalid_mode_raises(self):
        session = InterviewSession(self.config, domains=("work",))
        session.start_domain("work")
        with self.assertRaises(ValueError):
            session.submit_answers(
                "work", responses_for(["direct"]), capture_mode="GIST"
            )


class TestOffCycleCapture(SessionTestCase):
    """PARAM-MEMINQU-013: submit_answers asserts cycle membership."""

    def test_submit_outside_cycle_rejected(self):
        # "personal" is config-known but not in this cycle.
        session = InterviewSession(self.config, domains=("work",))
        with self.assertRaises(SessionError):
            session.submit_answers(
                "personal", responses_for(["direct"]), capture_mode="VERBATIM"
            )
        # Nothing was written: no perjured certification.
        self.assertIsNone(read_raw(self.config, "personal"))
        self.assertNotIn("personal", session.completion_report()["domains_captured"])

    def test_unknown_domain_still_config_error(self):
        # allow_off_cycle bypasses the cycle check, not config knowledge.
        session = InterviewSession(self.config, domains=("work",))
        with self.assertRaises(ConfigError):
            session.submit_answers(
                "fhk",
                responses_for(["direct"]),
                capture_mode="VERBATIM",
                allow_off_cycle=True,
            )

    def test_off_cycle_capture_with_explicit_override(self):
        # The operator genuinely needs off-cycle capture: explicit flag,
        # bytes land under the announced domain's raw.md.
        session = InterviewSession(self.config, domains=("work",))
        result = session.submit_answers(
            "personal",
            responses_for(["direct"]),
            capture_mode="VERBATIM",
            allow_off_cycle=True,
        )
        self.assertTrue(result.path.endswith("personal/raw.md"))
        raw = read_raw(self.config, "personal")
        self.assertIn(f"{ENTRY_MARKER} — personal", raw)
        # The report certifies the off-cycle capture under the announced
        # domain — the exact perjury this parameter closes. Untouched is
        # computed from the cycle, so "personal" is neither untouched
        # nor skipped.
        report = session.completion_report()
        self.assertIn("personal", report["domains_captured"])
        self.assertEqual(report["paths"]["personal"], "personal/raw.md")
        self.assertNotIn("personal", report["domains_untouched"])
        self.assertNotIn("personal", report["domains_skipped"])

    def test_off_cycle_override_preserves_reassignment(self):
        # allow_off_cycle governs the announced domain only; the explicit
        # capture_domain reassignment still routes the bytes (config-known
        # bar, unchanged) — the two validations stay distinct.
        session = InterviewSession(self.config, domains=("work",))
        result = session.submit_answers(
            "personal",
            responses_for(["direct"]),
            capture_domain="projects",
            capture_mode="VERBATIM",
            allow_off_cycle=True,
        )
        self.assertTrue(result.path.endswith("projects/raw.md"))
        self.assertIsNone(read_raw(self.config, "personal"))
        raw = read_raw(self.config, "projects")
        self.assertIn(f"{ENTRY_MARKER} — personal", raw)

    def test_reassignment_does_not_bypass_cycle_bar(self):
        # capture_domain does not smuggle an off-cycle announced domain
        # past the check — the flag is the only way through.
        session = InterviewSession(self.config, domains=("work",))
        with self.assertRaises(SessionError):
            session.submit_answers(
                "personal",
                responses_for(["direct"]),
                capture_domain="projects",
                capture_mode="VERBATIM",
            )

    def test_cycle_bar_matches_sibling_methods(self):
        # Same SessionError bar as start_domain and skip_domain.
        session = InterviewSession(self.config, domains=("work",))
        with self.assertRaises(SessionError):
            session.start_domain("personal")
        with self.assertRaises(SessionError):
            session.skip_domain("personal")
        with self.assertRaises(SessionError):
            session.submit_answers(
                "personal", responses_for(["direct"]), capture_mode="VERBATIM"
            )


if __name__ == "__main__":
    unittest.main()
