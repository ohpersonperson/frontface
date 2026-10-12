"""Tests for the mechanical linter checks (scans.py) and the discipline table."""

import os
import subprocess
import sys
import tempfile
import unittest

from postmo.disciplines import D1, D2, D3, D4, D5, DISCIPLINES, discipline_name

AUDIT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from postmo.scans import (
    Correction, CorrectionCandidate, CorrectionCoverage, HeldTension,
    MotiveFlag, PersonState, ScanError, correction_coverage,
    detect_softening, detect_supplied_motive, find_correction_candidates,
    find_subordinators, find_verdict_words, render_correction_coverage,
    scan_text,
)


class DisciplineTableTest(unittest.TestCase):
    def test_five_disciplines_numbered_1_to_5(self):
        self.assertEqual(set(DISCIPLINES), {1, 2, 3, 4, 5})

    def test_each_discipline_has_code_operator_split(self):
        for n, d in DISCIPLINES.items():
            for key in ("name", "rule", "mechanical", "operator"):
                self.assertTrue(d[key].strip(), f"D{n} missing {key}")

    def test_discipline_name(self):
        self.assertEqual(discipline_name(D1), "hold-contradictions")
        self.assertEqual(discipline_name(D5), "softening-self-check")
        with self.assertRaises(ValueError):
            discipline_name(6)


class SubordinatorScanTest(unittest.TestCase):
    def test_finds_but_and_however(self):
        self.assertIn("but", find_subordinators("X is true, but Y is also true."))
        self.assertIn("however", find_subordinators("X is true. However, Y."))

    def test_finds_multiword_connectives(self):
        self.assertIn("which means", find_subordinators("X is true, which means Y."))
        self.assertIn("in other words", find_subordinators("X. In other words, Y."))

    def test_parallel_sentences_pass(self):
        self.assertEqual(find_subordinators("X is true. Y is also true."), [])

    def test_held_tension_accepts_parallel(self):
        t = HeldTension(text="I adored her. I'm furious at her.")
        self.assertTrue(t.text)

    def test_held_tension_rejects_subordinator(self):
        with self.assertRaises(ScanError):
            HeldTension(text="I adored her, but I'm furious at her.")
        with self.assertRaises(ScanError):
            HeldTension(text="I adored her. However, I'm furious at her.")

    def test_held_tension_rejects_empty(self):
        with self.assertRaises(ScanError):
            HeldTension(text="   ")


class VerdictWordScanTest(unittest.TestCase):
    def test_flags_permanent_label(self):
        hits = find_verdict_words("He's a liar, that's all there is to it.")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].word, "liar")

    def test_state_description_passes(self):
        # "he was lying on Tuesday" is a time-indexed state, not a verdict.
        self.assertEqual(find_verdict_words("He was lying to her on Tuesday."), [])

    def test_adjective_state_passes(self):
        # Adjectives can legitimately describe a moment — nouns only.
        self.assertEqual(find_verdict_words("The situation was dangerous."), [])

    def test_person_state_requires_all_fields(self):
        with self.assertRaises(ScanError):
            PersonState(when="", person="Dana", state="calm")
        with self.assertRaises(ScanError):
            PersonState(when="Tue", person=" ", state="calm")
        ok = PersonState(when="2026-09-20", person="Dana", state="calm, cooperative")
        self.assertEqual(ok.person, "Dana")


class CorrectionTypingTest(unittest.TestCase):
    def test_accepts_both_kinds(self):
        self.assertEqual(Correction(kind="detail", text="3pm, not 2pm.").kind, "detail")
        self.assertEqual(
            Correction(kind="core-claim", text="She withdrew the claim.").kind,
            "core-claim",
        )

    def test_rejects_bad_kind_and_empty(self):
        with self.assertRaises(ScanError):
            Correction(kind="typo", text="whatever")
        with self.assertRaises(ScanError):
            Correction(kind="detail", text="  ")

    def test_finds_correction_candidates(self):
        found = find_correction_candidates(
            "The meeting was at two. Actually, it was at three. Dana agreed."
        )
        self.assertEqual(len(found), 1)
        self.assertIn("actually", found[0].marker)
        self.assertTrue(isinstance(found[0], CorrectionCandidate))

    def test_no_candidates_in_clean_text(self):
        self.assertEqual(
            find_correction_candidates("The meeting was at two. Dana agreed."), []
        )


