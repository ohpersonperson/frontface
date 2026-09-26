"""Ledger tests for flashy: session lifecycle is recorded as digests."""

import os
import tempfile
import unittest

from flashy.ledger import Ledger
from flashy.session import MissionSession


class FlashyLedgerTest(unittest.TestCase):
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

    def test_session_lifecycle_recorded(self):
        secret = "ledger-test-secret-flashy-000"
        s = MissionSession(f"Ship the thing {secret}", slug="ship")
        s.plan(["draft", "review"])
        s.start_executing()
        s.complete_milestone("draft")
        s.descope("review")
        recs = Ledger("flashy").read()
        events = [r["event"] for r in recs]
        self.assertEqual(events, ["session_start", "milestone", "descope"])
        ms = recs[1]["summary"]
        self.assertEqual(ms["completed"], 1)
        self.assertEqual(ms["remaining"], 1)  # "review" still active then
        ds = recs[2]["summary"]
        self.assertEqual(ds["remaining"], 0)  # descoped: nothing left
        with open(Ledger("flashy").path, encoding="utf-8") as f:
            body = f.read()
        self.assertNotIn(secret, body)
        self.assertNotIn("draft", body)  # milestone names are digested too

    def test_summary(self):
        s = MissionSession("Do stuff", slug="do")
        s.plan(["one"])
        summ = Ledger("flashy").summary()
        self.assertEqual(summ["records"], 1)
        self.assertEqual(summ["events"], {"session_start": 1})


if __name__ == "__main__":
    unittest.main()
