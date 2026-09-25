"""Tests: collision-record schema/validation/render/parse, engine normalize."""

import json
import unittest

from metacog.engine import (
    ReasoningInput, build_user_message, normalize, parse_model_json,
    run, to_collision_record,
)
from metacog.backends import StubBackend
from metacog.protocol import (
    Assumption, CollisionResult, Countermodel, SURVIVES, WEAKENED,
)
from metacog.record import CollisionRecord, RecordError
from metacog.triggers import TriggerEvaluation, STAKES, CONTRADICTION

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


def _valid_model():
    return {
        "triggers": [STAKES, CONTRADICTION],
        "countermodel": STRONG_COUNTERMODEL,
        "assumptions": [
            {"text": "Migration cost stays under $40k", "kind": "load-bearing"},
            {"text": "Churn drops below 4% after migration", "kind": "load-bearing"},
            {"text": "The new UI is nicer", "kind": "structural"},
        ],
        "collisions": [
            {"assumption": "Migration cost stays under $40k",
             "attack": "Three comparable migrations overran by 2.4x on dual-running fees.",
             "result": "weakened"},
            {"assumption": "Churn drops below 4% after migration",
             "attack": "Q1 cohort churn fell on support improvements, not billing changes.",
             "result": "survives"},
        ],
        "confidence_before": 80,
        "confidence_after": 55,
        "demotions": [],
        "surprise": "The churn mechanism and the billing mechanism are independent — support staffing is the hidden variable.",
    }


def _valid_record():
    return CollisionRecord(
        triggers=TriggerEvaluation(tripped=[STAKES, CONTRADICTION]),
        countermodel=Countermodel(text=STRONG_COUNTERMODEL, strength="strong"),
        assumptions=[
            Assumption(text="Migration cost stays under $40k", kind="load-bearing"),
            Assumption(text="Churn drops below 4% after migration", kind="load-bearing"),
            Assumption(text="The new UI is nicer", kind="structural"),
        ],
        collisions=[
            CollisionResult(
                assumption="Migration cost stays under $40k",
                attack="Three comparable migrations overran by 2.4x.",
                result=WEAKENED,
            ),
            CollisionResult(
                assumption="Churn drops below 4% after migration",
                attack="Q1 cohort fell on support improvements.",
                result=SURVIVES,
            ),
        ],
        confidence_before=80,
        confidence_after=55,
        surprise="Support staffing is the hidden variable.",
    )


class RecordValidationTests(unittest.TestCase):
    def test_valid_record_passes(self):
        _valid_record().validate()

    def test_stand_down_record_rejected(self):
        rec = _valid_record()
        rec.triggers = TriggerEvaluation(tripped=[])
        with self.assertRaises(RecordError):
            rec.validate()

    def test_structural_assumption_collision_rejected(self):
        rec = _valid_record()
        rec.collisions.append(CollisionResult(
            assumption="The new UI is nicer",
            attack="Beauty is subjective.",
            result=WEAKENED,
        ))
        with self.assertRaises(RecordError):
            rec.validate()

    def test_revision_without_collision_rejected(self):
        rec = _valid_record()
        rec.collisions = []
        with self.assertRaises(RecordError):
            rec.validate()

    def test_placeholder_rejected(self):
        rec = _valid_record()
        rec.surprise = "TODO fill in later"
        with self.assertRaises(RecordError):
            rec.validate()

    def test_confidence_bounds(self):
        rec = _valid_record()
        rec.confidence_after = 101
        with self.assertRaises(RecordError):
            rec.validate()


class RecordRenderParseTests(unittest.TestCase):
    def test_render_has_frontmatter_and_sections(self):
        text = _valid_record().render()
        self.assertIn("artifact: collision-record", text)
        self.assertIn("protocol: metacog/1.0", text)
        self.assertIn("## Countermodel", text)
        self.assertIn("## Load-Bearing Assumptions", text)
        self.assertIn("## Confidence", text)
        self.assertIn("## Surprise", text)
        self.assertIn("delta -25", text)

    def test_parse_round_trip(self):
        rec = _valid_record()
        parsed = CollisionRecord.parse(rec.render())
        self.assertEqual(parsed.confidence_before, 80)
        self.assertEqual(parsed.confidence_after, 55)
        self.assertIn(STAKES, parsed.triggers.tripped)
        self.assertIn(CONTRADICTION, parsed.triggers.tripped)

    def test_parse_rejects_non_record(self):
        with self.assertRaises(RecordError):
            CollisionRecord.parse("just some text")


class EngineTests(unittest.TestCase):
    def _input(self):
        return ReasoningInput(
            conclusion="Migrate billing to the new provider now",
            reasoning="Costs are lower and churn will drop.",
            evidence=["Quote: $38k migration", "Q1 cohort churn 3.8%"],
            stated_confidence=80,
            triggers=[STAKES],
        )

    def test_full_run_via_stub(self):
        result = run(self._input(), StubBackend(_valid_model()))
        self.assertTrue(result.ok)
        rec = result.record
        self.assertFalse(rec["stand_down"])
        self.assertEqual(rec["confidence_delta"], -25)
        self.assertEqual(rec["countermodel"]["strength"], "strong")
        self.assertEqual(len(rec["collisions"]), 2)

    def test_to_collision_record_renders(self):
        result = run(self._input(), StubBackend(_valid_model()))
        text = to_collision_record(result.record).render()
        self.assertIn("collision-record", text)

    def test_no_triggers_invalid(self):
        model = _valid_model()
        model["triggers"] = []
        result = run(self._input(), StubBackend(model))
        self.assertFalse(result.ok)
        self.assertIn("noise", result.error)

    def test_weak_countermodel_invalid(self):
        model = _valid_model()
        model["countermodel"] = "Some might disagree with the migration."
        result = run(self._input(), StubBackend(model))
        self.assertFalse(result.ok)
        self.assertIn("steelman", result.error)

    def test_structural_collision_invalid(self):
        model = _valid_model()
        model["collisions"] = [{
            "assumption": "The new UI is nicer",
            "attack": "Beauty is subjective.",
            "result": "weakened",
        }]
        result = run(self._input(), StubBackend(model))
        self.assertFalse(result.ok)
        self.assertIn("non-load-bearing", result.error)

    def test_stand_down(self):
        model = {"stand_down": True}
        result = run(self._input(), StubBackend(model))
        self.assertTrue(result.ok)
        self.assertTrue(result.record["stand_down"])

    def test_parse_model_json_tolerates_fences(self):
        raw = "```json\n" + json.dumps(_valid_model()) + "\n```"
        self.assertEqual(parse_model_json(raw)["confidence_after"], 55)

    def test_build_user_message_contents(self):
        msg = build_user_message(self._input())
        self.assertIn("Migrate billing", msg)
        self.assertIn("STATED CONFIDENCE: 80/100", msg)

    def test_broken_collision_demotes(self):
        model = _valid_model()
        model["collisions"][0]["result"] = "broken"
        result = run(self._input(), StubBackend(model))
        self.assertTrue(result.ok)
        self.assertEqual(len(result.record["demotions"]), 1)
        self.assertIn("demoted to hypothesis", result.record["demotions"][0])


if __name__ == "__main__":
    unittest.main()
