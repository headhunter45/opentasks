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

    def test_auto_download_on_config_version_change_in_ot_and_oat(self):
        """Regression for 65e194: updating system.toolVersion in .ot/config.json
        and running `ot task list` or `./oat task list` must automatically download
        and install `.ot/bin/<version>/ot.zipapp` + manifest while preserving old versions.
        """
        import json
        import os
        import subprocess
        import sys
        from ot.installation import init_project

        src_dir = Path(__file__).resolve().parent.parent / "src"
        proj_dir = self.root / "auto_dl_project"
        init_project(proj_dir, version="0.1.0")
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.1.0" / "ot.zipapp").is_file())

        # Prepare simulated GitHub Releases hosting v0.2.0 and v0.3.0
        releases_root = self.root / "releases"
        for ver in ("0.2.0", "0.3.0"):
            rdir = releases_root / f"v{ver}"
            rdir.mkdir(parents=True)
            art = rdir / f"ot-{ver}.zipapp"
            m = build_zipapp_artifact(src_dir, art, ver)
            (rdir / "SHA256SUMS").write_text(f"{m.sha256}  ot-{ver}.zipapp\n", encoding="utf-8")

        # Build global `ot` zipapp
        global_ot = self.root / "global-bin" / "ot"
        build_zipapp_artifact(src_dir, global_ot, "0.1.0")

        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env["OT_USER_HOME"] = str(self.root / "user_ot_home")
        env["OT_RELEASE_BASE_URL"] = releases_root.as_uri()
        env["OT_DISABLE_SOURCE_FALLBACK"] = "1"

        # 1. Update config.json to 0.2.0 and run global `ot task list`
        cfg_file = proj_dir / ".ot" / "config.json"
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        cfg["system"]["toolVersion"] = "0.2.0"
        cfg_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        res_ot = subprocess.run(
            [sys.executable, str(global_ot), "task", "list"],
            cwd=str(proj_dir),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(
            res_ot.returncode,
            0,
            f"ot task list failed:\nSTDOUT: {res_ot.stdout}\nSTDERR: {res_ot.stderr}",
        )
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.2.0" / "ot.zipapp").is_file())
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.2.0" / "ot-manifest.json").is_file())
        # Old version 0.1.0 is preserved
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.1.0" / "ot.zipapp").is_file())
        # Global cache was populated
        self.assertTrue(
            (Path(env["OT_USER_HOME"]) / "versions" / "0.2.0" / "ot.zipapp").is_file()
        )

        # 2. Update config.json to 0.3.0 and run `./oat task list`
        cfg["system"]["toolVersion"] = "0.3.0"
        cfg_file.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

        res_oat = subprocess.run(
            [str(proj_dir / "oat"), "task", "list"],
            cwd=str(proj_dir),
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(
            res_oat.returncode,
            0,
            f"./oat task list failed:\nSTDOUT: {res_oat.stdout}\nSTDERR: {res_oat.stderr}",
        )
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.3.0" / "ot.zipapp").is_file())
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.3.0" / "ot-manifest.json").is_file())
        self.assertTrue(
            (Path(env["OT_USER_HOME"]) / "versions" / "0.3.0" / "ot.zipapp").is_file()
        )


if __name__ == "__main__":
    unittest.main()
