"""Tests for global launcher and project binary dispatch."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ot.launcher import (
    find_project_binary,
    get_configured_version,
    run_launcher,
)
from ot.packaging import build_zipapp_artifact


class TestGlobalLauncher(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        sample_src = Path(__file__).resolve().parent.parent / "examples" / "sample-project"
        shutil.copytree(sample_src, self.root, dirs_exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_launcher_version_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = run_launcher(["version"], start_dir=self.root)
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("Open Tasks Launcher", out)
        self.assertIn("Project root:", out)

    def test_launcher_dispatches_to_project_installed_binary(self):
        # Build and install zipapp into .ot/bin/ot.zipapp
        bin_dir = self.root / ".ot" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        src_dir = Path(__file__).resolve().parent.parent / "src"
        build_zipapp_artifact(src_dir, bin_dir / "ot.zipapp", "0.1.0")

        found_bin = find_project_binary(self.root)
        self.assertIsNotNone(found_bin)
        self.assertEqual(found_bin.name, "ot.zipapp")

        # Test launcher dispatch
        ret = run_launcher(["task", "list"], start_dir=self.root)
        self.assertEqual(ret, 0)

    def test_packaged_global_zipapp_delegates_to_project_zipapp(self):
        """Regression: global `ot` packaged as a .zipapp must invoke run_launcher
        and delegate to the project's .ot/bin/ zipapp without infinite recursion.
        """
        import os
        import subprocess
        import sys

        src_dir = Path(__file__).resolve().parent.parent / "src"
        global_bin = self.root / "global-bin" / "ot"
        build_zipapp_artifact(src_dir, global_bin, "0.1.0")

        proj_bin = self.root / ".ot" / "bin" / "ot.zipapp"
        build_zipapp_artifact(src_dir, proj_bin, "0.1.1")

        env = dict(os.environ)
        env.pop("PYTHONPATH", None)

        res = subprocess.run(
            [sys.executable, str(global_bin), "task", "list"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(
            res.returncode,
            0,
            f"global zipapp failed:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}",
        )
        self.assertIn("ID", res.stdout)

        # Direct execution of the project zipapp must also succeed without recursion
        res_direct = subprocess.run(
            [sys.executable, str(proj_bin), "task", "list"],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(res_direct.returncode, 0)


if __name__ == "__main__":
    unittest.main()
