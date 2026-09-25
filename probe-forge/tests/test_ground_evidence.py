"""Tests for ground mapping and the evidence taxonomy."""

import unittest

from fairit.ground import (
    Correction,
    GroundError,
    GroundMap,
    HeldTension,
    PersonState,
    find_subordinators,
)
from fairit.evidence import (
    FORGE_TIERS,
    FORGE_MISSING,
    TAXONOMY,
    EvidenceError,
    EvidenceItem,
    check_matches_engine,
    forge_mapping_table,
    normalize_tag,
    tag_list,
)


class TestHeldTensions(unittest.TestCase):
    def test_parallel_sentences_pass(self):
        t = HeldTension("The email promised a refund. No refund has arrived.")
        self.assertIn("refund", t.text)

    def test_subordinating_but_rejected(self):
        with self.assertRaises(GroundError):
            HeldTension("The email promised a refund, but no refund has arrived.")

    def test_subordinating_however_rejected(self):
        with self.assertRaises(GroundError):
            HeldTension("She apologized. However, the behavior repeated.")

    def test_which_means_rejected(self):
        with self.assertRaises(GroundError):
            HeldTension("He missed the meeting, which means he doesn't care.")

    def test_empty_rejected(self):
        with self.assertRaises(GroundError):
            HeldTension("   ")

    def test_find_subordinators(self):
        self.assertEqual(find_subordinators("a, but b"), ["but"])
        self.assertEqual(find_subordinators("a. b. also c."), [])


class TestPersonStatesAndCorrections(unittest.TestCase):
    def test_person_state_time_indexed(self):
        p = PersonState("2026-09-20", "Mara", "cooperative in the meeting")
        self.assertEqual(p.when, "2026-09-20")

    def test_person_state_empty_rejected(self):
        with self.assertRaises(GroundError):
            PersonState("", "Mara", "cooperative")

    def test_correction_kinds(self):
        d = Correction("detail", "date was the 21st, not the 20th")
        c = Correction("core-claim", "first said no one was told; now says Mara was told")
        self.assertEqual(d.kind, "detail")
        self.assertEqual(c.kind, "core-claim")

    def test_bad_correction_kind_rejected(self):
        with self.assertRaises(GroundError):
            Correction("vibe", "something changed")

    def test_core_claim_changes_are_the_signal(self):
        g = GroundMap(
            corrections=[
                Correction("detail", "time was 3pm not 2pm"),
                Correction("core-claim", "denial became admission"),
            ]
        )
        signal = g.core_claim_changes()
        self.assertEqual(len(signal), 1)
        self.assertIn("admission", signal[0].text)


class TestTaxonomy(unittest.TestCase):
    def test_eleven_tags(self):
        self.assertEqual(len(TAXONOMY), 11)
        self.assertIn("OBFUSCATION", TAXONOMY)

    def test_forge_eight_are_subset(self):
        self.assertTrue(FORGE_TIERS <= set(TAXONOMY))
        self.assertEqual(len(FORGE_TIERS), 8)
        # Everything the forge named maps 1:1 — no renames.
        self.assertEqual(FORGE_TIERS & FORGE_MISSING, frozenset())

    def test_forge_missing_are_recognized(self):
        self.assertEqual(FORGE_MISSING, {"HYPOTHESIS", "REQUIREMENT", "DEPENDENCY"})

    def test_mapping_table_covers_all(self):
        table = forge_mapping_table()
        for tier in FORGE_TIERS:
            self.assertIn(tier, table)
        for tier in FORGE_MISSING:
            self.assertIn(tier, table)
            self.assertIn("recognized", table)

    def test_obfuscation_requires_probe(self):
        with self.assertRaises(EvidenceError):
            normalize_tag("OBFUSCATION")
        self.assertEqual(normalize_tag("OBFUSCATION", probe_ran=True), "OBFUSCATION")

    def test_suspected_stays_claim(self):
        self.assertEqual(normalize_tag("claim"), "CLAIM")

    def test_unknown_tag_rejected(self):
        with self.assertRaises(EvidenceError):
            EvidenceItem("something", "MAYBE")

    def test_empty_text_rejected(self):
        with self.assertRaises(EvidenceError):
            EvidenceItem("   ", "FACT")

    def test_matches_engine_when_available(self):
        result = check_matches_engine()
        # Either "matches" (sibling package on path) or "skipped".
        self.assertIn(result.split(":")[0], ("matches", "skipped"))


if __name__ == "__main__":
    unittest.main()
