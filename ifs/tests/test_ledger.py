"""Ledger tests for pressit: interrogations record counts, never the field."""

import os
import tempfile
import unittest

from pressit import backends, engine
from pressit.ledger import Ledger
from pressit.protocol import FieldInput

MODEL_JSON = {
    "meta": {"field": "Test field", "status": "INITIAL"},
    "field": {"objective": "o", "scope": "s"},
    "priorState": {"reference": None, "evaluations": []},
    "evidence": {"facts": [], "claims": [], "unknowns": []},
    "probe": {"obfuscatedObject": "x", "apparentFunction": "y",
              "activeTactics": [], "jargonFlags": []},
    "takes": [
        {"id": "A", "title": "TA", "argument": "arg A"},
        {"id": "B", "title": "TB", "argument": "arg B"},
    ],
    "collisions": [
        {"pair": "A/B", "contradiction": "c", "premiseFailure": "p",
         "discriminator": "d"},
    ],
    "keys": [
        {"statement": f"k{i}", "classification": "PLAUSIBLE", "evidence": "e",
         "confidence": "MODERATE", "vulnerability": "v", "falsifier": "f"}
        for i in range(3)
    ],
    "surprise": "s",
    "synthesis": {"establishedGround": "g", "survivingModel": "m",
                  "remainingUncertainties": "u", "primaryNextTarget": "n"},
}


class PressitLedgerTest(unittest.TestCase):
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

    def test_run_records_pressure_counts(self):
        secret = "ledger-test-secret-pressit-789"
        field = FieldInput(field=f"Revenue question {secret}")
        result = engine.run(field, backends.StubBackend(MODEL_JSON))
        self.assertTrue(result.ok)
        recs = Ledger("pressit").read()
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["event"], "pressure")
        self.assertTrue(rec["summary"]["ok"])
        self.assertEqual(rec["summary"]["takes"], 2)
        self.assertEqual(rec["summary"]["collisions"], 1)
        self.assertEqual(rec["summary"]["keys"], 3)
        with open(Ledger("pressit").path, encoding="utf-8") as f:
            self.assertNotIn(secret, f.read())

    def test_opt_out(self):
        os.environ["FRONTFACE_NO_LEDGER"] = "1"
        field = FieldInput(field="Another question")
        engine.run(field, backends.StubBackend(MODEL_JSON))
        self.assertEqual(Ledger("pressit").read(), [])


if __name__ == "__main__":
    unittest.main()
