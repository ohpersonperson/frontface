"""Tests for the shared hypothesis-testing core."""

import unittest
import warnings

from fairit.hypotheses import (
    H_BOTH,
    H_GENUINE,
    H_OBFUSCATION,
    INSUFFICIENT_EVIDENCE,
    CategoryGateDeclinedWarning,
    CategoryPresumptionError,
    DiscriminatingEvidence,
    HypothesisError,
    HypothesisRecord,
    Mechanism,
)


def ev(text, favors="neutral"):
    return DiscriminatingEvidence(text, favors)


class TestVerdictRules(unittest.TestCase):
    def test_obfuscation_needs_discriminating_evidence(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(candidate="X", verdict=H_OBFUSCATION, evidence=[])
        with self.assertRaises(HypothesisError):
            HypothesisRecord(
                candidate="X",
                verdict=H_OBFUSCATION,
                evidence=[ev("some neutral fact")],
            )

    def test_obfuscation_with_evidence_passes(self):
        r = HypothesisRecord(
            candidate="the phrase 'mistakes were made' dodges the firing decision",
            verdict=H_OBFUSCATION,
            evidence=[ev("the passive phrasing appears only in the public statement, never in internal emails", H_OBFUSCATION)],
            mechanisms=[Mechanism("passive-voice dodge", "supported")],
        )
        self.assertEqual(r.verdict, H_OBFUSCATION)

    def test_genuine_needs_its_own_evidence(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(
                candidate="X",
                verdict=H_GENUINE,
                evidence=[ev("looks bad", H_OBFUSCATION)],
            )

    def test_both_needs_both_sides(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(
                candidate="X",
                verdict=H_BOTH,
                evidence=[ev("only under pressure", H_OBFUSCATION)],
            )
        r = HypothesisRecord(
            candidate="X",
            verdict=H_BOTH,
            evidence=[
                ev("appears only under pressure", H_OBFUSCATION),
                ev("followed by changed behavior twice", H_GENUINE),
            ],
        )
        self.assertEqual(r.verdict, H_BOTH)

    def test_insufficient_evidence_needs_open_questions(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(candidate="X", verdict=INSUFFICIENT_EVIDENCE)
        r = HypothesisRecord(
            candidate="X",
            verdict=INSUFFICIENT_EVIDENCE,
            remaining_questions=["Did the behavior change after the statement?"],
        )
        self.assertEqual(r.verdict, INSUFFICIENT_EVIDENCE)

    def test_bad_verdict_rejected(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(candidate="X", verdict="H-suspicious")

    def test_empty_candidate_rejected(self):
        with self.assertRaises(HypothesisError):
            HypothesisRecord(candidate="   ", verdict=INSUFFICIENT_EVIDENCE,
                             remaining_questions=["q"])


class TestCategoryPresumption(unittest.TestCase):
    """The load-bearing integrity rule: category is never evidence."""

    def test_bare_category_label_rejected(self):
        with self.assertRaises(CategoryPresumptionError):
            DiscriminatingEvidence("therapy-speak", H_OBFUSCATION)

    def test_label_with_filler_rejected(self):
        for text in ("uses therapy-speak", "sounds like corporate speak",
                     "very corporate-speak", "just bureaucratic"):
            with self.assertRaises(CategoryPresumptionError, msg=text):
                DiscriminatingEvidence(text, H_OBFUSCATION)

    def test_observation_attached_passes(self):
        e = ev("uses therapy-speak only when asked about the missed deadline, never unprompted",
               H_OBFUSCATION)
        self.assertEqual(e.favors, H_OBFUSCATION)

    def test_v1_bias_regression_therapy_speak_cannot_convict(self):
        # The exact v1 failure mode: "mandatory flag... do not let it pass
        # as neutral." v2 must not be able to convict on the label alone.
        with self.assertRaises(CategoryPresumptionError):
            HypothesisRecord(
                candidate="the phrase 'doing the work' is armor",
                verdict=H_OBFUSCATION,
                evidence=[ev("therapy-speak", H_OBFUSCATION)],
            )

    def test_neutral_evidence_direction_allowed(self):
        e = ev("the statement was made on Tuesday")
        self.assertEqual(e.favors, "neutral")

    def test_bad_direction_rejected(self):
        with self.assertRaises(HypothesisError):
            DiscriminatingEvidence("something", "H-maybe")


class TestGateDeclineSurfaced(unittest.TestCase):
    """PARAM-FAIRIT-002: gate declines are visible, not silent."""

    def test_decline_emits_warning_naming_phrase_and_result(self):
        # "uses therapy-speak constantly" evades the two-word tripwire
        # ("constantly" is not a stopword) — the gate declines, and the
        # decline must be surfaced, not silent.
        phrase = "uses therapy-speak constantly"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            DiscriminatingEvidence(phrase, H_OBFUSCATION)
        self.assertEqual(len(caught), 1)
        self.assertTrue(
            issubclass(caught[0].category, CategoryGateDeclinedWarning)
        )
        message = str(caught[0].message)
        self.assertIn(phrase, message)
        self.assertIn("declined", message)

    def test_legitimate_evidence_also_consulted(self):
        # The gate is consulted for every phrase; a real observation
        # passes with a decline warning as its audit record.
        phrase = "the passive phrasing appears only in the public statement"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            e = DiscriminatingEvidence(phrase, H_OBFUSCATION)
        self.assertEqual(e.favors, H_OBFUSCATION)
        self.assertEqual(len(caught), 1)
        self.assertIn(phrase, str(caught[0].message))

    def test_fire_still_raises(self):
        # The existing CategoryPresumptionError path is unchanged.
        with self.assertRaises(CategoryPresumptionError):
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                DiscriminatingEvidence("therapy-speak", H_OBFUSCATION)


class TestObfuscationGate(unittest.TestCase):
    def test_gate_opens_only_on_supported_obfuscation(self):
        r = HypothesisRecord(
            candidate="X", verdict=H_OBFUSCATION,
            evidence=[ev("appears only under pressure", H_OBFUSCATION)],
            mechanisms=[Mechanism("fogging", "supported")],
        )
        self.assertTrue(r.supports_obfuscation())

    def test_gate_closed_for_contested(self):
        r = HypothesisRecord(
            candidate="X", verdict=H_OBFUSCATION,
            evidence=[ev("appears only under pressure", H_OBFUSCATION)],
            mechanisms=[Mechanism("fogging", "contested")],
        )
        self.assertFalse(r.supports_obfuscation())

    def test_gate_closed_for_genuine(self):
        r = HypothesisRecord(
            candidate="X", verdict=H_GENUINE,
            evidence=[ev("followed by apology and changed rota", H_GENUINE)],
        )
        self.assertFalse(r.supports_obfuscation())


if __name__ == "__main__":
    unittest.main()
