"""Tests: triggers, protocol data shapes, steelman heuristics, demotion rule."""

import unittest

from metacog.protocol import (
    LOAD_BEARING, STRUCTURAL, SURVIVES, WEAKENED, BROKEN,
    Assumption, CollisionResult, ConfidenceRevision, Countermodel,
    ProtocolError, apply_demotions,
)
from metacog.steelman import check_countermodel
from metacog.triggers import (
    TriggerEvaluation, TriggerError, STAKES, CONTRADICTION,
    PREMATURE_CONVERGENCE, EXPLICIT, CONFIDENCE_WITHOUT_EVIDENCE, TRIGGERS,
)


class TriggerTests(unittest.TestCase):
    def test_stand_down_when_nothing_tripped(self):
        ev = TriggerEvaluation(tripped=[])
        self.assertFalse(ev.fires)
        self.assertIn("Standing down", ev.stand_down_report())

    def test_fires_on_any_single_trigger(self):
        for t in TRIGGERS:
            with self.subTest(trigger=t):
                self.assertTrue(TriggerEvaluation(tripped=[t]).fires)

    def test_unknown_trigger_rejected(self):
        with self.assertRaises(TriggerError):
            TriggerEvaluation(tripped=["cosmic-vibes"])

    def test_stand_down_report_refuses_when_fired(self):
        ev = TriggerEvaluation(tripped=[STAKES])
        with self.assertRaises(TriggerError):
            ev.stand_down_report()

    def test_triggers_deduplicated(self):
        ev = TriggerEvaluation(tripped=[STAKES, STAKES, CONTRADICTION])
        self.assertEqual(ev.tripped, [STAKES, CONTRADICTION])


class AssumptionTests(unittest.TestCase):
    def test_load_bearing_flag(self):
        a = Assumption(text="Churn will drop below 4%", kind=LOAD_BEARING)
        self.assertTrue(a.load_bearing)

    def test_structural_flag(self):
        a = Assumption(text="The dashboard is blue", kind=STRUCTURAL)
        self.assertFalse(a.load_bearing)

    def test_bad_kind_rejected(self):
        with self.assertRaises(ProtocolError):
            Assumption(text="x", kind="vibes")


class CollisionTests(unittest.TestCase):
    def test_valid_collision(self):
        c = CollisionResult(
            assumption="Churn will drop below 4%",
            attack="Two quarters of data show churn rising when support headcount is flat.",
            result=WEAKENED,
        )
        self.assertEqual(c.result, WEAKENED)

    def test_bad_result_rejected(self):
        with self.assertRaises(ProtocolError):
            CollisionResult(assumption="a", attack="x", result="vibes")

    def test_empty_attack_rejected(self):
        with self.assertRaises(ProtocolError):
            CollisionResult(assumption="a", attack="   ", result=SURVIVES)


class CountermodelTests(unittest.TestCase):
    def test_weak_countermodel_rejected(self):
        with self.assertRaises(ProtocolError):
            Countermodel(text="some might disagree", strength="weak",
                         flags=["too-short"])


class ConfidenceRevisionTests(unittest.TestCase):
    def test_delta_math(self):
        rev = ConfidenceRevision(before=80, after=45)
        self.assertEqual(rev.delta, -35)

    def test_confidence_bounds(self):
        with self.assertRaises(ProtocolError):
            ConfidenceRevision(before=120, after=50)
        with self.assertRaises(ProtocolError):
            ConfidenceRevision(before=80, after=-5)

    def test_broken_assumption_demotes(self):
        collisions = [CollisionResult(
            assumption="Churn will drop below 4%",
            attack="Churn rose two quarters running.",
            result=BROKEN,
        )]
        demotions = apply_demotions("Migrate billing now", collisions)
        self.assertEqual(len(demotions), 1)
        self.assertIn("demoted to hypothesis", demotions[0])

    def test_no_broken_no_demotion(self):
        collisions = [CollisionResult(
            assumption="a", attack="x", result=SURVIVES,
        )]
        self.assertEqual(apply_demotions("conclusion", collisions), [])


class SteelmanTests(unittest.TestCase):
    STRONG_COUNTERMODEL = (
        "The strongest opposing case has three premises. Premise one: the migration "
        "cost is not the headline number — the data shows that the last three "
        "provider migrations in this industry overran by 2.4x on average, because "
        "contract penalties and dual-running fees were excluded from the business "
        "case. Premise two: the churn argument reverses under measurement. The "
        "evidence from the Q1 cohort shows churn fell only after support response "
        "times improved, not after the billing change, so the mechanism attributed "
        "to billing is actually support staffing. Premise three: the new provider's "
        "uptime record is worse, not better — three documented outages in the last "
        "twelve months versus one on the current contract. Therefore the conclusion "
        "rests on underestimated cost, misattributed churn improvement, and a "
        "weaker reliability premise, and migration now is the wrong call."
    )

    def test_strong_countermodel_passes(self):
        report = check_countermodel(
            self.STRONG_COUNTERMODEL, "Migrate billing now")
        self.assertTrue(report.ok)
        self.assertEqual(report.strength, "strong")
        self.assertEqual(report.flags, [])

    def test_too_short_flagged(self):
        report = check_countermodel("This is bad.", "Migrate billing now")
        self.assertFalse(report.ok)
        self.assertTrue(any("too-short" in f for f in report.flags))

    def test_hedged_no_specifics_flagged(self):
        text = ("Some might disagree with the migration plan. One could argue that "
                "perhaps things might not work out as hoped, and possibly there "
                "could be issues that someone might raise about the timing.")
        report = check_countermodel(text, "Migrate billing now")
        self.assertFalse(report.ok)
        self.assertTrue(any("hedged-no-specifics" in f for f in report.flags))

    def test_no_named_premises_flagged(self):
        text = ("I feel uneasy about this decision. It seems risky and there are "
                "probably downsides we have not thought of yet, which makes me "
                "wonder whether we should really go ahead with the migration at "
                "this particular point in time given all the uncertainty.")
        report = check_countermodel(text, "Migrate billing now")
        self.assertFalse(report.ok)
        self.assertTrue(any("no-named-premises" in f for f in report.flags))

    def test_unopposed_admission_is_finding_not_failure(self):
        text = ("I cannot build a strong countermodel here: the field is thin, "
                "the evidence all points one way, and no credible opposing case "
                "exists in the records I was given.")
        report = check_countermodel(text, "Migrate billing now")
        self.assertTrue(report.ok)
        self.assertEqual(report.strength, "unopposed")


if __name__ == "__main__":
    unittest.main()
