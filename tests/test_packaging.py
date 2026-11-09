"""Tests for packaging, versioning, and release artifacts."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from ot.packaging import (
    ReleaseManifest,
    build_zipapp_artifact,
    compute_sha256,
)
from ot.version import (
    compare_versions,
    is_valid_version,
    parse_semver,
)


class TestVersioningAndPackaging(unittest.TestCase):
    def test_semver_parsing_and_comparison(self):
        self.assertTrue(is_valid_version("1.0.0"))
        self.assertTrue(is_valid_version("0.1.0-alpha"))
        self.assertTrue(is_valid_version("0.5.0-rc.1"))
        self.assertTrue(is_valid_version("v0.5.0-rc.1"))
        self.assertFalse(is_valid_version("1.0"))
        self.assertFalse(is_valid_version("abc"))

        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(compare_versions("1.0.0", "1.1.0"), -1)
        self.assertEqual(compare_versions("2.0.0", "1.9.9"), 1)
        self.assertEqual(compare_versions("1.0.0-alpha", "1.0.0"), -1)
        self.assertEqual(compare_versions("0.5.0-rc.1", "0.5.0"), -1)
        self.assertEqual(compare_versions("0.5.0-rc.1", "0.5.0-rc.2"), -1)
        self.assertEqual(compare_versions("0.5.0-rc.2", "0.5.0-rc.10"), -1)

    def test_deploy_workflow_supports_rc_tags_without_pages(self):
        workflow_path = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "deploy.yml"
        content = workflow_path.read_text(encoding="utf-8")
        self.assertIn("'v[0-9]*-rc.[0-9]*'", content)
        self.assertIn("IS_PRERELEASE", content)
        self.assertIn("--prerelease", content)
        self.assertIn("if: needs.build-and-publish.outputs.deploy_pages == 'true'", content)

    def test_build_zipapp_artifact(self):
        src_dir = Path(__file__).resolve().parent.parent / "src"
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "dist" / "ot.zipapp"
            manifest = build_zipapp_artifact(src_dir, out_path, "0.1.0")

            self.assertTrue(out_path.is_file())
            self.assertEqual(manifest.version, "0.1.0")
            self.assertEqual(manifest.sha256, compute_sha256(out_path))

            # Test executing the packaged zipapp via python3
            res = subprocess.run(
                ["python3", str(out_path), "--help"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Open Tasks", res.stdout)

            # Test that packaged version command reflects stamped version
            res_v = subprocess.run(
                ["python3", str(out_path), "version"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res_v.returncode, 0)
            self.assertIn("0.1.0", res_v.stdout)

    def test_version_discovery_and_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ot_dir = root / ".ot"
            ot_dir.mkdir()

            from ot.version import discover_project_version, validate_project_version

            # Initially not configured
            self.assertIsNone(discover_project_version(root))

            # Configured valid version
            cfg = {"system": {"toolVersion": "1.2.0"}}
            (ot_dir / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
            self.assertEqual(discover_project_version(root), "1.2.0")

            is_valid, err = validate_project_version(root)
            self.assertTrue(is_valid)

            # Version mismatch
            (ot_dir / "bin").mkdir()
            manifest = {"version": "1.1.0"}
            (ot_dir / "bin" / "ot-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

            is_valid, err = validate_project_version(root)
            self.assertFalse(is_valid)
            self.assertIn("Version mismatch", err)



if __name__ == "__main__":
    unittest.main()
