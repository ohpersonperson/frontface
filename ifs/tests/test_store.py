import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Isolate the ledger: test runs must not touch the user's real ledger.
os.environ["FRONTFACE_LEDGER_DIR"] = tempfile.mkdtemp(prefix="pressit-store-test-")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pressit import artifact, protocol


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


class TestStore(unittest.TestCase):
    def test_store_writes_layout(self):
        a = make_artifact()
        with tempfile.TemporaryDirectory() as store:
            addr = artifact.save_artifact(a, store)
            expect = os.path.join(store, "2026-09-24",
                                  "corner-books-revenue-question", "artifact.md")
            self.assertEqual(addr, expect)
            self.assertTrue(os.path.isfile(expect))
            meta_path = os.path.join(store, "2026-09-24",
                                     "corner-books-revenue-question", "meta.json")
            self.assertTrue(os.path.isfile(meta_path))

    def test_stored_markdown_matches_render(self):
        a = make_artifact()
        with tempfile.TemporaryDirectory() as store:
            addr = artifact.save_artifact(a, store)
            with open(addr, encoding="utf-8") as f:
                on_disk = f.read()
            self.assertEqual(on_disk, artifact.render(a))

    def test_meta_json_content(self):
        a = make_artifact()
        with tempfile.TemporaryDirectory() as store:
            addr = artifact.save_artifact(a, store)
            meta_path = os.path.join(os.path.dirname(addr), "meta.json")
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
            self.assertEqual(meta["field"], "Corner Books revenue question")
            self.assertEqual(meta["slug"], "corner-books-revenue-question")
            self.assertEqual(meta["date"], "2026-09-24")
            self.assertEqual(meta["session"], 1)
            self.assertEqual(meta["interrogation"], 1)
            self.assertEqual(meta["depth"], "one-pass")
            self.assertEqual(meta["lifecycle"], "INITIAL")
            self.assertEqual(meta["filename"],
                             "interrogation-state-corner-books-revenue-question.md")
            self.assertEqual(
                meta["sha256"],
                hashlib.sha256(artifact.render(a).encode("utf-8")).hexdigest())

    def test_layout_matches_demo(self):
        # The conv demo's example: field "why do we dream" on 2026-10-12
        # lands at <store_dir>/2026-10-12/why-do-we-dream/artifact.md.
        a = make_artifact(field="why do we dream", date="2026-10-12")
        with tempfile.TemporaryDirectory() as store:
            addr = artifact.save_artifact(a, store)
            self.assertEqual(addr, os.path.join(
                store, "2026-10-12", "why-do-we-dream", "artifact.md"))
            self.assertTrue(os.path.isfile(addr))

    def test_store_creates_nested_dirs(self):
        a = make_artifact()
        with tempfile.TemporaryDirectory() as tmp:
            store = os.path.join(tmp, "nested", "my-runs")
            addr = artifact.save_artifact(a, store)
            self.assertTrue(os.path.isfile(addr))

    def test_store_overwrites_same_slot(self):
        a = make_artifact()
        with tempfile.TemporaryDirectory() as store:
            addr1 = artifact.save_artifact(a, store)
            addr2 = artifact.save_artifact(a, store)
            self.assertEqual(addr1, addr2)
            self.assertTrue(os.path.isfile(addr1))

    def test_no_store_dir_writes_nothing(self):
        # The default path must be byte-identical to render() and must
        # not touch the filesystem anywhere: run with cwd in an empty
        # temp dir and prove the dir stays empty.
        a = make_artifact()
        with tempfile.TemporaryDirectory() as sandbox:
            old = os.getcwd()
            os.chdir(sandbox)
            try:
                out = artifact.save_artifact(a)
            finally:
                os.chdir(old)
            self.assertEqual(out, artifact.render(a))
            self.assertEqual(os.listdir(sandbox), [])

    def test_package_export(self):
        import pressit
        self.assertIs(pressit.save_artifact, artifact.save_artifact)
        self.assertIs(pressit.artifact_meta, artifact.artifact_meta)


if __name__ == "__main__":
    unittest.main()
