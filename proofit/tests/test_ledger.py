"""Ledger tests for proofit: lint runs are recorded as digests, never raw text."""

import json
import os
import tempfile
import unittest

from proofit.__main__ import cmd_lint
from proofit.ledger import Ledger


class LedgerEnvTest(unittest.TestCase):
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

    def _lint_tmp(self, text):
        path = os.path.join(self.tmp.name, "draft.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        cmd_lint(path)
        return path

    def test_lint_records_digest_not_text(self):
        secret = "ledger-test-secret-xyz-123"
        self._lint_tmp(f"# Draft\n\n{secret}\n")
        recs = Ledger("proofit").read()
        self.assertEqual(len(recs), 1)
        rec = recs[0]
        self.assertEqual(rec["event"], "lint")
        self.assertEqual(rec["tool"], "proofit")
        self.assertIn("input_digest", rec)
        self.assertEqual(len(rec["input_digest"]), 64)
        self.assertIn("by_rule", rec["summary"])
        # the raw text must not appear anywhere in the ledger file
        with open(Ledger("proofit").path, encoding="utf-8") as f:
            self.assertNotIn(secret, f.read())

    def test_no_ledger_opt_out(self):
        os.environ["FRONTFACE_NO_LEDGER"] = "1"
        self._lint_tmp("# Draft\n")
        self.assertEqual(Ledger("proofit").read(), [])

    def test_summary_counts(self):
        self._lint_tmp("# Draft one\n")
        self._lint_tmp("# Draft two\n")
        s = Ledger("proofit").summary()
        self.assertEqual(s["records"], 2)
        self.assertEqual(s["events"], {"lint": 2})
        self.assertIsNotNone(s["first"])
        self.assertIsNotNone(s["last"])

    def test_version_stamped(self):
        self._lint_tmp("# Draft\n")
        rec = Ledger("proofit").read()[0]
        self.assertEqual(rec["tool_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