class CorrectionCoverageTest(unittest.TestCase):
    TEXT = ("The meeting was at two. Actually, it was at three. "
            "Dana agreed to the plan.")

    def test_statuses_typed_candidate_unmarked(self):
        typed = [Correction(kind="detail", text="Actually, it was at three.")]
        rows = correction_coverage(self.TEXT, typed)
        self.assertEqual([r.status for r in rows],
                         ["unmarked", "typed", "unmarked"])
        self.assertEqual(rows[1].kind, "detail")
        self.assertEqual(rows[1].marker, "actually")

    def test_candidate_carries_marker_when_untyped(self):
        rows = correction_coverage(self.TEXT)
        cand = rows[1]
        self.assertEqual(cand.status, "candidate")
        self.assertEqual(cand.marker, "actually")
        self.assertEqual(cand.kind, "")

    def test_typed_matches_on_stripped_text(self):
        typed = [Correction(kind="core-claim",
                            text="  Actually, it was at three.  ")]
        rows = correction_coverage(self.TEXT, typed)
        self.assertEqual(rows[1].status, "typed")
        self.assertEqual(rows[1].kind, "core-claim")

    def test_typed_matching_is_case_insensitive(self):
        typed = [Correction(kind="detail",
                            text="aCtUaLlY, It WaS aT tHrEe.")]
        rows = correction_coverage(self.TEXT, typed)
        self.assertEqual(rows[1].status, "typed")
        self.assertEqual(rows[1].kind, "detail")

    def test_first_typed_correction_wins_on_duplicates(self):
        typed = [Correction(kind="detail", text="Actually, it was at three."),
                 Correction(kind="core-claim",
                            text="ACTUALLY, IT WAS AT THREE.")]
        rows = correction_coverage(self.TEXT, typed)
        self.assertEqual(rows[1].status, "typed")
        self.assertEqual(rows[1].kind, "detail")

    def test_unmatched_typed_correction_is_surfaced_not_dropped(self):
        typed = [Correction(kind="detail", text="A sentence from nowhere.")]
        rows = correction_coverage(self.TEXT, typed)
        self.assertEqual(len(rows), 4)
        orphan = rows[3]
        self.assertEqual(orphan.status, "unmatched")
        self.assertEqual(orphan.kind, "detail")
        self.assertEqual(orphan.sentence, "A sentence from nowhere.")

    def test_empty_text_has_no_rows(self):
        self.assertEqual(correction_coverage("   "), [])

    def test_coverage_row_rejects_bad_status_and_kind(self):
        with self.assertRaises(ScanError):
            CorrectionCoverage(sentence="x.", status="maybe")
        with self.assertRaises(ScanError):
            CorrectionCoverage(sentence="x.", status="typed", kind="typo")
        with self.assertRaises(ScanError):
            CorrectionCoverage(sentence="  ", status="unmarked")

    def test_render_publishes_every_sentence_with_status(self):
        text = (self.TEXT + " To be clear, the venue changed.")
        typed = [Correction(kind="detail", text="Actually, it was at three."),
                 Correction(kind="core-claim",
                            text="A sentence from nowhere.")]
        rendered = render_correction_coverage(text, typed)
        self.assertIn("## Correction typing coverage (discipline 3)",
                      rendered)
        self.assertIn("- [unmarked] The meeting was at two.", rendered)
        self.assertIn("- [typed: detail] (marker: 'actually') "
                      "Actually, it was at three.", rendered)
        self.assertIn("- [untyped candidate] (marker: 'to be clear,') "
                      "To be clear, the venue changed.", rendered)
        self.assertIn("- [unmarked] Dana agreed to the plan.", rendered)
        self.assertIn("## Typed corrections not found in the text", rendered)
        self.assertIn("- [unmatched: core-claim] A sentence from nowhere.",
                      rendered)

    def test_scan_text_carries_coverage_and_filters_typed_candidates(self):
        typed = [Correction(kind="detail",
                            text="actually, it was at three.")]
        report = scan_text(self.TEXT, typed=typed)
        self.assertEqual([r.status for r in report.correction_coverage],
                         ["unmarked", "typed", "unmarked"])
        self.assertEqual(report.correction_coverage[1].kind, "detail")
        # The typed sentence drops off the needs-typing candidate list.
        self.assertEqual(report.correction_candidates, [])

    def test_typed_accepts_a_generator(self):
        def gen():
            yield Correction(kind="detail", text="Actually, it was at three.")
            yield Correction(kind="core-claim",
                             text="A sentence from nowhere.")
        report = scan_text(self.TEXT, typed=gen())
        self.assertEqual([r.status for r in report.correction_coverage],
                         ["unmarked", "typed", "unmarked", "unmatched"])
        self.assertEqual(report.correction_candidates, [])

    def test_scan_text_without_typed_is_unchanged(self):
        report = scan_text(self.TEXT)
        self.assertEqual(len(report.correction_candidates), 1)
        self.assertEqual(report.correction_candidates[0].marker, "actually")
        self.assertEqual([r.status for r in report.correction_coverage],
                         ["unmarked", "candidate", "unmarked"])


