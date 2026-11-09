"""Tests for project and VCS discovery."""

import os
import tempfile
import unittest
from pathlib import Path

from ot.discovery import find_project_root, find_vcs_root, discover_root


class TestProjectDiscovery(unittest.TestCase):
    def test_find_project_root_in_nested_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            ot_dir = root / ".ot"
            ot_dir.mkdir()
            nested = root / "src" / "deeply" / "nested" / "folder"
            nested.mkdir(parents=True)

            found = find_project_root(nested)
            self.assertEqual(found, root)

    def test_find_project_root_from_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".ot").mkdir()
            test_file = root / "subdir" / "file.txt"
            test_file.parent.mkdir()
            test_file.touch()

            found = find_project_root(test_file)
            self.assertEqual(found, root)

    def test_find_project_root_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            found = find_project_root(root)
            self.assertIsNone(found)

    def test_environment_variable_override(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".ot").mkdir()
            other = root / "other"
            other.mkdir()

            old_env = os.environ.get("OPEN_TASKS_ROOT")
            try:
                os.environ["OPEN_TASKS_ROOT"] = str(root)
                found = find_project_root(other)
                self.assertEqual(found, root)
            finally:
                if old_env is not None:
                    os.environ["OPEN_TASKS_ROOT"] = old_env
                else:
                    os.environ.pop("OPEN_TASKS_ROOT", None)

    def test_git_discovery(self):
        from ot.discovery import is_git_available, get_git_identity, find_vcs_root
        vcs_type, vcs_path = find_vcs_root(Path.cwd())
        self.assertEqual(vcs_type, "git")
        self.assertIsNotNone(vcs_path)

        if is_git_available():
            name, email = get_git_identity(Path.cwd())
            # In git repository, name and email should be queryable
            self.assertTrue(name is None or isinstance(name, str))

    def test_no_vcs_fallback(self):
        from ot.discovery import get_system_identity, get_system_editor
        name, email = get_system_identity()
        self.assertIsNotNone(name)
        editor = get_system_editor()
        self.assertIsNotNone(editor)

    def test_hg_discovery_and_identity_resolution(self):
        from ot.config import load_config
        from ot.discovery import (
            find_vcs_root,
            get_hg_editor,
            get_hg_identity,
            parse_hg_username,
        )

        self.assertEqual(
            parse_hg_username("Grace Hopper <grace@navy.mil>"),
            ("Grace Hopper", "grace@navy.mil"),
        )
        self.assertEqual(parse_hg_username("Grace Hopper"), ("Grace Hopper", None))

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / ".ot").mkdir()
            hg_dir = root / ".hg"
            hg_dir.mkdir()
            (hg_dir / "hgrc").write_text(
                "[ui]\nusername = Ada Lovelace <ada@analytical.engine>\neditor = emacs\n",
                encoding="utf-8",
            )

            vcs_type, vcs_root = find_vcs_root(root)
            self.assertEqual(vcs_type, "hg")
            self.assertEqual(vcs_root, root)

            name, email = get_hg_identity(root)
            self.assertEqual(name, "Ada Lovelace")
            self.assertEqual(email, "ada@analytical.engine")
            self.assertEqual(get_hg_editor(root), "emacs")

            cfg = load_config(root)
            self.assertEqual(cfg.user_name, "Ada Lovelace")
            self.assertEqual(cfg.user_email, "ada@analytical.engine")
            self.assertEqual(cfg.editor, "emacs")
            self.assertEqual(cfg.get_origin("user.name"), "vcs (hg)")
            self.assertEqual(cfg.get_origin("user.editor"), "vcs (hg)")




if __name__ == "__main__":
    unittest.main()
