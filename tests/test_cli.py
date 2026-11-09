"""Tests for CLI commands (task list, show, create, edit, comment, dependencies)."""

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
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

    def test_cli_task_list_multi_column_and_prefix_filtering(self):
        # Sample project has:
        # - Release Alpha: epic, in_progress
        # - Implement User Authentication: feature, in_progress
        # - Fix Login Crash on Null Password: bug, triage
        # - Setup Continuous Integration Pipeline: chore, planned

        # Repeated flags: -s triage -s in_progress -s planned (OR within status)
        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            ret = main(["-C", str(self.root), "task", "list", "-s", "triage", "-s", "in_progress", "-s", "planned", "--json"])
        self.assertEqual(ret, 0)
        data1 = json.loads(buf1.getvalue())
        self.assertEqual(len(data1), 4)

        # Comma-separated flags: -s triage,in_progress,planned
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            ret = main(["-C", str(self.root), "task", "list", "-s", "triage,in_progress,planned", "--json"])
        self.assertEqual(ret, 0)
        data2 = json.loads(buf2.getvalue())
        self.assertEqual(len(data2), 4)

        # AND across columns, OR within column: -s triage,planned -t bug,chore
        buf3 = io.StringIO()
        with redirect_stdout(buf3):
            ret = main(["-C", str(self.root), "task", "list", "-s", "triage,planned", "-t", "bug,chore", "--json"])
        self.assertEqual(ret, 0)
        data3 = json.loads(buf3.getvalue())
        titles3 = {item["title"] for item in data3}
        self.assertEqual(titles3, {"Fix Login Crash on Null Password", "Setup Continuous Integration Pipeline"})

        # Prefix matching from start of column value: -s tr,in matches triage and in_progress, not planned
        buf4 = io.StringIO()
        with redirect_stdout(buf4):
            ret = main(["-C", str(self.root), "task", "list", "-s", "tr,in", "--json"])
        self.assertEqual(ret, 0)
        data4 = json.loads(buf4.getvalue())
        titles4 = {item["title"] for item in data4}
        self.assertEqual(
            titles4,
            {"Release Alpha", "Implement User Authentication", "Fix Login Crash on Null Password"},
        )

        # WorkItemIndex.filter directly verifies prefix-from-start ('lan' does not match 'planned')
        from ot.scanner import load_index
        idx = load_index(self.root)
        filtered = idx.filter(status="tr,lan,in")
        self.assertEqual(
            {it.title for it in filtered},
            {"Release Alpha", "Implement User Authentication", "Fix Login Crash on Null Password"},
        )

    def test_cli_task_list_frontmatter_filters_and_validation(self):
        # --id and --title prefix matching
        buf_all = io.StringIO()
        with redirect_stdout(buf_all):
            main(["-C", str(self.root), "task", "list", "--json"])
        all_items = json.loads(buf_all.getvalue())
        first_short = all_items[0]["short_id"]

        buf_id = io.StringIO()
        with redirect_stdout(buf_id):
            ret = main(["-C", str(self.root), "task", "list", "--id", first_short[:4], "--json"])
        self.assertEqual(ret, 0)
        id_items = json.loads(buf_id.getvalue())
        self.assertEqual(len(id_items), 1)
        self.assertEqual(id_items[0]["short_id"], first_short)

        buf_title = io.StringIO()
        with redirect_stdout(buf_title):
            ret = main(["-C", str(self.root), "task", "list", "--title", "Release,Fix Login", "--json"])
        self.assertEqual(ret, 0)
        title_items = json.loads(buf_title.getvalue())
        self.assertEqual(
            {it["title"] for it in title_items},
            {"Release Alpha", "Fix Login Crash on Null Password"},
        )

        # Invalid --type prints allowed types and returns non-zero
        err_type = io.StringIO()
        with redirect_stderr(err_type):
            ret = main(["-C", str(self.root), "task", "list", "-t", "nonexistent"])
        self.assertEqual(ret, 1)
        self.assertIn("Allowed types:", err_type.getvalue())

        # Invalid --status (including middle substring like 'lan') prints allowed statuses and returns non-zero
        err_status = io.StringIO()
        with redirect_stderr(err_status):
            ret = main(["-C", str(self.root), "task", "list", "-s", "tr,lan,in"])
        self.assertEqual(ret, 1)
        self.assertIn("Allowed statuses:", err_status.getvalue())

        # --author substring and /regex/ matching against name and email
        buf_auth_sub = io.StringIO()
        with redirect_stdout(buf_auth_sub):
            ret = main(["-C", str(self.root), "task", "list", "--author", "example.com", "--json"])
        self.assertEqual(ret, 0)
        self.assertGreater(len(json.loads(buf_auth_sub.getvalue())), 0)

        buf_auth_re = io.StringIO()
        with redirect_stdout(buf_auth_re):
            ret = main(["-C", str(self.root), "task", "list", "--author", "/@example\\.com$/", "--json"])
        self.assertEqual(ret, 0)
        self.assertGreater(len(json.loads(buf_auth_re.getvalue())), 0)

        buf_auth_nomatch = io.StringIO()
        with redirect_stdout(buf_auth_nomatch):
            ret = main(["-C", str(self.root), "task", "list", "--author", "/^nobody@nowhere\\.org$/", "--json"])
        self.assertEqual(ret, 0)
        self.assertEqual(len(json.loads(buf_auth_nomatch.getvalue())), 0)

    def test_cli_task_list_width(self):
        import os

        # Explicit --width 80 sets divider length to 80
        buf80 = io.StringIO()
        with redirect_stdout(buf80):
            ret = main(["-C", str(self.root), "task", "list", "--width", "80"])
        self.assertEqual(ret, 0)
        lines80 = buf80.getvalue().splitlines()
        self.assertEqual(len(lines80[1]), 80)

        # Explicit --width 140 sets divider length to 140
        buf140 = io.StringIO()
        with redirect_stdout(buf140):
            ret = main(["-C", str(self.root), "--width", "140", "task", "list"])
        self.assertEqual(ret, 0)
        lines140 = buf140.getvalue().splitlines()
        self.assertEqual(len(lines140[1]), 140)

        # Terminal width < 120 via COLUMNS defaults to 80; >= 120 uses full width
        old_cols = os.environ.get("COLUMNS")
        try:
            os.environ["COLUMNS"] = "100"
            buf_narrow = io.StringIO()
            with redirect_stdout(buf_narrow):
                main(["-C", str(self.root), "task", "list"])
            self.assertEqual(len(buf_narrow.getvalue().splitlines()[1]), 80)

            os.environ["COLUMNS"] = "150"
            buf_wide = io.StringIO()
            with redirect_stdout(buf_wide):
                main(["-C", str(self.root), "task", "list"])
            self.assertEqual(len(buf_wide.getvalue().splitlines()[1]), 150)
        finally:
            if old_cols is None:
                os.environ.pop("COLUMNS", None)
            else:
                os.environ["COLUMNS"] = old_cols

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