class MotiveScanTest(unittest.TestCase):
    def test_flags_supplied_motive(self):
        flags = detect_supplied_motive("He tackled you because he panicked.")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "flag")
        self.assertTrue(isinstance(flags[0], MotiveFlag))

    def test_attributed_motive_is_clean(self):
        # The teller assigned the why — discipline 4 satisfied.
        self.assertEqual(
            detect_supplied_motive("He said he panicked when it happened."), []
        )

    def test_bare_quote_is_not_attribution(self):
        # Scare quotes must not pass as sourcing (PARAM-POSTMO-014):
        # the quote alone no longer suppresses the motive flag.
        flags = detect_supplied_motive(
            "He panicked and \"ran\" when it happened.")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "flag")

    def test_quote_adjacent_speech_verb_is_attribution(self):
        self.assertEqual(
            detect_supplied_motive("\"He panicked and ran,\" she admitted."),
            [])
        self.assertEqual(
            detect_supplied_motive("She admitted, \"He panicked and ran.\""),
            [])
        self.assertEqual(
            detect_supplied_motive(
                "\"He panicked and ran,\" the witness admitted."), []
        )
        self.assertEqual(
            detect_supplied_motive("The report quotes him: "
                                   "\"He panicked and ran.\""),
            [])

    def test_verb_in_unrelated_clause_is_not_attribution(self):
        # "admitted" belongs to another clause — the scare quote stays
        # unattributed. ("said" would be a marker regardless.)
        flags = detect_supplied_motive(
            "He panicked and \"ran\" when the witness admitted "
            "he was afraid.")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "flag")

    def test_quote_with_marker_still_clean(self):
        self.assertEqual(
            detect_supplied_motive("\"He panicked and ran,\" she said."), []
        )

    def test_marked_guess_is_allowed_but_kept(self):
        flags = detect_supplied_motive("If I had to guess, he panicked.")
        self.assertEqual(len(flags), 1)
        self.assertEqual(flags[0].severity, "guess")

    def test_flags_driven_by_and_out_of(self):
        self.assertTrue(detect_supplied_motive("It was driven by fear."))
        self.assertTrue(detect_supplied_motive("She did it out of spite."))

    def test_observed_sequence_passes(self):
        self.assertEqual(
            detect_supplied_motive("He tackled you. You fell. He walked away."), []
        )

    def test_motive_flag_rejects_bad_severity(self):
        with self.assertRaises(ScanError):
            MotiveFlag(sentence="x", pattern="y", severity="verdict")


