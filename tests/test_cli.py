"""Tests for CLI commands (task list, show, create, edit, comment, dependencies)."""

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ot.cli import main


class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Copy sample project into temporary directory for isolated mutations
        sample_src = Path(__file__).resolve().parent.parent / "examples" / "sample-project"
        shutil.copytree(sample_src, self.root, dirs_exist_ok=True)


    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cli_task_list(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "list"])
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("Release Alpha", out)
        self.assertIn("Implement User Authentication", out)

    def test_cli_task_list_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "list", "--json"])
        self.assertEqual(ret, 0)
        data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)

    def test_cli_task_show(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "show", "Release Alpha"])
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("ID:", out)
        self.assertIn("Title:       Release Alpha", out)
        self.assertIn("Type:        epic", out)
        self.assertIn("Children:", out)

    def test_cli_task_create(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main([
                "-C",
                str(self.root),
                "task",
                "create",
                "--title",
                "New Test Feature",
                "--type",
                "feature",
                "--status",
                "planned",
                "--overview",
                "Testing CLI create",
                "--no-edit",
            ])
        self.assertEqual(ret, 0)
        self.assertIn("Created WorkItem", buf.getvalue())

        # Verify it now appears in list
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            main(["-C", str(self.root), "task", "list"])
        self.assertIn("New Test Feature", buf2.getvalue())

    def test_cli_task_create_positional_title(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "create", "Fix Something"])
        self.assertEqual(ret, 0)
        self.assertIn("Created WorkItem", buf.getvalue())
        self.assertIn("Fix Something", buf.getvalue())

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            main(["-C", str(self.root), "task", "show", "Fix Something"])
        self.assertIn("Title:       Fix Something", buf2.getvalue())

    def test_cli_task_status(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "status", "Setup Continuous Integration Pipeline", "completed"])
        self.assertEqual(ret, 0)
        self.assertIn("Updated status", buf.getvalue())

    def test_cli_task_update(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main([
                "-C",
                str(self.root),
                "task",
                "update",
                "Setup Continuous Integration Pipeline",
                "--title",
                "Setup CI/CD Pipeline",
                "--status",
                "in_progress",
                "--size",
                "large",
                "--tag",
                "ci,devops",
                "--overview",
                "Updated CI overview.",
            ])
        self.assertEqual(ret, 0)
        self.assertIn("Updated WorkItem", buf.getvalue())

        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            main(["-C", str(self.root), "task", "show", "Setup CI/CD Pipeline"])
        out = buf2.getvalue()
        self.assertIn("Title:       Setup CI/CD Pipeline", out)
        self.assertIn("Status:      in_progress", out)
        self.assertIn("Size:        large", out)
        self.assertIn("Updated CI overview.", out)

    def test_cli_task_comment(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "comment", "Release Alpha", "LGTM for alpha launch!"])
        self.assertEqual(ret, 0)
        self.assertIn("Added comment to", buf.getvalue())

    def test_cli_dependencies_flow(self):
        # Add dependency
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main([
                "-C",
                str(self.root),
                "task",
                "add-dependency",
                "Setup Continuous Integration Pipeline",
                "Fix Login Crash on Null Password",
            ])
        self.assertEqual(ret, 0)
        self.assertIn("Added dependency", buf.getvalue())

        # Get dependencies
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            ret2 = main(["-C", str(self.root), "task", "get-dependencies", "Setup Continuous Integration Pipeline"])
        self.assertEqual(ret2, 0)
        self.assertIn("Fix Login Crash", buf2.getvalue())

        # Remove dependency
        buf3 = io.StringIO()
        with redirect_stdout(buf3):
            ret3 = main([
                "-C",
                str(self.root),
                "task",
                "remove-dependency",
                "Setup Continuous Integration Pipeline",
                "Fix Login Crash on Null Password",
            ])
        self.assertEqual(ret3, 0)
        self.assertIn("Removed dependency", buf3.getvalue())


if __name__ == "__main__":
    unittest.main()
