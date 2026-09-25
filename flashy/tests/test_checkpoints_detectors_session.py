"""Tests: checkpoints/tokens, detectors, mission session."""

import unittest

from flashy.checkpoints import (
    Checkpoint, CheckpointError, make_resume_token, parse_resume_token,
)
from flashy.detectors import (
    ARTIFICIAL_STOP_PHRASES, DRIFT_QUESTIONS, HIGH, MEDIUM, LOW,
    DetectorError, detect_artificial_stop, asks_permission_to_continue,
    should_pause, is_implementation_changing,
)
from flashy.session import MissionSession
from flashy.state_machine import TransitionError, DONE


class ResumeTokenTests(unittest.TestCase):
    def test_make_and_parse_round_trip(self):
        token = make_resume_token("debate-sim", 3)
        self.assertEqual(token, "finish:debate-sim-m3")
        slug, index = parse_resume_token(token)
        self.assertEqual((slug, index), ("debate-sim", 3))

    def test_malformed_token_rejected(self):
        for bad in ["debate-sim-m3", "flashy:debate-sim-m3", "finish:debate-sim",
                    "finish:debate-sim-mx", ""]:
            with self.subTest(token=bad):
                with self.assertRaises(CheckpointError):
                    parse_resume_token(bad)

    def test_bad_slug_rejected(self):
        with self.assertRaises(CheckpointError):
            make_resume_token("", 2)


class CheckpointTests(unittest.TestCase):
    def _checkpoint(self):
        return Checkpoint(
            objective="Deliver a functional debate simulator",
            done=["Architecture", "UI"],
            current="Logic",
            remaining=["Persistence", "Testing", "Delivery"],
            next_action="Implement turn-taking",
            resume_token="finish:debate-sim-m3",
        )

    def test_render_contains_all_fields(self):
        text = self._checkpoint().render()
        for marker in ("FLASHY CHECKPOINT", "OBJECTIVE", "DONE", "CURRENT",
                       "REMAINING", "NEXT", "RESUME", "finish:debate-sim-m3",
                       "Continuing..."):
            self.assertIn(marker, text)

    def test_parse_round_trip(self):
        parsed = Checkpoint.parse(self._checkpoint().render())
        self.assertEqual(parsed.objective, "Deliver a functional debate simulator")
        self.assertEqual(parsed.done, ["Architecture", "UI"])
        self.assertEqual(parsed.remaining, ["Persistence", "Testing", "Delivery"])
        self.assertEqual(parsed.resume_token, "finish:debate-sim-m3")

    def test_needs_objective_and_token(self):
        with self.assertRaises(CheckpointError):
            Checkpoint(objective="  ", resume_token="finish:x-m1")
        with self.assertRaises(CheckpointError):
            Checkpoint(objective="x", resume_token="bogus")

    def test_parse_rejects_non_checkpoint(self):
        with self.assertRaises(CheckpointError):
            Checkpoint.parse("just some notes")


class DetectorTests(unittest.TestCase):
    def test_artificial_stop_phrases_detected(self):
        text = ("Here's a starting point for the script. "
                "You can expand this to handle more file types.")
        hits = detect_artificial_stop(text)
        self.assertIn("here's a starting point", hits)
        self.assertIn("you can expand this", hits)

    def test_clean_text_no_hits(self):
        self.assertEqual(
            detect_artificial_stop("Implemented the parser and all 41 tests pass."), [])

    def test_due_to_space_detected(self):
        hits = detect_artificial_stop("Due to space, here's Part 1 of the implementation.")
        self.assertIn("due to space", hits)
        self.assertIn("here's part 1", hits)

    def test_permission_phrases_detected(self):
        hits = asks_permission_to_continue("Finished the login form. Should I keep going?")
        self.assertIn("should i keep going?", hits)

    def test_phrase_list_matches_original(self):
        # The skill's list, ported verbatim — 9 phrases.
        self.assertEqual(len(ARTIFICIAL_STOP_PHRASES), 9)

    def test_drift_questions_present(self):
        self.assertEqual(len(DRIFT_QUESTIONS), 4)
        self.assertIn("Am I still solving the original problem?", DRIFT_QUESTIONS)

    def test_only_low_pauses(self):
        self.assertFalse(should_pause(HIGH))
        self.assertFalse(should_pause(MEDIUM))
        self.assertTrue(should_pause(LOW))

    def test_bad_confidence_rejected(self):
        with self.assertRaises(DetectorError):
            should_pause("vibes")

    def test_implementation_changing_heuristic(self):
        self.assertTrue(is_implementation_changing("Which database should we use?"))
        self.assertFalse(is_implementation_changing("Should I use a for loop here?"))


class MissionSessionTests(unittest.TestCase):
    def _session(self):
        s = MissionSession("Deliver a functional debate simulator", slug="debate-sim")
        s.plan(["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"])
        s.start_executing()
        return s

    def test_plan_and_advance(self):
        s = self._session()
        self.assertEqual(s.current_milestone.name, "Architecture")
        s.complete_milestone("Architecture")
        self.assertEqual(s.current_milestone.name, "UI")
        self.assertEqual(s.completed(), ["Architecture"])

    def test_dashboard_shape(self):
        s = self._session()
        dash = s.dashboard()
        for marker in ("OBJECTIVE", "NOW", "DONE", "NEXT", "BLOCKERS"):
            self.assertIn(marker, dash)
        self.assertIn("Deliver a functional debate simulator", dash)

    def test_descope_never_silent(self):
        s = self._session()
        s.descope("Persistence")
        self.assertNotIn("Persistence", s.remaining())

    def test_end_of_response_gate(self):
        s = self._session()
        self.assertEqual(s.end_of_response_gate(), "continue")
        for m in ["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"]:
            s.complete_milestone(m)
        self.assertEqual(s.end_of_response_gate(), "verify")

    def test_full_run_to_done(self):
        s = self._session()
        for m in ["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"]:
            s.complete_milestone(m)
        s.begin_verification()
        s.gate.check_all()
        s.finish()
        self.assertEqual(s.machine.state, DONE)

    def test_finish_blocked_by_open_gate(self):
        s = self._session()
        for m in ["Architecture", "UI", "Logic", "Persistence", "Testing", "Delivery"]:
            s.complete_milestone(m)
        s.begin_verification()
        with self.assertRaises(TransitionError):
            s.finish()  # gate boxes unchecked

    def test_checkpoint_from_session(self):
        s = self._session()
        s.complete_milestone("Architecture")
        cp = s.checkpoint(milestone_index=1)
        self.assertEqual(cp.resume_token, "finish:debate-sim-m1")
        self.assertIn("Architecture", cp.render())

    def test_plan_only_from_locked(self):
        s = self._session()
        with self.assertRaises(TransitionError):
            s.plan(["Another"])


if __name__ == "__main__":
    unittest.main()
