"""Tests for DISTILL: consolidates raw, never alters it."""

import tempfile
import unittest

from memdate import frontmatter as fm
from memdate.adapters import LocalFilesystemAdapter, StorageAdapter
from memdate.capture import capture
from memdate.config import ConfigError, MemoryConfig
from memdate.distill import (
    ARTIFACT,
    DistillError,
    distill,
    read_distilled,
)


def make_config(root):
    return MemoryConfig(root=root, domains=("work", "personal"))


class SaboteurAdapter(LocalFilesystemAdapter):
    """Modifies raw.md whenever distilled.md is written — simulates an
    isolation violation so we can prove distill() detects it."""

    def write(self, path, text):
        super().write(path, text)
        if path.endswith("distilled.md"):
            domain = path.split("/")[0]
            super().append(f"{domain}/raw.md", "\n## sabotage\n")


class DistillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)
        self.store = LocalFilesystemAdapter(self.tmp.name)
        capture(self.cfg, "work", "Note one.", adapter=self.store)
        capture(self.cfg, "work", "Note two.", adapter=self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def test_distill_writes_provenance_frontmatter(self):
        result = distill(self.cfg, "work", "Consolidated: two notes exist.",
                         today="2026-09-24", adapter=self.store)
        text = self.store.read("work/distilled.md")
        fields, body = fm.split(text)
        self.assertEqual(fields["artifact"], ARTIFACT)
        self.assertEqual(fields["domain"], "work")
        self.assertEqual(fields["date"], "2026-09-24")
        self.assertIn("protocol", fields)
        self.assertEqual(fields["lifecycle"], "ITERATIVE")
        self.assertIn("Consolidated: two notes exist.", body)
        self.assertEqual(result.lifecycle, "ITERATIVE")
        self.assertTrue(result.raw_untouched)

    def test_distill_refuses_without_raw(self):
        with self.assertRaises(DistillError):
            distill(self.cfg, "personal", "Nothing to consolidate.",
                    adapter=self.store)

    def test_distill_detects_raw_mutation(self):
        saboteur = SaboteurAdapter(self.tmp.name)
        # Seed raw through the saboteur so digests line up initially.
        with self.assertRaises(DistillError) as ctx:
            distill(self.cfg, "work", "Body.", adapter=saboteur)
        self.assertIn("Isolation violation", str(ctx.exception))

    def test_distill_leaves_raw_byte_identical(self):
        before = self.store.digest("work/raw.md")
        distill(self.cfg, "work", "Body.", adapter=self.store)
        self.assertEqual(before, self.store.digest("work/raw.md"))

    def test_invalid_lifecycle_rejected(self):
        with self.assertRaises(DistillError):
            distill(self.cfg, "work", "Body.", lifecycle="DRAFT",
                    adapter=self.store)

    def test_lifecycle_case_insensitive(self):
        result = distill(self.cfg, "work", "Body.", lifecycle="final",
                         adapter=self.store)
        self.assertEqual(result.lifecycle, "FINAL")

    def test_empty_body_rejected(self):
        with self.assertRaises(DistillError):
            distill(self.cfg, "work", "  ", adapter=self.store)

    def test_unknown_informs_domain_rejected(self):
        with self.assertRaises(ConfigError):
            distill(self.cfg, "work", "Body.", informs=["fhk"],
                    adapter=self.store)

    def test_entities_and_questions_round_trip(self):
        distill(
            self.cfg, "work", "Body.",
            entities=["Acme Corp", "Priya"],
            entity_notes={"Acme Corp": "client, contract renews Q1"},
            informs=["personal"],
            open_questions=["Does the Acme contract renew in Q1?"],
            adapter=self.store,
        )
        fields, _body = read_distilled(self.cfg, "work", adapter=self.store)
        self.assertEqual(fields["entities"], ["Acme Corp", "Priya"])
        self.assertEqual(fields["entity_notes"],
                         {"Acme Corp": "client, contract renews Q1"})
        self.assertEqual(fields["informs"], ["personal"])
        self.assertEqual(fields["open_questions"],
                         ["Does the Acme contract renew in Q1?"])

    def test_read_distilled_none_when_missing(self):
        self.assertIsNone(read_distilled(self.cfg, "personal",
                                         adapter=self.store))

    def test_read_distilled_rejects_wrong_artifact(self):
        self.store.write("work/distilled.md",
                         fm.render({"artifact": "something-else",
                                    "domain": "work", "date": "2026-09-24",
                                    "protocol": "x", "lifecycle": "ITERATIVE"})
                         + "Body.\n")
        with self.assertRaises(DistillError):
            read_distilled(self.cfg, "work", adapter=self.store)

    def test_second_distill_overwrites_derived_not_raw(self):
        distill(self.cfg, "work", "First pass.", adapter=self.store)
        raw_before = self.store.digest("work/raw.md")
        distill(self.cfg, "work", "Second pass.", lifecycle="FINAL",
                adapter=self.store)
        fields, body = read_distilled(self.cfg, "work", adapter=self.store)
        self.assertIn("Second pass.", body)
        self.assertEqual(fields["lifecycle"], "FINAL")
        self.assertEqual(raw_before, self.store.digest("work/raw.md"))


if __name__ == "__main__":
    unittest.main()
