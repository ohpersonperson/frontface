"""Tests for CAPTURE: append-only, timestamped, never interpreting."""

import tempfile
import unittest
from datetime import datetime, timezone

from memdate.adapters import LocalFilesystemAdapter
from memdate.capture import (
    CaptureError,
    InterpretationError,
    capture,
    read_raw,
    route,
    scan_interpretation,
)
from memdate.config import ConfigError, MemoryConfig


def make_config(root, **kw):
    return MemoryConfig(root=root, domains=("work", "personal"), **kw)


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)
        self.store = LocalFilesystemAdapter(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_capture_creates_timestamped_entry(self):
        now = datetime(2026, 9, 24, 18, 0, tzinfo=timezone.utc)
        result = capture(self.cfg, "work", "Shipped the patch.", now=now,
                         adapter=self.store)
        text = self.store.read("work/raw.md")
        self.assertIn("2026-09-24 18:00", text)
        self.assertIn("Shipped the patch.", text)
        self.assertTrue(text.startswith("## "))
        self.assertEqual(result.domain, "work")
        self.assertFalse(result.bypassed_check)

    def test_capture_appends_and_preserves_order(self):
        capture(self.cfg, "work", "First note.", adapter=self.store)
        before = self.store.read("work/raw.md")
        capture(self.cfg, "work", "Second note.", adapter=self.store)
        after = self.store.read("work/raw.md")
        # Append-only: prior content is a strict prefix of new content.
        self.assertTrue(after.startswith(before))
        self.assertLess(after.index("First note."), after.index("Second note."))

    def test_capture_records_source(self):
        capture(self.cfg, "work", "A note.", source="phone", adapter=self.store)
        self.assertIn("source: phone", self.store.read("work/raw.md"))

    def test_empty_text_rejected(self):
        with self.assertRaises(CaptureError):
            capture(self.cfg, "work", "   ", adapter=self.store)

    def test_unknown_domain_rejected(self):
        with self.assertRaises(ConfigError):
            capture(self.cfg, "fhk", "A note.", adapter=self.store)

    def test_domain_matching_is_case_insensitive(self):
        capture(self.cfg, "WORK", "A note.", adapter=self.store)
        self.assertIsNotNone(self.store.read("work/raw.md"))

    def test_interpretation_markers_rejected(self):
        with self.assertRaises(InterpretationError) as ctx:
            capture(self.cfg, "work",
                    "In summary, the meeting went well and we should move on.",
                    adapter=self.store)
        self.assertIn("in summary", str(ctx.exception).lower())
        # Nothing was written.
        self.assertIsNone(self.store.read("work/raw.md"))

    def test_force_bypass_records_itself(self):
        result = capture(self.cfg, "work",
                         "Overall, things are fine.",
                         force=True, adapter=self.store)
        self.assertTrue(result.bypassed_check)
        text = self.store.read("work/raw.md")
        self.assertIn("interpretation-check bypassed", text)
        self.assertIn("Overall, things are fine.", text)

    def test_scan_is_case_insensitive(self):
        hits = scan_interpretation("THE BOTTOM LINE is x", ("the bottom line",))
        self.assertEqual(hits, ["the bottom line"])
        self.assertEqual(scan_interpretation("plain note", ("the bottom line",)), [])

    def test_custom_markers_via_config(self):
        cfg = make_config(self.tmp.name, interpretation_markers=("synergy",))
        with self.assertRaises(InterpretationError):
            capture(cfg, "work", "Great synergy today.", adapter=self.store)

    def test_read_raw_none_when_empty(self):
        self.assertIsNone(read_raw(self.cfg, "work", adapter=self.store))

    def test_read_raw_unknown_domain(self):
        with self.assertRaises(ConfigError):
            read_raw(self.cfg, "nope", adapter=self.store)


class RouteTests(unittest.TestCase):
    def test_route_capture(self):
        self.assertEqual(route("capture"), "capture")
        self.assertEqual(route("  CAPTURE "), "capture")

    def test_route_distill(self):
        self.assertEqual(route("distill"), "distill")

    def test_route_both_rejected(self):
        with self.assertRaises(CaptureError):
            route("both")

    def test_route_unknown_rejected(self):
        with self.assertRaises(CaptureError):
            route("summarize")


if __name__ == "__main__":
    unittest.main()
