import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pressit import artifact, engine, backends, protocol


def _key(i):
    return protocol.KeyDraft(
        statement=f"Statement {i}", classification="PLAUSIBLE",
        evidence=f"FACT #{i}", confidence="MODERATE",
        vulnerability=f"vulnerability {i}", falsifier=f"falsifier {i}")


def make_artifact(**kw):
    args = dict(
        field="Corner Books revenue question",
        session=1,
        date="2026-09-24",
        depth="one-pass",
        trigger_context="user invocation",
        lifecycle="INITIAL",
        prior_interrogation=None,
        prior_date=None,
        prior_keys=[],
        takes=[
            artifact.Take("A", "Turnaround", "The series built a real customer base."),
            artifact.Take("B", "Blip", "The delta is the estate sale alone."),
        ],
        collisions=[
            artifact.Collision("A/B", "Is regular-stock revenue up or flat?",
                               "A requires conversion of attendees into buyers.",
                               "Item-level sales mix (UNKNOWN)."),
        ],
        keys=[_key(1), _key(2), _key(3)],
        surprise="The turnaround story is the mechanism of the coming harm.",
        synthesis=artifact.Synthesis(
            established_ground="Q3 up 41%; estate sale in July.",
            surviving_model="One-time inventory event, flat base business.",
            remaining_uncertainties="Item-level sales mix; Q4 pipeline.",
            primary_next_target="Obtain item-level Q3 data."),
    )
    args.update(kw)
    return artifact.StateArtifact(**args)


class TestArtifact(unittest.TestCase):
    def test_filename_slug(self):
        a = make_artifact()
        self.assertEqual(a.filename, "interrogation-state-corner-books-revenue-question.md")

    def test_render_contains_all_sections(self):
        md = artifact.render(make_artifact())
        self.assertEqual(artifact.check_sections(md), [])

    def test_render_has_no_placeholders(self):
        md = artifact.render(make_artifact())
        for token in ("TODO", "[TBD]", "???"):
            self.assertNotIn(token, md)

    def test_wrong_collision_pairs_rejected(self):
        with self.assertRaises(artifact.ArtifactError):
            make_artifact(collisions=[
                artifact.Collision("A/C", "x", "y", "z"),
            ])

    def test_three_take_collision_pairs(self):
        a = make_artifact(
            takes=[artifact.Take("A", "t", "a"), artifact.Take("B", "t", "b"),
                   artifact.Take("C", "t", "c")],
            collisions=[artifact.Collision(p, "x", "y", "z")
                        for p in ("A/B", "A/C", "B/C")],
        )
        self.assertEqual([c.pair for c in a.collisions], ["A/B", "A/C", "B/C"])

    def test_load_prior_extracts_keys_and_session(self):
        md = artifact.render(make_artifact(interrogation=2))
        prior = artifact.load_prior(md)
        self.assertEqual(prior["interrogation"], 2)
        self.assertEqual(len(prior["keys"]), 3)

    def test_prior_key_disposition_validated(self):
        with self.assertRaises(artifact.ArtifactError):
            artifact.PriorKeyEvaluation("s", "PROBABLY", "n")

    def test_cracked_key_preserved_in_render(self):
        a = make_artifact(
            interrogation=2, lifecycle="ITERATIVE", prior_interrogation=1,
            prior_keys=[artifact.PriorKeyEvaluation(
                "The owner will not act before January", "CRACKED",
                "The owner signed a sublease in December.")],
        )
        md = artifact.render(a)
        self.assertIn("CRACKED", md)
        self.assertIn("The owner will not act before January", md)

    def test_frontmatter_names(self):
        fm = artifact.render_frontmatter(make_artifact())
        self.assertIn("artifact: interrogation-state", fm)
        self.assertNotIn("ifs-state", fm)


