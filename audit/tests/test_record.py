"""Tests for the audit record (record.py), the overlay contract, and evidence."""

import unittest

from postmo.disciplines import D1, D5
from postmo.evidence import (
    EvidenceError, EvidenceItem, check_matches_engine, normalize_tag, tag_list,
)
from postmo.overlay import NEVER, attachment_for, describe_contract
from postmo.record import (
    AuditRecord, DisciplineEntry, RecordError, check_stand_down, parse,
)
from postmo.scans import (
    Correction, HeldTension, MotiveFlag, PersonState, ScanError, SofteningFlag,
)


def sample_record() -> AuditRecord:
    rec = AuditRecord(case_name="Warehouse shift dispute")
    rec.tensions.append(HeldTension(
        text="Dana says the pallet was already damaged. Marco says it was intact."
    ))
    rec.tensions.append(HeldTension(
        text="Marco says Dana reported it immediately. Dana says she found it that way."
    ))
    rec.states.append(PersonState(when="2026-09-18", person="Dana", state="calm, cooperative"))
    rec.states.append(PersonState(when="2026-09-20", person="Dana", state="withdrawn, clipped"))
    rec.states.append(PersonState(when="2026-09-18", person="Marco", state="agitated, loud"))
    rec.corrections.append(Correction(kind="detail", text="The shift was Tuesday, not Monday."))
    rec.corrections.append(Correction(kind="core-claim", text="Marco withdrew the claim that Dana hid the damage."))
    rec.motive_flags.append(MotiveFlag(
        sentence="He hid it because he panicked.", pattern=r"because\s+(he|she|they)\s+\w+ed\b",
        severity="flag"))
    rec.softening_flags.append(SofteningFlag(
        kind="downgrade", detail="'lied' in the original became 'misspoke' in the restatement.",
        original_term="lied", replacement="misspoke"))
    rec.log(D1, "enforced", "2 tensions held as parallel sentences, 0 subordinators")
    rec.log(D5, "flagged", "1 downgrade caught: lied -> misspoke")
    rec.evidence.append(EvidenceItem(text="Dana stated the pallet was damaged on arrival.", tag="claim"))
    rec.evidence.append(EvidenceItem(text="Shift log shows the pallet scanned at 14:02.", tag="observation"))
    return rec


class RecordSchemaTest(unittest.TestCase):
    def test_requires_case_name(self):
        with self.assertRaises(RecordError):
            AuditRecord(case_name="  ")

    def test_rejects_bad_lifecycle(self):
        with self.assertRaises(RecordError):
            AuditRecord(case_name="x", lifecycle="DRAFT")

    def test_render_has_frontmatter(self):
        rendered = sample_record().render()
        self.assertIn("artifact: audit-record", rendered)
        self.assertIn("protocol: postmo/1.0", rendered)
        self.assertIn("lifecycle: FINAL", rendered)
        self.assertIn("# Audit record: Warehouse shift dispute", rendered)

    def test_render_has_all_five_discipline_sections(self):
        rendered = sample_record().render()
        for heading in ("Held tensions", "Person-state sequences", "Corrections",
                        "Motive flags", "Softening flags", "Discipline log", "Evidence"):
            self.assertIn(heading, rendered)

    def test_stand_down_rejects_synthesis(self):
        with self.assertRaises(RecordError):
            check_stand_down("# Audit record: x\n\n## Synthesis\n\nThey reconciled.")
        with self.assertRaises(RecordError):
            check_stand_down("# Audit record: x\n\n## Resolution\n\nCase closed.")
        with self.assertRaises(RecordError):
            check_stand_down("# Audit record: x\n\n## Verdict\n\nHe is guilty.")

    def test_render_rejects_stand_down_violation(self):
        rec = sample_record()
        rendered = rec.render() + "\n## Synthesis\n\nThey made up."
        with self.assertRaises(RecordError):
            check_stand_down(rendered)

    def test_conversation_digest_names_tensions(self):
        convo = sample_record().render_conversation()
        self.assertIn("not picking one", convo)
        self.assertIn("Dana", convo)
        self.assertIn("Correction typed as core-claim", convo)
        self.assertIn("Nothing here is resolved", convo)


