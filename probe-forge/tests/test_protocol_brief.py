"""Tests for the probe protocol, the brief, and the end-to-end cycle."""

import unittest

from fairit.brief import AuditBrief, BriefError, check_stand_down, parse
from fairit.dialects import detect_markers
from fairit.ground import Correction, GroundMap, HeldTension, PersonState
from fairit.hypotheses import (
    H_BOTH,
    H_GENUINE,
    H_OBFUSCATION,
    INSUFFICIENT_EVIDENCE,
    DiscriminatingEvidence,
    HypothesisRecord,
    Mechanism,
)
from fairit.overlay import (
    ProbeError,
    evidence_tag_for,
    run_jargon_test,
    scan_and_test,
)


def seeds(n=2):
    return [f"seed frame {i + 1}" for i in range(n)]


class TestJargonProtocol(unittest.TestCase):
    def test_obfuscation_wins_with_discriminating_evidence(self):
        flag = run_jargon_test(
            "mistakes were made", "bureaucratic",
            "the passive phrasing appears only in the public statement; internal emails name the decision-maker",
            "",
            mechanisms=[Mechanism("passive-voice dodge", "supported")],
        )
        self.assertEqual(flag.record.verdict, H_OBFUSCATION)

    def test_genuine_wins_with_accountability(self):
        flag = run_jargon_test(
            "holding space", "therapy",
            "",
            "the phrase was followed by a named apology and a changed schedule within 24 hours",
        )
        self.assertEqual(flag.record.verdict, H_GENUINE)

    def test_both_when_evidence_splits(self):
        flag = run_jargon_test(
            "circle back", "corporate",
            "used to end every accountability question without answering it",
            "also used unprompted in low-stakes scheduling with follow-through",
        )
        self.assertEqual(flag.record.verdict, H_BOTH)

    def test_insufficient_when_no_evidence(self):
        flag = run_jargon_test("unpacking", "therapy", "", "")
        self.assertEqual(flag.record.verdict, INSUFFICIENT_EVIDENCE)
        self.assertTrue(flag.record.remaining_questions)

    def test_unknown_dialect_rejected(self):
        with self.assertRaises(ProbeError):
            run_jargon_test("vibes", "astrology", "x", "")


class TestScanAndTest(unittest.TestCase):
    def test_hits_become_tested_flags(self):
        text = "We need to circle back on the missed deadline. Mistakes were made."
        flags = scan_and_test(text, {
            "circle back": ("used to deflect the missed-deadline question", ""),
            "mistakes were made": ("", ""),
        })
        by_phrase = {f.phrase: f for f in flags}
        self.assertEqual(by_phrase["circle back"].record.verdict, H_OBFUSCATION)
        self.assertEqual(by_phrase["mistakes were made"].record.verdict,
                         INSUFFICIENT_EVIDENCE)

    def test_detection_alone_never_convicts(self):
        text = "I'm really doing the work on my boundaries."
        flags = scan_and_test(text, {})
        for flag in flags:
            self.assertEqual(flag.record.verdict, INSUFFICIENT_EVIDENCE)

    def test_detection_alone_never_exonerates(self):
        # Detection without evidence must not produce H-genuine either.
        text = "Let's take this offline and leverage our bandwidth."
        flags = scan_and_test(text, {})
        for flag in flags:
            self.assertNotEqual(flag.record.verdict, H_GENUINE)


class TestEvidenceTagging(unittest.TestCase):
    def _obf_record(self):
        return HypothesisRecord(
            candidate="the passive phrasing dodges the firing decision",
            verdict=H_OBFUSCATION,
            evidence=[DiscriminatingEvidence(
                "passive phrasing only in public, named actors in private",
                H_OBFUSCATION)],
            mechanisms=[Mechanism("passive-voice dodge", "supported")],
        )

    def test_supported_obfuscation_earns_tag(self):
        self.assertEqual(evidence_tag_for(self._obf_record()), "OBFUSCATION")

    def test_genuine_stays_claim(self):
        r = HypothesisRecord(
            candidate="X", verdict=H_GENUINE,
            evidence=[DiscriminatingEvidence("followed by named apology", H_GENUINE)],
        )
        self.assertEqual(evidence_tag_for(r), "CLAIM")

    def test_untested_suspicion_stays_claim(self):
        r = HypothesisRecord(
            candidate="X", verdict=INSUFFICIENT_EVIDENCE,
            remaining_questions=["Did behavior change?"],
        )
        self.assertEqual(evidence_tag_for(r), "CLAIM")


