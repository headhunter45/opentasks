"""Tests for validation, error reporting, and repair framework."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ot.cli import main
from ot.validation import Diagnostic, Repairer, Severity, Validator


class TestValidationAndRepair(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        sample_src = Path(__file__).resolve().parent.parent / "examples" / "sample-project"
        shutil.copytree(sample_src, self.root, dirs_exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sample_project_clean_validation(self):
        # Create templates & meetings dirs so project is fully clean
        (self.root / ".ot" / "templates").mkdir(exist_ok=True)
        (self.root / ".ot" / "meetings").mkdir(exist_ok=True)

        validator = Validator(self.root)
        diags = validator.validate_all()
        errors = [d for d in diags if d.severity == Severity.ERROR]
        self.assertEqual(len(errors), 0)

    def test_missing_directory_detection_and_repair(self):
        # Remove templates and meetings if present
        shutil.rmtree(self.root / ".ot" / "templates", ignore_errors=True)
        shutil.rmtree(self.root / ".ot" / "meetings", ignore_errors=True)

        validator = Validator(self.root)
        diags = validator.validate_all()
        missing_dirs = [d for d in diags if d.category == "filesystem" and d.is_fixable]
        self.assertGreaterEqual(len(missing_dirs), 1)

        # Repair missing directories
        repairer = Repairer(self.root)
        repairs = repairer.repair()
        self.assertTrue(any("templates" in r for r in repairs))
        self.assertTrue((self.root / ".ot" / "templates").is_dir())


    def test_protected_key_misplacement_detection_and_repair(self):
        # Put protected key alongside an unprotected sibling key in config.local.json
        local_cfg = self.root / ".ot" / "config.local.json"
        local_cfg.write_text(
            json.dumps(
                {
                    "workItem": {
                        "types": {"custom": {"label": "Custom"}},
                        "customUnprotectedSetting": True,
                    },
                    "project": {
                        "name": "Local Project Override",
                    },
                }
            ),
            encoding="utf-8",
        )

        validator = Validator(self.root)
        diags = validator.validate_all()
        warnings = [d for d in diags if d.category == "config" and d.is_fixable]
        self.assertGreaterEqual(len(warnings), 1)

        # Run repair
        repairer = Repairer(self.root)
        repairs = repairer.repair()
        self.assertTrue(any("config.local.json" in r for r in repairs))

        # Check that protected keys were deep-merged into config.json
        proj_cfg_data = json.loads((self.root / ".ot" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(proj_cfg_data["workItem"]["types"]["custom"]["label"], "Custom")
        self.assertEqual(proj_cfg_data["project"]["name"], "Local Project Override")

        # Check that unprotected sibling under workItem was preserved and empty 'project' dict was pruned
        local_cfg_data = json.loads(local_cfg.read_text(encoding="utf-8"))
        self.assertEqual(local_cfg_data.get("workItem"), {"customUnprotectedSetting": True})
        self.assertNotIn("project", local_cfg_data)

    def test_global_config_and_cross_layer_schema_validation(self):
        import os

        old_home = os.environ.get("OT_USER_HOME")
        global_home = Path(tempfile.mkdtemp())
        try:
            os.environ["OT_USER_HOME"] = str(global_home)

            # 1. Protected key and unsupported schema version in global config + mismatch with local config
            (global_home / "config.json").write_text(
                json.dumps(
                    {
                        "system": {"configSchemaVersion": 2},
                        "workItem": {"statuses": {"extra": {"label": "Extra"}}},
                    }
                ),
                encoding="utf-8",
            )
            (self.root / ".ot" / "config.local.json").write_text(
                json.dumps({"system": {"configSchemaVersion": 1}}),
                encoding="utf-8",
            )

            validator = Validator(self.root)
            diags = validator.validate_configuration()
            messages = [d.message for d in diags]
            self.assertTrue(any("Unsupported configuration schema version in global config: 2" in m for m in messages))
            self.assertTrue(any("Protected configuration key 'workItem.statuses' is improperly placed in global config" in m for m in messages))
            self.assertTrue(any("Configuration schema version mismatch across layers" in m for m in messages))

            # 2. Invalid JSON in global config produces ERROR diagnostic without crashing Validator
            (global_home / "config.json").write_text("{invalid json", encoding="utf-8")
            validator2 = Validator(self.root)
            diags2 = validator2.validate_configuration()
            self.assertTrue(any("Failed to parse global config" in d.message and d.severity == Severity.ERROR for d in diags2))
        finally:
            if old_home is None:
                os.environ.pop("OT_USER_HOME", None)
            else:
                os.environ["OT_USER_HOME"] = old_home
            shutil.rmtree(global_home, ignore_errors=True)

    def test_self_dependency_detection_and_repair(self):
        # Add self-dependency to an item
        task_file = self.root / ".ot" / "tasks" / "FixLoginCrash" / "index.md"
        content = task_file.read_text(encoding="utf-8")
        # Add self-UUID to dependencies
        item_id = "33333333-3333-4333-8333-333333333333"
        content = content.replace("dependencies:\n", f"dependencies:\n  - {item_id}\n")
        task_file.write_text(content, encoding="utf-8")

        validator = Validator(self.root)
        diags = validator.validate_all()
        self_dep_diags = [d for d in diags if "depends on itself" in d.message]
        self.assertEqual(len(self_dep_diags), 1)
        self.assertTrue(self_dep_diags[0].is_fixable)

        # Repair self-dependency
        repairer = Repairer(self.root)
        repairs = repairer.repair()
        self.assertTrue(any("Removed self-dependency" in r for r in repairs))

    def test_cli_check_command(self):
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "check", "--fix"])
        self.assertEqual(ret, 0)
        self.assertIn("Repairs applied:", buf.getvalue())

    def test_custom_paths_validation_and_leftover_warning(self):
        import io
        from contextlib import redirect_stdout

        # 1. Configure custom paths.tasks = "docs/tasks" while .ot/tasks still has sample tasks
        cfg_file = self.root / ".ot" / "config.json"
        cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
        cfg_data["paths"] = {
            "tasks": "docs/tasks",
            "meetings": "docs/meetings",
            "templates": ".ot/templates",
        }
        cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")

        validator = Validator(self.root)
        diags = validator.validate_all()
        messages = [d.message for d in diags]
        self.assertTrue(any("Missing required directory: docs/tasks" in m for m in messages))
        self.assertTrue(any("default directory '.ot/tasks' still contains files" in m for m in messages))

        # Repair creates docs/tasks and docs/meetings without deleting .ot/tasks
        repairer = Repairer(self.root)
        repairs = repairer.repair()
        self.assertTrue((self.root / "docs" / "tasks").is_dir())
        self.assertTrue((self.root / "docs" / "meetings").is_dir())
        self.assertTrue((self.root / ".ot" / "tasks").is_dir())

        # Creating a task writes into docs/tasks
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(self.root), "task", "create", "Custom Path Task", "--no-edit"])
        self.assertEqual(ret, 0)
        self.assertTrue((self.root / "docs" / "tasks" / "CustomPathTask" / "index.md").is_file())

        # 2. Path escaping project_root produces ERROR
        cfg_data["paths"]["tasks"] = "../escaped-tasks"
        cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")
        validator2 = Validator(self.root)
        diags2 = validator2.validate_configuration()
        self.assertTrue(
            any(
                "resolves outside the project root" in d.message and d.severity == Severity.ERROR
                for d in diags2
            )
        )

    def test_cycles_relative_links_and_standalone_file_repair(self):
        # 1. Standalone task file SomeTask.md -> SomeTask/index.md repair
        standalone = self.root / ".ot" / "tasks" / "StandaloneItem.md"
        standalone.write_text(
            "---\n"
            "id: 99999999-9999-4999-8999-999999999999\n"
            "title: Standalone Item\n"
            "type: task\n"
            "status: planned\n"
            "created_at: 2026-01-01T00:00:00Z\n"
            "updated_at: 2026-01-01T00:00:00Z\n"
            "---\n\n# Standalone Item\n",
            encoding="utf-8",
        )
        validator = Validator(self.root)
        diags = validator.validate_work_items()
        self.assertTrue(any("Standalone task file" in d.message and d.is_fixable for d in diags))

        repairer = Repairer(self.root)
        repairs = repairer.repair()
        self.assertTrue(any("Moved standalone task file" in r for r in repairs))
        self.assertFalse(standalone.exists())
        self.assertTrue((self.root / ".ot" / "tasks" / "StandaloneItem" / "index.md").is_file())

        # 2. Parent cycle and dependency cycle between two tasks
        from ot.parser import read_work_item, write_work_item

        t1 = self.root / ".ot" / "tasks" / "FixLoginCrash" / "index.md"
        t2 = self.root / ".ot" / "tasks" / "SetupCI" / "index.md"
        item1 = read_work_item(t1)
        item2 = read_work_item(t2)

        item1.meta.parent = item2.id
        item1.meta.dependencies = [item2.id]
        item1.body += "\nSee [missing doc](missing-spec.md) and [ext](https://example.com/spec).\n"
        write_work_item(item1)

        item2.meta.parent = item1.id
        item2.meta.dependencies = [item1.id]
        write_work_item(item2)

        validator2 = Validator(self.root)
        diags2 = validator2.validate_work_items()
        msgs2 = [d.message for d in diags2]
        self.assertTrue(any("Circular parent relationship detected" in m for m in msgs2))
        self.assertTrue(any("Circular dependency relationship detected" in m for m in msgs2))
        self.assertTrue(any("Broken relative Markdown link 'missing-spec.md'" in m for m in msgs2))
        self.assertFalse(any("https://example.com/spec" in m for m in msgs2))

    def test_dvcs_safety_checks_and_conflict_markers(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout

        # 1. Simulate active Git merge (.git/MERGE_HEAD)
        git_dir = self.root / ".git"
        git_dir.mkdir(exist_ok=True)
        merge_head = git_dir / "MERGE_HEAD"
        merge_head.write_text("deadbeef\n", encoding="utf-8")

        # Read-only command succeeds
        out_ro = io.StringIO()
        with redirect_stdout(out_ro):
            ret_ro = main(["-C", str(self.root), "task", "list"])
        self.assertEqual(ret_ro, 0)

        # Mutating command is blocked without --force
        out_mut = io.StringIO()
        err_mut = io.StringIO()
        with redirect_stdout(out_mut), redirect_stderr(err_mut):
            ret_mut = main(["-C", str(self.root), "task", "status", "Setup Continuous Integration Pipeline", "completed"])
        self.assertEqual(ret_mut, 1)
        self.assertIn("unsafe VCS state", err_mut.getvalue())

        # Mutating command succeeds with --force
        out_force = io.StringIO()
        with redirect_stdout(out_force):
            ret_force = main([
                "-C",
                str(self.root),
                "task",
                "status",
                "Setup Continuous Integration Pipeline",
                "completed",
                "--force",
            ])
        self.assertEqual(ret_force, 0)

        # Validator reports vcs diagnostic
        v_git = Validator(self.root)
        diags_git = v_git.validate_all()
        self.assertTrue(any(d.category == "vcs" and "MERGE_HEAD" in d.message for d in diags_git))
        shutil.rmtree(git_dir, ignore_errors=True)

        # 2. Simulate active Mercurial rebase (.hg/rebasestate)
        hg_dir = self.root / ".hg"
        hg_dir.mkdir(exist_ok=True)
        (hg_dir / "rebasestate").write_text("state\n", encoding="utf-8")
        err_hg = io.StringIO()
        with redirect_stderr(err_hg):
            ret_hg = main(["-C", str(self.root), "task", "create", "Blocked By Hg Rebase", "--no-edit"])
        self.assertEqual(ret_hg, 1)
        self.assertIn(".hg/rebasestate", err_hg.getvalue())
        shutil.rmtree(hg_dir, ignore_errors=True)

        # 3. Conflict markers in config, templates, and meetings
        marker_start = "<" * 7 + " HEAD"
        marker_end = ">" * 7 + " branch"
        tpl_dir = self.root / ".ot" / "templates" / "tasks"
        tpl_dir.mkdir(parents=True, exist_ok=True)
        (tpl_dir / "conflict.md").write_text(f"# Title\n{marker_start}\nA\n{marker_end}\n", encoding="utf-8")

        mtg_dir = self.root / ".ot" / "meetings"
        mtg_dir.mkdir(parents=True, exist_ok=True)
        (mtg_dir / "conflict_mtg.md").write_text(f"# Mtg\n{marker_start}\nB\n{marker_end}\n", encoding="utf-8")

        v_conflict = Validator(self.root)
        c_diags = v_conflict.validate_all()
        conflict_msgs = [d.message for d in c_diags if d.category == "merge_conflict"]
        self.assertTrue(any("template conflict.md" in m for m in conflict_msgs))
        self.assertTrue(any("meeting conflict_mtg.md" in m for m in conflict_msgs))

    def test_attachment_validation_broken_links_and_orphans(self):
        task_dir = self.root / ".ot" / "tasks" / "FixLoginCrash"
        att_dir = task_dir / "attachments"
        att_dir.mkdir(parents=True, exist_ok=True)
        # Orphaned file in attachments/ not referenced in index.md
        (att_dir / "orphan.png").write_bytes(b"1234")
        # Referenced file + broken attachment link in index.md
        (att_dir / "linked.png").write_bytes(b"5678")
        index_md = task_dir / "index.md"
        content = index_md.read_text(encoding="utf-8")
        index_md.write_text(
            content + "\n![ok](attachments/linked.png)\n![missing](attachments/missing.png)\n",
            encoding="utf-8",
        )

        v = Validator(self.root)
        diags = v.validate_all()
        broken_errs = [
            d for d in diags if "Broken relative Markdown link 'attachments/missing.png'" in d.message
        ]
        self.assertEqual(len(broken_errs), 1)
        self.assertEqual(broken_errs[0].severity, Severity.ERROR)

        orphans = [d for d in diags if "Orphaned attachment" in d.message]
        self.assertEqual(len(orphans), 1)
        self.assertEqual(orphans[0].severity, Severity.WARNING)
        self.assertIn("orphan.png", orphans[0].message)


if __name__ == "__main__":
    unittest.main()
