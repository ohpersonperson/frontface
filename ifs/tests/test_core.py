import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pressit import evidence, protocol, overlay


class TestEvidenceTaxonomy(unittest.TestCase):
    def test_all_core_tags_accepted(self):
        for tag in ("FACT", "OBSERVATION", "CLAIM", "INFERENCE", "ASSUMPTION",
                    "HYPOTHESIS", "REQUIREMENT", "CONSTRAINT", "DEPENDENCY", "UNKNOWN"):
            item = evidence.EvidenceItem(text="x", tag=tag)
            self.assertEqual(item.tag, tag)

    def test_unknown_tag_rejected(self):
        with self.assertRaises(evidence.EvidenceError):
            evidence.EvidenceItem(text="x", tag="GUESS")

    def test_obfuscation_rejected_without_overlay(self):
        with self.assertRaises(evidence.EvidenceError):
            evidence.normalize_tag("OBFUSCATION", overlay_on=False)

    def test_obfuscation_allowed_with_overlay(self):
        self.assertEqual(
            evidence.normalize_tag("OBFUSCATION", overlay_on=True), "OBFUSCATION")

    def test_empty_text_rejected(self):
        with self.assertRaises(evidence.EvidenceError):
            evidence.EvidenceItem(text="   ", tag="FACT")


class TestProtocol(unittest.TestCase):
    def test_two_takes_one_pair(self):
        self.assertEqual(protocol.required_collision_pairs(["A", "B"]), ["A/B"])

    def test_three_takes_three_pairs(self):
        self.assertEqual(protocol.required_collision_pairs(["A", "B", "C"]),
                         ["A/B", "A/C", "B/C"])

    def test_bad_take_count_rejected(self):
        with self.assertRaises(ValueError):
            protocol.required_collision_pairs(["A"])
        with self.assertRaises(ValueError):
            protocol.required_collision_pairs(["A", "B", "C", "D"])

    def _key(self, statement="S"):
        return protocol.KeyDraft(
            statement=statement, classification="PLAUSIBLE", evidence="FACT #1",
            confidence="MODERATE", vulnerability="v", falsifier="f")

    def test_three_to_five_keys_pass(self):
        for n in (3, 4, 5):
            keys = [self._key(f"S{i}") for i in range(n)]
            self.assertEqual(len(protocol.validate_keys(keys)), n)

    def test_two_keys_rejected(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_keys([self._key("a"), self._key("b")])

    def test_six_keys_rejected(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_keys([self._key(f"S{i}") for i in range(6)])

    def test_key_missing_falsifier_rejected(self):
        bad = protocol.KeyDraft(statement="S", classification="PLAUSIBLE",
                                evidence="e", confidence="MODERATE",
                                vulnerability="v", falsifier=" ")
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_keys([self._key("a"), self._key("b"), bad])

    def test_bad_classification_rejected(self):
        bad = protocol.KeyDraft(statement="S", classification="PROVEN",
                                evidence="e", confidence="MODERATE",
                                vulnerability="v", falsifier="f")
        with self.assertRaises(protocol.ProtocolError):
            protocol.validate_keys([self._key("a"), self._key("b"), bad])

    def test_field_input_rejects_empty_field(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.FieldInput(field="  ")

    def test_field_input_rejects_unknown_mode(self):
        with self.assertRaises(protocol.ProtocolError):
            protocol.FieldInput(field="x", mode="oracle")

    def test_system_prompt_is_decoupled(self):
        banned = ["tarot", "astrology", "harmonic key", "Tribunal", "Anvil",
                  "Hammer", "Furnace", "mysti"]
        lowered = protocol.SYSTEM_PROMPT.lower()
        for word in banned:
            self.assertNotIn(word, lowered, f"coupling residue: {word}")
        # the protocol must still name its moving parts
        for word in ["diverge", "collide", "falsifier", "obfuscation"]:
            self.assertIn(word, lowered, f"missing mechanism term: {word}")

    def test_modes_cover_original_modes(self):
        for mode in ("standard", "systemic", "stress-test", "adjudication"):
            self.assertIn(mode, protocol.MODES)


class TestOverlay(unittest.TestCase):
    def test_probe_jargon_obfuscation_path(self):
        flag = overlay.probe_jargon(
            "I'm holding space for you",
            evidence_for_obfuscation="phrase appears each time accountability is raised, never followed by a change",
            evidence_for_genuine="")
        self.assertEqual(flag.hypothesis, overlay.H_OBFUSCATION)

    def test_probe_jargon_genuine_path(self):
        flag = overlay.probe_jargon(
            "I feel dysregulated",
            evidence_for_obfuscation="",
            evidence_for_genuine="stated while actively de-escalating and naming a coping step")
        self.assertEqual(flag.hypothesis, overlay.H_GENUINE)

    def test_probe_jargon_both_path(self):
        flag = overlay.probe_jargon(
            "working on myself",
            evidence_for_obfuscation="used to close inquiry twice",
            evidence_for_genuine="attendance records show 18 months of sessions")
        self.assertEqual(flag.hypothesis, overlay.H_BOTH)

    def test_probe_jargon_insufficient_evidence(self):
        flag = overlay.probe_jargon("doing the work", "", "")
        self.assertEqual(flag.hypothesis, overlay.H_INSUFFICIENT)

    def test_supported_obfuscation_gates_tag(self):
        brief = overlay.ProbeBrief(
            field="x", obfuscated_object="the missed deadline",
            obfuscation_support="supported")
        self.assertTrue(brief.supported_obfuscation())
        brief2 = overlay.ProbeBrief(
            field="x", obfuscated_object="the missed deadline",
            obfuscation_support="contested")
        self.assertFalse(brief2.supported_obfuscation())

    def test_handoff_requires_two_to_three_seeds(self):
        brief = overlay.ProbeBrief(field="x", take_seeds=["s1", "s2"])
        self.assertEqual(len(overlay.handoff_seeds(brief)), 2)
        brief_bad = overlay.ProbeBrief(field="x", take_seeds=["only one"])
        with self.assertRaises(overlay.OverlayError):
            overlay.handoff_seeds(brief_bad)


if __name__ == "__main__":
    unittest.main()
