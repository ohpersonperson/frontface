"""Ledger tests for postmo: audits record counts, never the case material."""

import os
import tempfile
import unittest

from postmo.ledger import Ledger
from postmo.record import AuditRecord, parse
from postmo.scans import HeldTension, PersonState
from postmo.disciplines import D1


class PostmoLedgerTest(unittest.TestCase):
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

    def test_parse_records_audit_counts(self):
        secret = "ledger-test-secret-postmo-222"
        rec = AuditRecord(case_name="Ledger test case")
        rec.tensions.append(HeldTension(
            text=f"Dana says X. Marco says Y. {secret}"))
        rec.states.append(PersonState(when="2026-09-18", person="Dana",
                                      state="calm"))
        rec.log(D1, "enforced", "2 tensions held, 0 subordinators")
        parsed = parse(rec.render())
        self.assertEqual(parsed.case_name, "Ledger test case")
        recs = Ledger("postmo").read()
        self.assertEqual(len(recs), 1)
        summary = recs[0]["summary"]
        self.assertEqual(recs[0]["event"], "audit")
        self.assertEqual(summary["tensions"], 1)
        self.assertEqual(summary["states"], 1)
        self.assertEqual(summary["disciplines_used"], [1])
        with open(Ledger("postmo").path, encoding="utf-8") as f:
            self.assertNotIn(secret, f.read())


if __name__ == "__main__":
    unittest.main()
