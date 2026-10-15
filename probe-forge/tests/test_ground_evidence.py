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


class TestFairit003WhenAndCorrections(unittest.TestCase):
    """PARAM-FAIRIT-003: vacuous when-values, sequence ordering, and
    correction referential checks. (Ground-only; no ledger writes.)"""

    def test_vacuous_when_rejected(self):
        with self.assertRaises(GroundError):
            PersonState("sometime", "Mara", "cooperative")

    def test_vacuous_when_case_and_whitespace_insensitive(self):
        for when in ("  SOMETIME  ", "Some Time", "UNKNOWN", "tbd", "?"):
            with self.assertRaises(GroundError, msg=when):
                PersonState(when, "Mara", "cooperative")

    def test_informative_non_iso_when_still_passes(self):
        # The vacuity line is exact-match: anything naming a time passes,
        # even if the lightweight parser can't order it.
        p = PersonState("during the standup", "Mara", "cooperative")
        self.assertEqual(p.when, "during the standup")

    def test_vacuous_line_is_exact_match(self):
        # "sometime in June" still indexes June — the operator's content,
        # not a vacuous time-index.
        p = PersonState("sometime in June", "Mara", "cooperative")
        self.assertEqual(p.when, "sometime in June")

    def test_ordered_iso_sequence_passes(self):
        GroundMap(person_states=[
            PersonState("2026-08-15", "Mara", "assuring"),
            PersonState("2026-10-03", "Mara", "deflecting"),
        ])

    def test_out_of_order_sequence_rejected(self):
        with self.assertRaises(GroundError):
            GroundMap(person_states=[
                PersonState("2026-10-03", "Mara", "deflecting"),
                PersonState("2026-08-15", "Mara", "assuring"),
            ])

    def test_equal_when_values_allowed(self):
        GroundMap(person_states=[
            PersonState("2026-08-15", "Mara", "assuring"),
            PersonState("2026-08-15", "Mara", "also quiet"),
        ])

    def test_ordering_is_per_person(self):
        # A's states need not sort against B's: the timeline is a
        # per-person sequence.
        GroundMap(person_states=[
            PersonState("2026-10-03", "Mara", "deflecting"),
            PersonState("2026-08-15", "Lee", "assuring"),
        ])

    def test_unparseable_whens_do_not_order(self):
        # Labels the lightweight parser can't read are carried as unknown
        # points — they neither order nor break the chain.
        GroundMap(person_states=[
            PersonState("after lunch", "Mara", "assuring"),
            PersonState("before lunch", "Mara", "deflecting"),
        ])

    def test_ordering_enforced_across_unparseable_gaps(self):
        with self.assertRaises(GroundError):
            GroundMap(person_states=[
                PersonState("2026-10-03", "Mara", "deflecting"),
                PersonState("sometime later", "Mara", "quiet"),
                PersonState("2026-08-15", "Mara", "assuring"),
            ])

    def test_correction_with_resolving_refs_passes(self):
        GroundMap(
            person_states=[
                PersonState("2026-09-20", "Mara", "cooperative"),
            ],
            corrections=[
                Correction("detail", "date was the 21st, not the 20th",
                           person="Mara", when="2026-09-20"),
            ],
        )

    def test_correction_unknown_person_rejected(self):
        with self.assertRaises(GroundError):
            GroundMap(
                person_states=[
                    PersonState("2026-09-20", "Mara", "cooperative"),
                ],
                corrections=[
                    Correction("core-claim", "Zed was never told",
                               person="Zed"),
                ],
            )

    def test_correction_unknown_when_for_known_person_rejected(self):
        with self.assertRaises(GroundError):
            GroundMap(
                person_states=[
                    PersonState("2026-09-20", "Mara", "cooperative"),
                ],
                corrections=[
                    Correction("detail", "time was 3pm not 2pm",
                               person="Mara", when="2026-09-21"),
                ],
            )

    def test_correction_when_only_resolves_against_any_state(self):
        GroundMap(
            person_states=[
                PersonState("2026-09-20", "Mara", "cooperative"),
            ],
            corrections=[
                Correction("detail", "time was 3pm not 2pm",
                           when="2026-09-20"),
            ],
        )
        with self.assertRaises(GroundError):
            GroundMap(
                person_states=[
                    PersonState("2026-09-20", "Mara", "cooperative"),
                ],
                corrections=[
                    Correction("detail", "time was 3pm not 2pm",
                               when="2026-09-21"),
                ],
            )

    def test_correction_person_match_is_case_insensitive(self):
        GroundMap(
            person_states=[
                PersonState("2026-09-20", "Mara", "cooperative"),
            ],
            corrections=[
                Correction("detail", "date fixed", person="mara"),
            ],
        )

    def test_correction_without_refs_unchanged(self):
        # Backward compatibility: Correction(kind, text) still constructs,
        # and ref-less corrections pass the map check.
        GroundMap(corrections=[
            Correction("detail", "time was 3pm not 2pm"),
            Correction("core-claim", "denial became admission"),
        ])

    def test_same_day_date_datetime_mix_not_out_of_order(self):
        # Review E1: a bare date means "that day", not "midnight" — a
        # same-day date/datetime mix must not raise.
        GroundMap(person_states=[
            PersonState("2026-08-15T09:00", "Mara", "assuring"),
            PersonState("2026-08-15", "Mara", "quiet"),
        ])
        GroundMap(person_states=[
            PersonState("2026-08-15", "Mara", "quiet"),
            PersonState("2026-08-15T09:00", "Mara", "assuring"),
        ])
        # But a genuinely earlier day after a later one still raises.
        with self.assertRaises(GroundError):
            GroundMap(person_states=[
                PersonState("2026-08-16", "Mara", "deflecting"),
                PersonState("2026-08-15T09:00", "Mara", "assuring"),
            ])

    def test_correction_when_matches_semantically_not_by_string(self):
        # Review E2: "2026-09-20T00:00:00" names the same instant as
        # "2026-09-20" — string-equality would falsely reject it.
        GroundMap(
            person_states=[
                PersonState("2026-09-20", "Mara", "cooperative"),
            ],
            corrections=[
                Correction("detail", "time was 3pm not 2pm",
                           person="Mara", when="2026-09-20T00:00:00"),
                Correction("detail", "also that day", person="Mara",
                           when="2026-09-20T15:30"),
            ],
        )
        with self.assertRaises(GroundError):
            GroundMap(
                person_states=[
                    PersonState("2026-09-20", "Mara", "cooperative"),
                ],
                corrections=[
                    Correction("detail", "time was 3pm not 2pm",
                               person="Mara", when="2026-09-21T00:00:00"),
                ],
            )


