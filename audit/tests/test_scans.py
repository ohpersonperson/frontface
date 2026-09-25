"""Tests for the mechanical linter checks (scans.py) and the discipline table."""

import unittest

from postmo.disciplines import D1, D2, D3, D4, D5, DISCIPLINES, discipline_name
from postmo.scans import (
    Correction, CorrectionCandidate, HeldTension, MotiveFlag, PersonState,
    ScanError, detect_softening, detect_supplied_motive,
    find_correction_candidates, find_subordinators, find_verdict_words,
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

    def test_scan_text_clean(self):
        report = scan_text(
            "He arrived at three. She left at four. Both of those happened."
        )
        self.assertTrue(report.clean())


if __name__ == "__main__":
    unittest.main()
