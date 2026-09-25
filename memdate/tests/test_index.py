"""Tests for INDEX: cross-domain connective tissue, regenerated mechanically."""

import tempfile
import unittest

from memdate import frontmatter as fm
from memdate.adapters import LocalFilesystemAdapter
from memdate.capture import capture
from memdate.config import MemoryConfig
from memdate.distill import distill
from memdate.index import (
    INDEX_PATH,
    IndexError,
    read_index,
    regenerate_index,
)


def make_config(root):
    return MemoryConfig(root=root, domains=("work", "personal", "projects"))


class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = make_config(self.tmp.name)
        self.store = LocalFilesystemAdapter(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _seed(self, domain, body, **kw):
        capture(self.cfg, domain, f"seed note for {domain}", adapter=self.store)
        return distill(self.cfg, domain, body, today="2026-09-24",
                       adapter=self.store, **kw)

    def test_single_domain_distill_skips_index(self):
        self._seed("work", "Work body.")
        result = regenerate_index(self.cfg, ["work"], adapter=self.store)
        self.assertTrue(result.skipped)
        self.assertIn("Single-domain", result.reason)
        self.assertIsNone(self.store.read(INDEX_PATH))

    def test_two_domains_regenerate(self):
        self._seed("work", "Work body.", entities=["Acme Corp"])
        self._seed("personal", "Personal body.", entities=["Acme Corp"])
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertFalse(result.skipped)
        self.assertEqual(result.cross_domain_entities, 1)
        text = self.store.read(INDEX_PATH)
        self.assertIn("**Acme Corp**: personal, work", text)

    def test_single_domain_entities_excluded(self):
        self._seed("work", "Work body.", entities=["Acme Corp", "Solo Project"])
        self._seed("personal", "Personal body.", entities=["Acme Corp"])
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.cross_domain_entities, 1)
        text = self.store.read(INDEX_PATH)
        self.assertNotIn("Solo Project", text.split("## Open Questions")[0])

    def test_open_questions_aggregated_with_source(self):
        self._seed("work", "Work body.",
                   open_questions=["Does the contract renew?"])
        self._seed("personal", "Personal body.",
                   open_questions=["Call the accountant?"])
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.open_questions, 2)
        text = self.store.read(INDEX_PATH)
        self.assertIn("Does the contract renew? (from work)", text)
        self.assertIn("Call the accountant? (from personal)", text)

    def test_cross_domain_questions_prioritized(self):
        self._seed("work", "Work body.", entities=["Acme Corp"],
                   open_questions=["Does Acme Corp renew in Q1?"])
        self._seed("personal", "Personal body.", entities=["Acme Corp"],
                   open_questions=["Buy more coffee?"])
        regenerate_index(self.cfg, ["work", "personal"], adapter=self.store)
        text = self.store.read(INDEX_PATH)
        section = text.split("## Open Questions")[1].split("## Hot Zones")[0]
        self.assertLess(section.index("Acme Corp renew"),
                        section.index("Buy more coffee?"))
        self.assertIn("[cross-domain]", section)

    def test_dependencies_and_chains(self):
        self._seed("work", "Work body.", informs=["personal"])
        self._seed("personal", "Personal body.", informs=["projects"])
        self._seed("projects", "Projects body.")
        regenerate_index(self.cfg, ["work", "personal", "projects"],
                          adapter=self.store)
        text = self.store.read(INDEX_PATH)
        self.assertIn("work informs: personal", text)
        self.assertIn("work -> personal -> projects", text)

    def test_uncertainty_and_divergence_flags_are_hot_zones(self):
        self._seed("work", "Work body.\n? Not sure the date is right.\n! Raw says Tuesday, distilled says Wednesday.")
        self._seed("personal", "Personal body.")
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.hot_zones, 2)
        text = self.store.read(INDEX_PATH)
        self.assertIn("[work] uncertainty: Not sure the date is right.", text)
        self.assertIn("[work] raw<->distilled divergence:", text)

    def test_differing_entity_notes_flag_tension(self):
        self._seed("work", "Work body.", entities=["Acme Corp"],
                   entity_notes={"Acme Corp": "client, happy"})
        self._seed("personal", "Personal body.", entities=["Acme Corp"],
                   entity_notes={"Acme Corp": "client, late payments"})
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.hot_zones, 1)
        text = self.store.read(INDEX_PATH)
        self.assertIn("[tension] Acme Corp", text)

    def test_no_questions_means_final(self):
        self._seed("work", "Work body.")
        self._seed("personal", "Personal body.")
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.lifecycle, "FINAL")
        fields, _body = read_index(self.cfg, adapter=self.store)
        self.assertEqual(fields["lifecycle"], "FINAL")

    def test_questions_mean_iterative(self):
        self._seed("work", "Work body.", open_questions=["One open thing."])
        self._seed("personal", "Personal body.")
        result = regenerate_index(self.cfg, ["work", "personal"],
                                  adapter=self.store)
        self.assertEqual(result.lifecycle, "ITERATIVE")

    def test_fewer_than_two_distilled_domains_fails(self):
        self._seed("work", "Work body.")
        with self.assertRaises(IndexError):
            regenerate_index(self.cfg, ["work", "personal"], adapter=self.store)

    def test_index_frontmatter_valid(self):
        self._seed("work", "Work body.")
        self._seed("personal", "Personal body.")
        regenerate_index(self.cfg, ["work", "personal"], adapter=self.store)
        fields, _body = read_index(self.cfg, adapter=self.store)
        fm.require(fields, "artifact", "date", "protocol", "lifecycle",
                   what="index")
        self.assertEqual(fields["artifact"], "memdate-cross-domain-index")

    def test_read_index_none_when_missing(self):
        self.assertIsNone(read_index(self.cfg, adapter=self.store))

    def test_index_is_derived_not_authoritative(self):
        # Regenerating twice with no new distills produces identical output.
        self._seed("work", "Work body.", entities=["Acme Corp"])
        self._seed("personal", "Personal body.", entities=["Acme Corp"])
        regenerate_index(self.cfg, ["work", "personal"], today="2026-09-24",
                         adapter=self.store)
        first = self.store.read(INDEX_PATH)
        regenerate_index(self.cfg, ["work", "personal"], today="2026-09-24",
                         adapter=self.store)
        self.assertEqual(first, self.store.read(INDEX_PATH))


if __name__ == "__main__":
    unittest.main()
