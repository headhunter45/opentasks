"""Tests for ot init and project installation."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ot.cli import main
from ot.installation import init_project
from ot.packaging import build_zipapp_artifact


class TestInstallationAndInit(unittest.TestCase):
    def test_init_project_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            res = init_project(
                target_dir=tmpdir,
                project_name="Demo Init",
                version="0.1.0",
                description="Demo project",
                install_binary=True,
                create_wrappers=True,
            )
            root = Path(tmpdir)
            self.assertTrue((root / ".ot").is_dir())
            self.assertTrue((root / ".ot" / "config.json").is_file())
            self.assertTrue((root / ".ot" / "templates" / "tasks" / "default.md").is_file())
            self.assertTrue((root / ".ot" / "bin" / "0.1.0" / "ot.zipapp").is_file())
            self.assertTrue((root / ".ot" / "bin" / "0.1.0" / "ot-manifest.json").is_file())
            self.assertTrue((root / "otw").is_file())
            self.assertTrue((root / ".gitignore").is_file())
            self.assertIn(".ot/bin/", (root / ".gitignore").read_text(encoding="utf-8"))

            cfg_data = json.loads((root / ".ot" / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(cfg_data["system"]["toolVersion"], "0.1.0")
            self.assertEqual(cfg_data["project"]["name"], "Demo Init")

    def test_init_project_updates_existing_gitignore_idempotently(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gitignore = root / ".gitignore"
            gitignore.write_text("node_modules/\n.DS_Store", encoding="utf-8")

            init_project(target_dir=root, install_binary=False, create_wrappers=False)
            content = gitignore.read_text(encoding="utf-8")
            self.assertEqual(content, "node_modules/\n.DS_Store\n.ot/bin/\n")

            # Running init again must not duplicate .ot/bin/
            init_project(target_dir=root, install_binary=False, create_wrappers=False)
            self.assertEqual(gitignore.read_text(encoding="utf-8"), content)

    def test_cli_init_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            buf = io.StringIO()
            with redirect_stdout(buf):
                ret = main(["init", tmpdir, "--name", "CLI Project", "--version", "0.1.0"])
            self.assertEqual(ret, 0)
            self.assertIn("Initialized Open Tasks project", buf.getvalue())
            self.assertTrue((Path(tmpdir) / ".ot" / "config.json").is_file())

    def test_init_from_distributed_zipapp(self):
        """Regression: `ot init` run from an installed .zipapp (e.g.
        ``~/.local/bin/ot``) must not fail with "Source package not found".

        The running binary *is* the source, so ``init`` copies it into the new
        project's ``.ot/bin/`` rather than probing for a ``src/ot`` tree that
        isn't present beside a distributed artifact. See the bug where running
        v0.1.0/v0.1.1 failed with:

            Initialization failed: Source package not found at
            /Users/.../.local/bin/src/ot
        """
        with tempfile.TemporaryDirectory() as wd:
            wd = Path(wd)
            src = Path(__file__).resolve().parent.parent / "src"
            bin_dir = wd / "bin"
            bin_dir.mkdir()
             # install.sh drops BINARY_NAME "ot" directly in the bin dir,
            # with no sibling "src/" to find.
            fakebin = bin_dir / "ot"

            from ot.packaging import build_zipapp_artifact
            build_zipapp_artifact(src, fakebin, "0.1.1")
            os.chmod(fakebin, 0o755)

            proj = wd / "project"
            proj.mkdir()
            env = dict(os.environ)
            env["OT_USER_HOME"] = str(wd / "home")
            # Point PYTHONPATH away so the subprocess can't accidentally
            # resolve ot from this checkout — it must use the zipapp only.
            env.pop("PYTHONPATH", None)

            # Run init straight from the bin-dir zipapp, exactly like the user.
            res = subprocess.run(
                [sys.executable, str(fakebin), "init", str(proj),
                "--version", "0.1.1"],
                capture_output=True, text=True, env=env)
            self.assertEqual(
                res.returncode, 0,
                f"init failed from zipapp:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}",
             )

            # The project binary must have been installed under .ot/bin/<version>/...
            proj_zip = proj / ".ot" / "bin" / "0.1.1" / "ot.zipapp"
            self.assertTrue(proj_zip.is_file())
            # ...along with its manifest so version discovery works.
            manifest = proj / ".ot" / "bin" / "0.1.1" / "ot-manifest.json"
            self.assertTrue(manifest.is_file())
            self.assertEqual(json.loads(manifest.read_text())["version"], "0.1.1")
            # ...and that installed binary must itself run.
            run = subprocess.run(
                [sys.executable, str(proj_zip), "version"],
                 capture_output=True, text=True, env=env,
                cwd=str(proj),
             )
            self.assertEqual(
                run.returncode, 0,
                f"installed project binary failed:\nSTDOUT: {run.stdout}\nSTDERR: {run.stderr}",
             )
            self.assertIn("Open Tasks", run.stdout)


if __name__ == "__main__":
    unittest.main()