class RecordRoundTripTest(unittest.TestCase):
    def test_parse_returns_full_record(self):
        rec = parse(sample_record().render())
        self.assertEqual(rec.case_name, "Warehouse shift dispute")
        self.assertEqual(len(rec.tensions), 2)
        self.assertEqual(len(rec.states), 3)
        self.assertEqual(len(rec.corrections), 2)
        self.assertEqual(len(rec.motive_flags), 1)
        self.assertEqual(len(rec.softening_flags), 1)
        self.assertEqual(len(rec.discipline_log), 2)
        self.assertEqual(len(rec.evidence), 2)

    def test_tensions_revalidate_on_parse(self):
        self.assertEqual(rec_tension_texts()[0],
                         "Dana says the pallet was already damaged. Marco says it was intact.")

    def test_hand_edited_subordinator_fails_parse(self):
        rendered = sample_record().render().replace(
            "- Dana says the pallet was already damaged. Marco says it was intact.",
            "- Dana says the pallet was already damaged, but Marco says it was intact.",
        )
        with self.assertRaises(ScanError):
            parse(rendered)

    def test_parse_rejects_non_record(self):
        with self.assertRaises(RecordError):
            parse("---\nartifact: something-else\n---\n\n# Audit record: x")

    def test_parse_rejects_resolution_section(self):
        rendered = sample_record().render() + "\n## Verdict\n\nDana is right."
        with self.assertRaises(RecordError):
            parse(rendered)

    def test_double_round_trip_stable(self):
        once = parse(sample_record().render())
        twice = parse(once.render())
        self.assertEqual(once.render(), twice.render())


def rec_tension_texts():
    return [t.text for t in parse(sample_record().render()).tensions]


class DisciplineLogTest(unittest.TestCase):
    def test_log_appends_timestamped_entry(self):
        rec = AuditRecord(case_name="x")
        entry = rec.log(D1, "enforced", "held 1 tension")
        self.assertEqual(len(rec.discipline_log), 1)
        self.assertTrue(entry.timestamp)  # ISO timestamp present
        self.assertIn("T", entry.timestamp)

    def test_rejects_bad_discipline_and_action(self):
        with self.assertRaises(RecordError):
            DisciplineEntry(discipline=9, action="enforced", detail="x")
        with self.assertRaises(RecordError):
            DisciplineEntry(discipline=D1, action="ignored", detail="x")
        with self.assertRaises(RecordError):
            DisciplineEntry(discipline=D1, action="enforced", detail=" ")

    def test_core_claim_changes_filters(self):
        rec = sample_record()
        core = rec.core_claim_changes()
        self.assertEqual(len(core), 1)
        self.assertEqual(core[0].kind, "core-claim")

    def test_states_for_person(self):
        rec = sample_record()
        dana = rec.states_for("dana")  # case-insensitive
        self.assertEqual(len(dana), 2)
        self.assertEqual(rec.states_for("nobody"), [])


class EvidenceTaxonomyTest(unittest.TestCase):
    def test_eleven_tags(self):
        self.assertEqual(len(tag_list()), 11)
        self.assertIn("OBFUSCATION", tag_list())

    def test_rejects_unknown_tag(self):
        with self.assertRaises(EvidenceError):
            EvidenceItem(text="x", tag="RUMOR")

    def test_obfuscation_needs_probe(self):
        with self.assertRaises(EvidenceError):
            normalize_tag("OBFUSCATION")
        self.assertEqual(normalize_tag("obfuscation", probe_ran=True), "OBFUSCATION")

    def test_matches_engine_or_skips(self):
        result = check_matches_engine()
        self.assertIn(result, ("matches", "skipped: adversarial_ifs not importable"))


class OverlayContractTest(unittest.TestCase):
    def test_attachment_points(self):
        self.assertEqual(attachment_for("Decompose"), (2, 3, 4))
        self.assertEqual(attachment_for("Collide"), (1, 5))

    def test_unknown_phase_rejected(self):
        from postmo.overlay import OverlayError, attachment_for
        with self.assertRaises(OverlayError):
            attachment_for("Synthesize")

    def test_never_list_covers_the_contract(self):
        joined = " ".join(NEVER)
        self.assertIn("resolve a contradiction", joined)
        self.assertIn("synthesis", joined)
        self.assertIn("interrogation unasked", joined)

    def test_describe_contract_mentions_phases(self):
        text = describe_contract()
        self.assertIn("Decompose", text)
        self.assertIn("Collide", text)
        self.assertIn("report the audit record and stop", text)


if __name__ == "__main__":
    unittest.main()
