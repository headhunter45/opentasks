"""Tests for cache management, download verification, transactional upgrades, and ot upgrade CLI."""

import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ot.cache import (
    ChecksumMismatchError,
    cache_version_artifact,
    get_cached_version_path,
    is_version_cached,
    verify_artifact_checksum,
)
from ot.cli import main
from ot.installation import init_project
from ot.packaging import build_zipapp_artifact, compute_sha256
from ot.upgrade import (
    UpgradeError,
    fetch_version_artifact,
    perform_transactional_upgrade,
)


class TestUpgradeSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        # Use isolated global OT directory for test cache
        os.environ["OT_USER_HOME"] = str(self.root / "global_ot")

    def tearDown(self):
        os.environ.pop("OT_USER_HOME", None)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cache_management_and_checksum_verification(self):
        src_dir = Path(__file__).resolve().parent.parent / "src"
        zipapp_file = self.root / "test.zipapp"
        build_zipapp_artifact(src_dir, zipapp_file, "0.2.0")

        # Correct checksum
        sha = compute_sha256(zipapp_file)
        self.assertTrue(verify_artifact_checksum(zipapp_file, sha))

        # Checksum mismatch
        with self.assertRaises(ChecksumMismatchError):
            verify_artifact_checksum(zipapp_file, "bad_checksum_hash_value")

        # Cache artifact
        cached = cache_version_artifact("0.2.0", zipapp_file, expected_sha256=sha)
        self.assertTrue(is_version_cached("0.2.0"))
        self.assertEqual(cached, get_cached_version_path("0.2.0"))

    def test_perform_transactional_upgrade(self):
        proj_dir = self.root / "my_project"
        init_project(proj_dir, version="0.1.0")
        # Simulate legacy otw / otw.bat wrappers from older release
        (proj_dir / "otw").write_text("#!/bin/sh\n", encoding="utf-8")
        (proj_dir / "otw.bat").write_text("@echo off\n", encoding="utf-8")

        # Upgrade to 0.2.0
        res = perform_transactional_upgrade(proj_dir, "0.2.0")
        self.assertEqual(res["status"], "upgraded")

        # Verify config.json was updated
        cfg = json.loads((proj_dir / ".ot" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["system"]["toolVersion"], "0.2.0")

        # Verify oat / oat.bat exist and legacy otw / otw.bat were removed
        self.assertTrue((proj_dir / "oat").is_file())
        self.assertTrue((proj_dir / "oat.bat").is_file())
        self.assertFalse((proj_dir / "otw").exists())
        self.assertFalse((proj_dir / "otw.bat").exists())

        # Verify new versioned binary and manifest were installed AND old version was preserved
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.1.0" / "ot.zipapp").is_file())
        self.assertTrue((proj_dir / ".ot" / "bin" / "0.2.0" / "ot.zipapp").is_file())
        manifest = json.loads(
            (proj_dir / ".ot" / "bin" / "0.2.0" / "ot-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["version"], "0.2.0")

    def test_download_version_artifact_with_sha256sums(self):
        from ot.cache import download_version_artifact

        src_dir = Path(__file__).resolve().parent.parent / "src"
        release_dir = self.root / "releases" / "v0.3.0"
        release_dir.mkdir(parents=True)
        artifact_file = release_dir / "ot-0.3.0.zipapp"
        manifest = build_zipapp_artifact(src_dir, artifact_file, "0.3.0")
        (release_dir / "SHA256SUMS").write_text(
            f"{manifest.sha256}  ot-0.3.0.zipapp\n", encoding="utf-8"
        )

        base_url = (self.root / "releases").as_uri()
        cached_path = download_version_artifact("0.3.0", base_url=base_url)
        self.assertTrue(cached_path.is_file())
        self.assertEqual(cached_path, get_cached_version_path("0.3.0"))

        # Corrupt SHA256SUMS and verify ChecksumMismatchError is raised
        release_bad = self.root / "releases" / "v0.3.1"
        release_bad.mkdir(parents=True)
        bad_artifact = release_bad / "ot-0.3.1.zipapp"
        build_zipapp_artifact(src_dir, bad_artifact, "0.3.1")
        (release_bad / "SHA256SUMS").write_text(
            "0000000000000000000000000000000000000000000000000000000000000000  ot-0.3.1.zipapp\n",
            encoding="utf-8",
        )
        with self.assertRaises(ChecksumMismatchError):
            download_version_artifact("0.3.1", base_url=base_url)

    def test_upgrade_downgrade_rejection(self):
        proj_dir = self.root / "my_project_downgrade"
        init_project(proj_dir, version="0.2.0")

        with self.assertRaises(UpgradeError):
            perform_transactional_upgrade(proj_dir, "0.1.0")

    def test_cli_upgrade_command(self):
        proj_dir = self.root / "cli_upgrade_proj"
        init_project(proj_dir, version="0.1.0")

        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["-C", str(proj_dir), "upgrade", "--version", "0.2.0"])
        self.assertEqual(ret, 0)
        self.assertIn("Successfully upgraded", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
