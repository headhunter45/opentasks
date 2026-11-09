"""Tests for configuration loader, resolution, and protected keys."""

import json
import tempfile
import unittest
from pathlib import Path

from ot.config import (
    Config,
    DEFAULT_CONFIG,
    deep_merge,
    find_protected_key_violations,
    load_config,
    load_json_file,
)


class TestConfigLoader(unittest.TestCase):
    def test_load_json_file_missing(self):
        self.assertEqual(load_json_file("/non/existent/path.json"), {})

    def test_load_json_file_valid(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".json") as f:
            f.write(json.dumps({"project": {"name": "Test"}}))
            f.flush()
            data = load_json_file(f.name)
            self.assertEqual(data, {"project": {"name": "Test"}})

    def test_deep_merge(self):
        base = {"a": 1, "nested": {"k1": "v1", "k2": "v2"}}
        override = {"b": 2, "nested": {"k2": "updated", "k3": "v3"}}
        merged = deep_merge(base, override)
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"], 2)
        self.assertEqual(merged["nested"]["k1"], "v1")
        self.assertEqual(merged["nested"]["k2"], "updated")
        self.assertEqual(merged["nested"]["k3"], "v3")

    def test_protected_key_violations(self):
        bad_local = {
            "workItem": {
                "types": {"custom": {"label": "Custom"}},
            },
            "user": {
                "name": "Developer",
            },
        }
        violations = find_protected_key_violations(bad_local)
        self.assertIn("workItem.types", violations)
        self.assertNotIn("user.name", violations)

    def test_config_precedence_and_dot_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            ot_dir = root / ".ot"
            ot_dir.mkdir()

            proj_cfg = {
                "project": {"name": "My Custom Project"},
                "workItem": {"types": {"bug": {"label": "Custom Bug"}}},
            }
            (ot_dir / "config.json").write_text(json.dumps(proj_cfg), encoding="utf-8")

            local_cfg = {
                "user": {"name": "Override User", "editor": "vim"},
            }
            (ot_dir / "config.local.json").write_text(json.dumps(local_cfg), encoding="utf-8")

            cfg = load_config(root)
            self.assertEqual(cfg.get("project.name"), "My Custom Project")
            self.assertEqual(cfg.get("workItem.types.bug.label"), "Custom Bug")
            self.assertEqual(cfg.user_name, "Override User")
            self.assertEqual(cfg.editor, "vim")
            self.assertEqual(cfg.warnings, [])
            self.assertEqual(cfg.tasks_dir, root / ".ot" / "tasks")
            self.assertEqual(cfg.meetings_dir, root / ".ot" / "meetings")
            self.assertEqual(cfg.templates_dir, root / ".ot" / "templates")

    def test_configurable_paths_and_containment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            ot_dir = root / ".ot"
            ot_dir.mkdir()

            proj_cfg = {
                "paths": {
                    "tasks": "docs/tasks",
                    "meetings": "docs/meetings",
                    "templates": "docs/templates",
                }
            }
            (ot_dir / "config.json").write_text(json.dumps(proj_cfg), encoding="utf-8")

            cfg = load_config(root)
            self.assertEqual(cfg.tasks_dir, root / "docs" / "tasks")
            self.assertEqual(cfg.meetings_dir, root / "docs" / "meetings")
            self.assertEqual(cfg.templates_dir, root / "docs" / "templates")
            self.assertTrue(cfg.is_within_project_root("docs/tasks"))
            self.assertFalse(cfg.is_within_project_root("../outside"))
            self.assertFalse(cfg.is_within_project_root("/etc/passwd"))


if __name__ == "__main__":
    unittest.main()
