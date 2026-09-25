"""Tests for DROP: the ingestion layer."""

import tempfile
import unittest

from memdate.adapters import LocalFilesystemAdapter
from memdate.config import MemoryConfig
from memdate.drop import ensure_layout, sweep_new


def make_config(root):
    return MemoryConfig(root=root, domains=("work", "personal"))


class DropTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)
        self.store = LocalFilesystemAdapter(self.tmp.name)
        ensure_layout(self.cfg, adapter=self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def _drop(self, filename, text):
        self.store.write(f"DROP/NEW/{filename}", text)

    def test_layout_created(self):
        for sub in ("NEW", "PROCESSED", "PENDING", "QUARANTINE"):
            self.assertTrue(self.store.exists(f"DROP/{sub}"))
        self.assertTrue(self.store.exists("work"))
        self.assertTrue(self.store.exists("personal"))

    def test_well_formed_file_captured_and_archived(self):
        self._drop("note1.md", "domain: work\n\nFixed the flaky test.")
        results = sweep_new(self.cfg, adapter=self.store)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].outcome, "captured")
        self.assertEqual(results[0].domain, "work")
        raw = self.store.read("work/raw.md")
        self.assertIn("Fixed the flaky test.", raw)
        self.assertIn("DROP/NEW/note1.md", raw)  # source recorded
        self.assertEqual(self.store.list_files("DROP/NEW"), [])
        processed = self.store.list_files("DROP/PROCESSED")
        self.assertEqual(len(processed), 1)
        self.assertTrue(processed[0].endswith("note1.md"))

    def test_missing_header_quarantined(self):
        self._drop("note.md", "No header here.")
        results = sweep_new(self.cfg, adapter=self.store)
        self.assertEqual(results[0].outcome, "quarantined")
        self.assertIn("header", results[0].reason)
        self.assertIsNone(self.store.read("work/raw.md"))
        quarantine = self.store.list_files("DROP/QUARANTINE")
        self.assertEqual(len(quarantine), 2)  # file + reason file
        self.assertTrue(any(n.endswith(".reason.txt") for n in quarantine))

    def test_unknown_domain_quarantined(self):
        self._drop("note.md", "domain: fhk\n\nSome note.")
        results = sweep_new(self.cfg, adapter=self.store)
        self.assertEqual(results[0].outcome, "quarantined")
        self.assertIn("fhk", results[0].reason)

    def test_interpretation_markers_quarantined(self):
        self._drop("note.md",
                   "domain: work\n\nIn summary, the project is fine.")
        results = sweep_new(self.cfg, adapter=self.store)
        self.assertEqual(results[0].outcome, "quarantined")
        self.assertIn("interpretation", results[0].reason)
        self.assertIsNone(self.store.read("work/raw.md"))

    def test_empty_body_quarantined(self):
        self._drop("note.md", "domain: work\n")
        results = sweep_new(self.cfg, adapter=self.store)
        self.assertEqual(results[0].outcome, "quarantined")

    def test_mixed_batch_processed_independently(self):
        self._drop("good.md", "domain: personal\n\nBought seeds.")
        self._drop("bad.md", "domain: nope\n\nLost note.")
        results = sweep_new(self.cfg, adapter=self.store)
        outcomes = {r.filename: r.outcome for r in results}
        self.assertEqual(outcomes, {"good.md": "captured",
                                    "bad.md": "quarantined"})
        self.assertIn("Bought seeds.", self.store.read("personal/raw.md"))

    def test_sweep_is_idempotent_on_empty_new(self):
        self.assertEqual(sweep_new(self.cfg, adapter=self.store), [])


if __name__ == "__main__":
    unittest.main()