class TestBrief(unittest.TestCase):
    def _brief(self):
        ground = GroundMap(
            tensions=[HeldTension("The memo promised transparency. The names were redacted.")],
            person_states=[PersonState("2026-09-20", "Lee", "defensive in the review")],
            corrections=[Correction("core-claim", "first said no one knew; now says the team knew")],
        )
        record = HypothesisRecord(
            candidate="the redaction dodges responsibility for the delay",
            verdict=H_OBFUSCATION,
            evidence=[DiscriminatingEvidence(
                "redactions cover exactly the decision-makers' names", H_OBFUSCATION)],
            mechanisms=[Mechanism("selective redaction", "supported")],
        )
        return AuditBrief(case_name="memo redactions", ground=ground,
                          records=[record], seeds=seeds())

    def test_render_has_frontmatter(self):
        rendered = self._brief().render()
        self.assertIn("artifact: audit-brief", rendered)
        self.assertIn("protocol: fairit/1.0", rendered)
        self.assertIn("## Handoff seeds", rendered)

    def test_parse_round_trip(self):
        brief = self._brief()
        parsed = parse(brief.render())
        self.assertEqual(parsed.case_name, "memo redactions")
        self.assertEqual(len(parsed.seeds), 2)

    def test_seed_count_enforced(self):
        with self.assertRaises(BriefError):
            AuditBrief(case_name="x", seeds=["only one"])
        with self.assertRaises(BriefError):
            AuditBrief(case_name="x", seeds=seeds(4))

    def test_stand_down_rejects_collision_section(self):
        with self.assertRaises(BriefError):
            check_stand_down("# Report\n\n## Collision analysis\n\nstuff")
        with self.assertRaises(BriefError):
            check_stand_down("# Report\n\n### Surprise extraction\n\nstuff")

    def test_stand_down_rejects_adjudication(self):
        brief_text = self._brief().render() + "\n## Adjudication\n\nverdict here"
        with self.assertRaises(BriefError):
            check_stand_down(brief_text)

    def test_obfuscation_supported_true(self):
        self.assertTrue(self._brief().obfuscation_supported())

    def test_not_an_audit_brief_rejected(self):
        with self.assertRaises(BriefError):
            parse("---\nartifact: something-else\n---\n# Audit brief: x\n## Handoff seeds\n1. s\n2. s")


class TestEndToEnd(unittest.TestCase):
    """Ground -> probe -> tag -> brief, the full overlay cycle."""

    def test_full_cycle(self):
        # 1. Ground mapping.
        ground = GroundMap(
            tensions=[HeldTension(
                "The vendor promised delivery Friday. Nothing arrived by Monday.")],
            person_states=[PersonState("2026-09-19", "vendor rep", "assuring")],
        )
        # 2. Probe the shield vocabulary.
        flags = scan_and_test(
            "We're going to circle back and leverage learnings going forward.",
            {
                "circle back": ("used to end the delivery-failure call without a new date", ""),
                "going forward": ("", "used in routine status updates with dates attached"),
            },
        )
        # 3. Tag each tested record.
        tags = [evidence_tag_for(f.record) for f in flags]
        self.assertIn("OBFUSCATION", tags)
        self.assertIn("CLAIM", tags)  # 'going forward' untested -> stays CLAIM
        # 4. Brief renders and parses.
        brief = AuditBrief(
            case_name="vendor delivery failure",
            ground=ground,
            records=[f.record for f in flags],
            seeds=["The vendor is managing the relationship, not the delivery.",
                   "The missed date is being reframed as process improvement."],
        )
        rendered = brief.render()
        parsed = parse(rendered)
        self.assertEqual(parsed.case_name, "vendor delivery failure")
        self.assertTrue(brief.obfuscation_supported())
        # 5. Stand-down: nothing engine-owned in the output.
        for word in ("collision", "adjudicat", "surprise"):
            self.assertNotIn(word, rendered.lower())


if __name__ == "__main__":
    unittest.main()
