"""Ledger tests for fairit: jargon tests record verdicts, never the phrase."""

import os
import tempfile
import unittest

from fairit.ledger import Ledger
from fairit.overlay import run_jargon_test


class FairitLedgerTest(unittest.TestCase):
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

    def test_jargon_test_recorded(self):
        secret = "ledger-test-secret-fairit-111"
        flag = run_jargon_test(
            f"synergize {secret}", "corporate",
            "appears only when asked who is responsible", "",
        )
        self.assertEqual(flag.record.verdict, "H-obfuscation")
        recs = Ledger("fairit").read()
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["event"], "jargon_test")
        self.assertEqual(rec["summary"]["verdict"], "H-obfuscation")
        self.assertEqual(rec["summary"]["dialect"], "corporate")
        with open(Ledger("fairit").path, encoding="utf-8") as f:
            self.assertNotIn(secret, f.read())


if __name__ == "__main__":
    unittest.main()