class TestPersonViewAccessor(unittest.TestCase):
    """PARAM-FAIRIT-016: person-keyed view on GroundMap."""

    def _map(self):
        return GroundMap(person_states=[
            PersonState("2026-09-20", "Mara", "cooperative"),
            PersonState("2026-09-20", "Theo", "guarded"),
            PersonState("2026-09-21", "Mara", "withdrawn"),
        ])

    def test_returns_only_that_persons_states(self):
        seq = self._map().person_states_for("Mara")
        self.assertEqual([s.state for s in seq],
                         ["cooperative", "withdrawn"])

    def test_mapped_order_preserved(self):
        seq = self._map().person_states_for("Mara")
        self.assertEqual([s.when for s in seq],
                         ["2026-09-20", "2026-09-21"])

    def test_name_match_is_case_insensitive(self):
        seq = self._map().person_states_for("mara")
        self.assertEqual(len(seq), 2)

    def test_unknown_person_yields_empty_list(self):
        self.assertEqual(self._map().person_states_for("Nobody"), [])

    def test_render_stays_flat(self):
        # The audit log itself is unchanged: interleave, no grouping.
        text = self._map().render()
        self.assertLess(text.index("Mara"), text.index("Theo"))
        self.assertLess(text.index("Theo"),
                        text.index("Mara", text.index("Theo")))


if __name__ == "__main__":
    unittest.main()