class SofteningScanTest(unittest.TestCase):
    def test_downgrade_betrayal_to_mistake(self):
        flags = detect_softening(
            "It was a betrayal of my trust.", "It was a mistake."
        )
        kinds = [f.kind for f in flags]
        self.assertIn("downgrade", kinds)
        down = next(f for f in flags if f.kind == "downgrade")
        self.assertEqual(down.original_term, "betrayal")
        self.assertEqual(down.replacement, "mistake")

    def test_dropped_strong_term(self):
        flags = detect_softening("He lied to me.", "It was complicated.")
        self.assertTrue(any(
            f.kind == "dropped" and f.original_term == "lied" for f in flags
        ))

    def test_strong_term_kept_is_clean(self):
        self.assertEqual(
            detect_softening("He lied to me.", "He lied, and it hurt."), []
        )

    def test_tidy_restatement_phrase(self):
        flags = detect_softening(
            "I adored her. I'm furious at her.",
            "So what you're saying is you have mixed feelings.",
        )
        self.assertTrue(any(f.kind == "tidy-restatement" for f in flags))

    def test_ambivalence_resolved(self):
        flags = detect_softening(
            "I adored her. I'm furious at her.",
            "The real feeling underneath is anger.",
        )
        self.assertTrue(any(f.kind == "ambivalence-resolved" for f in flags))


class BatchScanTest(unittest.TestCase):
    def test_scan_text_fires_everything(self):
        report = scan_text(
            "He's a liar. Actually, he tackled you because he panicked, but I adored him.",
            restatement="So what you're saying is he made a mistake.",
        )
        self.assertTrue(report.subordinators)
        self.assertTrue(report.verdict_words)
        self.assertTrue(report.correction_candidates)
        self.assertTrue(report.motive_flags)
        self.assertTrue(report.softening_flags)
        self.assertFalse(report.clean())

    def test_scan_text_clean_with_restatement(self):
        report = scan_text(
            "He arrived at three. She left at four. Both of those happened.",
            restatement="He arrived at three. She left at four.",
        )
        self.assertTrue(report.softening_checked)
        self.assertEqual(report.softening_state(), "clean")
        self.assertTrue(report.clean())

    def test_scan_text_not_clean_when_d5_unchecked(self):
        # PARAM-POSTMO-015: no restatement → D5 never ran → the report
        # must not claim clean, and the state says so explicitly.
        report = scan_text(
            "He arrived at three. She left at four. Both of those happened."
        )
        self.assertFalse(report.softening_checked)
        self.assertEqual(report.softening_state(), "not-checked")
        self.assertFalse(report.clean())

    def test_softening_state_flagged(self):
        report = scan_text(
            "It was a betrayal of my trust.",
            restatement="It was a mistake.",
        )
        self.assertTrue(report.softening_checked)
        self.assertEqual(report.softening_state(), "flagged")
        self.assertFalse(report.clean())


class LintExampleTest(unittest.TestCase):
    def _run_lint(self, draft_text, extra_args=()):
        with tempfile.TemporaryDirectory() as tmp:
            draft = os.path.join(tmp, "draft.txt")
            with open(draft, "w", encoding="utf-8") as f:
                f.write(draft_text)
            env = dict(os.environ,
                       PYTHONPATH=os.path.join(AUDIT_DIR, "src"))
            return subprocess.run(
                [sys.executable, "examples/lint_audit.py",
                 "--text", draft, *extra_args],
                capture_output=True, text=True, cwd=AUDIT_DIR, env=env,
            )

    def test_cli_prints_unchecked_d5_notice(self):
        proc = self._run_lint("He arrived at three. She left at four.\n")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("softening not checked", proc.stdout)
        self.assertIn("Not checked' is not 'no softening found'", proc.stdout)

    def test_cli_no_notice_when_restatement_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            rest = os.path.join(tmp, "rest.txt")
            with open(rest, "w", encoding="utf-8") as f:
                f.write("He arrived at three.\n")
            proc = self._run_lint("He arrived at three. She left at four.\n",
                                  extra_args=("--restatement", rest))
        self.assertEqual(proc.returncode, 0)
        self.assertNotIn("softening not checked", proc.stdout)


if __name__ == "__main__":
    unittest.main()
