"""Ledger tests for metacog: runs record confidence deltas, never the reasoning."""

import os
import tempfile
import unittest

from metacog.backends import StubBackend
from metacog.engine import ReasoningInput, run
from metacog.ledger import Ledger
from metacog.triggers import STAKES, CONTRADICTION

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
        "surprise": "Support staffing is the hidden variable.",
    }


class MetacogLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old_dir = os.environ.get("FRONTFACE_LEDGER_DIR")
        self._old_off = os.environ.get("FRONTFACE_NO_LEDGER")
        os.environ["FRONTFACE_LEDGER_DIR"] = self.tmp.name
        os.environ.pop("FRONTFACE_NO_LEDGER", None)

    def tearDown(self):
        if self._old_dir is None:
            os.environ.pop("FRONTFACE_LEDGER_DIR", None)
        else:
            os.environ["FRONTFACE_LEDGER_DIR"] = self._old_dir
        if self._old_off is None:
            os.environ.pop("FRONTFACE_NO_LEDGER", None)
        else:
            os.environ["FRONTFACE_NO_LEDGER"] = self._old_off
        self.tmp.cleanup()

    def test_run_records_collision_with_deltas(self):
        secret = "ledger-test-secret-metacog-456"
        inp = ReasoningInput(
            conclusion="Migrate billing now",
            reasoning=f"Costs are lower. {secret}",
            evidence=["Quote: $38k"],
            stated_confidence=80,
            triggers=[STAKES],
        )
        result = run(inp, StubBackend(_valid_model()))
        self.assertTrue(result.ok)
        recs = Ledger("metacog").read()
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["event"], "collision")
        self.assertTrue(rec["summary"]["ok"])
        self.assertEqual(rec["summary"]["confidence_before"], 80)
        self.assertEqual(rec["summary"]["confidence_after"], 55)
        self.assertEqual(rec["summary"]["confidence_delta"], -25)
        self.assertEqual(rec["summary"]["assumptions"], 3)
        self.assertEqual(rec["summary"]["load_bearing"], 2)
        with open(Ledger("metacog").path, encoding="utf-8") as f:
            self.assertNotIn(secret, f.read())

    def test_failed_run_records_error(self):
        inp = ReasoningInput(
            conclusion="x", reasoning="y", evidence=[],
            stated_confidence=50, triggers=[STAKES],
        )
        result = run(inp, StubBackend({"triggers": []}))
        self.assertFalse(result.ok)
        recs = Ledger("metacog").read()
        self.assertEqual(len(recs), 1)
        self.assertFalse(recs[0]["summary"]["ok"])
        self.assertIn("error", recs[0]["summary"])


if __name__ == "__main__":
    unittest.main()
