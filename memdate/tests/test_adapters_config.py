"""Tests for storage adapters, config, and frontmatter."""

import json
import os
import tempfile
import unittest

from memdate import frontmatter as fm
from memdate.adapters import (
    DriveNotConfigured,
    GoogleDriveAdapter,
    LocalFilesystemAdapter,
    StorageError,
    default_adapter,
)
from memdate.config import ConfigError, MemoryConfig


class LocalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LocalFilesystemAdapter(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_read_round_trip(self):
        self.assertIsNone(self.store.read("a/b.txt"))
        self.store.write("a/b.txt", "hello")
        self.assertEqual(self.store.read("a/b.txt"), "hello")
        self.assertTrue(self.store.exists("a/b.txt"))

    def test_append_creates_and_extends(self):
        self.store.append("log.md", "one\n")
        self.store.append("log.md", "two\n")
        self.assertEqual(self.store.read("log.md"), "one\ntwo\n")

    def test_move(self):
        self.store.write("src/f.txt", "data")
        self.store.move("src/f.txt", "dst/nested/f.txt")
        self.assertFalse(self.store.exists("src/f.txt"))
        self.assertEqual(self.store.read("dst/nested/f.txt"), "data")

    def test_list_files(self):
        self.store.write("d/b.txt", "x")
        self.store.write("d/a.txt", "x")
        self.store.makedirs("d/sub")
        self.assertEqual(self.store.list_files("d"), ["a.txt", "b.txt"])
        self.assertEqual(self.store.list_files("missing"), [])

    def test_digest_stable(self):
        self.store.write("f.txt", "abc")
        d1 = self.store.digest("f.txt")
        self.store.append("f.txt", "d")
        self.assertNotEqual(d1, self.store.digest("f.txt"))
        self.assertEqual(len(d1), 64)

    def test_path_escape_rejected(self):
        with self.assertRaises(StorageError):
            self.store.write("../evil.txt", "x")
        with self.assertRaises(StorageError):
            self.store.read("../../etc/passwd")

    def test_default_adapter_is_local(self):
        adapter = default_adapter(self.tmp.name)
        self.assertIsInstance(adapter, LocalFilesystemAdapter)


class DriveSeamTests(unittest.TestCase):
    def test_every_method_raises_loudly(self):
        drive = GoogleDriveAdapter()
        with self.assertRaises(DriveNotConfigured) as ctx:
            drive.read("x")
        self.assertIn("seam, not an implementation", str(ctx.exception))
        for method, args in [
            ("write", ("x", "y")), ("append", ("x", "y")),
            ("exists", ("x",)), ("makedirs", ("x",)),
            ("move", ("x", "y")), ("list_files", ("x",)),
            ("digest", ("x",)),
        ]:
            with self.assertRaises(DriveNotConfigured, msg=method):
                getattr(drive, method)(*args)


class ConfigTests(unittest.TestCase):
    def test_defaults_are_neutral(self):
        cfg = MemoryConfig(root="/tmp/mem")
        self.assertEqual(cfg.domains,
                         ("personal", "work", "projects", "reference", "misc"))
        for ryan_only in ("fhk", "tribunal", "memory-system"):
            self.assertNotIn(ryan_only, cfg.domains)

    def test_blank_root_rejected(self):
        with self.assertRaises(ConfigError):
            MemoryConfig(root="")

    def test_bad_domain_names_rejected(self):
        for bad in ["a/b", "..", "  ", "a\\b"]:
            with self.assertRaises(ConfigError, msg=bad):
                MemoryConfig(root="/tmp/mem", domains=("ok", bad))

    def test_duplicate_domains_rejected(self):
        with self.assertRaises(ConfigError):
            MemoryConfig(root="/tmp/mem", domains=("Work", "work"))

    def test_require_domain_case_insensitive(self):
        cfg = MemoryConfig(root="/tmp/mem", domains=("Work",))
        self.assertEqual(cfg.require_domain("WORK"), "Work")
        with self.assertRaises(ConfigError):
            cfg.require_domain("fhk")

    def test_from_dict(self):
        cfg = MemoryConfig.from_dict({"root": "/tmp/m",
                                      "domains": ["garden", "car"]})
        self.assertEqual(cfg.domains, ("garden", "car"))

    def test_from_dict_needs_root(self):
        with self.assertRaises(ConfigError):
            MemoryConfig.from_dict({"domains": ["a"]})

    def test_from_json(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as f:
            json.dump({"root": "/tmp/m", "domains": ["a", "b"]}, f)
            path = f.name
        try:
            cfg = MemoryConfig.from_json(path)
            self.assertEqual(cfg.domains, ("a", "b"))
        finally:
            os.unlink(path)

    def test_from_yaml_subset(self):
        text = (
            "# memory config\n"
            "root: /tmp/m\n"
            "domains:\n"
            "  - garden\n"
            "  - 'car'\n"
            'interpretation_markers:\n'
            '  - "in summary"\n'
        )
        with tempfile.NamedTemporaryFile("w", suffix=".yaml",
                                         delete=False) as f:
            f.write(text)
            path = f.name
        try:
            cfg = MemoryConfig.from_yaml(path)
            self.assertEqual(cfg.root, "/tmp/m")
            self.assertEqual(cfg.domains, ("garden", "car"))
            self.assertEqual(cfg.interpretation_markers, ("in summary",))
        finally:
            os.unlink(path)

    def test_from_yaml_rejects_unsupported(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml",
                                         delete=False) as f:
            f.write("root: /tmp/m\n  indented: junk\n")
            path = f.name
        try:
            with self.assertRaises(ConfigError):
                MemoryConfig.from_yaml(path)
        finally:
            os.unlink(path)


class FrontmatterTests(unittest.TestCase):
    def test_render_split_round_trip(self):
        fields = {
            "artifact": "memdate-distilled",
            "domain": "work",
            "entities": ["Acme", "Priya"],
            "entity_notes": {"Acme": "client"},
            "open_questions": [],
        }
        text = fm.render(fields) + "Body here.\n"
        back, body = fm.split(text)
        self.assertEqual(back["artifact"], "memdate-distilled")
        self.assertEqual(back["entities"], ["Acme", "Priya"])
        self.assertEqual(back["entity_notes"], {"Acme": "client"})
        self.assertEqual(back["open_questions"], [])
        self.assertEqual(body.strip(), "Body here.")

    def test_missing_frontmatter_raises(self):
        with self.assertRaises(fm.FrontmatterError):
            fm.split("No frontmatter here.\n")

    def test_unclosed_frontmatter_raises(self):
        with self.assertRaises(fm.FrontmatterError):
            fm.split("---\nkey: value\n")

    def test_require_flags_missing_keys(self):
        with self.assertRaises(fm.FrontmatterError):
            fm.require({"a": 1}, "a", "b", what="test doc")


if __name__ == "__main__":
    unittest.main()
