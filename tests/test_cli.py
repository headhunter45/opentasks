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

    def test_cli_task_list_positional_ids(self):
        buf_all = io.StringIO()
        with redirect_stdout(buf_all):
            main(["-C", str(self.root), "task", "list", "--json"])
        all_items = json.loads(buf_all.getvalue())
        id1 = all_items[0]["short_id"]
        id2 = all_items[1]["short_id"]

        # Space-separated positional IDs
        buf_space = io.StringIO()
        with redirect_stdout(buf_space):
            ret = main(["-C", str(self.root), "task", "list", id1, id2, "--json"])
        self.assertEqual(ret, 0)
        self.assertEqual({it["short_id"] for it in json.loads(buf_space.getvalue())}, {id1, id2})

        # Comma-separated positional IDs
        buf_comma = io.StringIO()
        with redirect_stdout(buf_comma):
            ret = main(["-C", str(self.root), "task", "list", f"{id1},{id2}", "--json"])
        self.assertEqual(ret, 0)
        self.assertEqual({it["short_id"] for it in json.loads(buf_comma.getvalue())}, {id1, id2})

        # Mix of matched and unmatched IDs in table mode: prints matched rows, errors on stderr, returns 1
        out_tbl = io.StringIO()
        err_tbl = io.StringIO()
        with redirect_stdout(out_tbl), redirect_stderr(err_tbl):
            ret = main(["-C", str(self.root), "task", "list", f"{id1},deadbeef"])
        self.assertEqual(ret, 1)
        self.assertIn(id1, out_tbl.getvalue())
        self.assertIn("deadbeef", err_tbl.getvalue())

        # Mix of matched and unmatched IDs in --json mode: includes {"id": "deadbeef", "exists": false}, returns 1
        out_json = io.StringIO()
        with redirect_stdout(out_json):
            ret = main(["-C", str(self.root), "task", "list", id1, "deadbeef", "--json"])
        self.assertEqual(ret, 1)
        data = json.loads(out_json.getvalue())
        self.assertEqual(len(data), 2)
        self.assertIn({"id": "deadbeef", "exists": False}, data)

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

    def test_cli_task_edit_and_create_validation(self):
        import re
        import sys

        local_cfg = self.root / ".ot" / "config.local.json"
        try:
            # 1. Valid edit in ot task edit updates canonical file
            editor_script_valid = self.root / "editor_valid.py"
            editor_script_valid.write_text(
                "import sys, pathlib\n"
                "p = pathlib.Path(sys.argv[1])\n"
                "text = p.read_text()\n"
                "p.write_text(text.replace('status: planned', 'status: in_progress'))\n",
                encoding="utf-8",
            )
            local_cfg.write_text(
                json.dumps({"user": {"editor": f"{sys.executable} {editor_script_valid}"}}),
                encoding="utf-8",
            )

            out_ok = io.StringIO()
            err_ok = io.StringIO()
            with redirect_stdout(out_ok), redirect_stderr(err_ok):
                ret = main(["-C", str(self.root), "task", "edit", "Setup Continuous Integration Pipeline"])
            self.assertEqual(ret, 0)
            self.assertIn("Updated WorkItem", out_ok.getvalue())

            # 2. Invalid edit in ot task edit fails, preserves temp file, leaves canonical file untouched
            editor_script_invalid = self.root / "editor_invalid.py"
            editor_script_invalid.write_text(
                "import sys, pathlib\n"
                "p = pathlib.Path(sys.argv[1])\n"
                "text = p.read_text()\n"
                "p.write_text(text.replace('status: in_progress', 'status: invalid_status_xyz'))\n",
                encoding="utf-8",
            )
            local_cfg.write_text(
                json.dumps({"user": {"editor": f"{sys.executable} {editor_script_invalid}"}}),
                encoding="utf-8",
            )

            out_err = io.StringIO()
            err_err = io.StringIO()
            with redirect_stdout(out_err), redirect_stderr(err_err):
                ret_err = main(["-C", str(self.root), "task", "edit", "Setup Continuous Integration Pipeline"])
            self.assertEqual(ret_err, 1)
            err_text = err_err.getvalue()
            self.assertIn("Invalid status 'invalid_status_xyz'", err_text)
            self.assertIn("Edited content preserved at:", err_text)
            m = re.search(r"Edited content preserved at:\s*(.+)", err_text)
            self.assertIsNotNone(m)
            preserved_path = Path(m.group(1).strip())
            self.assertTrue(preserved_path.exists())
            preserved_path.unlink(missing_ok=True)

            # Verify canonical task still has status: in_progress
            show_buf = io.StringIO()
            with redirect_stdout(show_buf):
                main(["-C", str(self.root), "task", "show", "Setup Continuous Integration Pipeline"])
            self.assertIn("Status:      in_progress", show_buf.getvalue())

            # 3. Invalid edit in ot task create --edit fails and preserves temp file
            editor_script_create_invalid = self.root / "editor_create_invalid.py"
            editor_script_create_invalid.write_text(
                "import sys, pathlib\n"
                "p = pathlib.Path(sys.argv[1])\n"
                "text = p.read_text()\n"
                "p.write_text(text.replace('type: task', 'type: bogus_type'))\n",
                encoding="utf-8",
            )
            local_cfg.write_text(
                json.dumps({"user": {"editor": f"{sys.executable} {editor_script_create_invalid}"}}),
                encoding="utf-8",
            )

            out_c = io.StringIO()
            err_c = io.StringIO()
            with redirect_stdout(out_c), redirect_stderr(err_c):
                ret_c = main(["-C", str(self.root), "task", "create", "--title", "Bad Edit Task", "--edit"])
            self.assertEqual(ret_c, 1)
            err_c_text = err_c.getvalue()
            self.assertIn("Invalid type 'bogus_type'", err_c_text)
            self.assertIn("Edited content preserved at:", err_c_text)
            m2 = re.search(r"Edited content preserved at:\s*(.+)", err_c_text)
            self.assertIsNotNone(m2)
            Path(m2.group(1).strip()).unlink(missing_ok=True)
        finally:
            local_cfg.unlink(missing_ok=True)
            for f in ("editor_valid.py", "editor_invalid.py", "editor_create_invalid.py"):
                (self.root / f).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
