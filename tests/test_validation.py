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


if __name__ == "__main__":
    unittest.main()