class TestEngine(unittest.TestCase):
    MODEL_JSON = {
        "meta": {"field": "Test field", "status": "INITIAL"},
        "field": {"objective": "o", "scope": "s"},
        "priorState": {"reference": None, "evaluations": []},
        "evidence": {"facts": [], "claims": [], "unknowns": []},
        "probe": {"obfuscatedObject": "x", "apparentFunction": "y",
                  "activeTactics": [], "jargonFlags": []},
        "takes": [
            {"id": "A", "title": "TA", "argument": "arg A"},
            {"id": "B", "title": "TB", "argument": "arg B"},
            {"id": "D", "title": "TD", "argument": "bogus id filtered"},
        ],
        "collisions": [
            {"pair": "A/B", "contradiction": "c", "premiseFailure": "p",
             "discriminator": "d"},
            {"pair": "A/C", "contradiction": "extra", "premiseFailure": "x",
             "discriminator": "y"},
        ],
        "keys": [
            {"statement": f"k{i}", "classification": "PLAUSIBLE", "evidence": "e",
             "confidence": "MODERATE", "vulnerability": "v", "falsifier": "f"}
            for i in range(7)
        ],
        "surprise": "s",
        "synthesis": {"establishedGround": "g", "survivingModel": "m",
                      "remainingUncertainties": "u", "primaryNextTarget": "n"},
    }

    def test_parse_tolerates_fences(self):
        raw = "```json\n" + json.dumps(self.MODEL_JSON) + "\n```"
        parsed = engine.parse_model_json(raw)
        self.assertEqual(parsed["meta"]["field"], "Test field")

    def test_parse_rejects_garbage(self):
        with self.assertRaises(engine.EngineError):
            engine.parse_model_json("no json here at all")

    def test_normalize_enforces_hard_limits(self):
        out = engine.normalize("Test field", overlay=False,
                               prior_session=None, model=self.MODEL_JSON)
        # bogus Take D filtered -> 2 takes -> only A/B survives
        self.assertEqual([t["id"] for t in out["takes"]], ["A", "B"])
        self.assertEqual([c["pair"] for c in out["collisions"]], ["A/B"])
        # 7 keys capped to 5
        self.assertEqual(len(out["keys"]), 5)
        # probe dropped when overlay is off
        self.assertIsNone(out["probe"])
        self.assertEqual(out["meta"]["session"], 1)

    def test_normalize_keeps_probe_when_overlay_on(self):
        out = engine.normalize("Test field", overlay=True,
                               prior_session=None, model=self.MODEL_JSON)
        self.assertIsNotNone(out["probe"])

    def test_normalize_rejects_too_few_keys(self):
        bad = dict(self.MODEL_JSON)
        bad["keys"] = bad["keys"][:2]
        with self.assertRaises(engine.EngineError):
            engine.normalize("f", overlay=False, prior_session=None, model=bad)

    def test_run_end_to_end_with_stub(self):
        backend = backends.StubBackend(self.MODEL_JSON)
        field = protocol.FieldInput(field="Test field")
        result = engine.run(field, backend)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(len(result.artifact["keys"]), 5)

    def test_run_prior_session_increments(self):
        backend = backends.StubBackend(self.MODEL_JSON)
        field = protocol.FieldInput(field="Test field")
        result = engine.run(field, backend, prior_json='{"keys":[]}', prior_session=1)
        self.assertTrue(result.ok, result.error)
        self.assertEqual(result.artifact["meta"]["session"], 2)
        self.assertEqual(result.artifact["meta"]["status"], "INITIAL")

    def test_user_message_includes_overlay_and_prior(self):
        msg = engine.build_user_message("my field", overlay=True, prior_json='{"k":1}')
        self.assertIn("OVERLAY: ON", msg)
        self.assertIn("PRIOR ARTIFACT", msg)
        msg2 = engine.build_user_message("my field", overlay=False, prior_json=None)
        self.assertIn("OVERLAY: OFF", msg2)
        self.assertIn("PRIOR ARTIFACT: none", msg2)

    def test_stub_backend_says_stub(self):
        self.assertEqual(backends.StubBackend({}).name, "stub")


if __name__ == "__main__":
    unittest.main()
