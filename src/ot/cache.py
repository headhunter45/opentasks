"""Cache management and download verification for Open Tasks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Optional
import urllib.error
import urllib.request

from ot.packaging import compute_sha256
from ot.version import is_valid_version

DEFAULT_GITHUB_REPO = "headhunter45/opentasks"


class ChecksumMismatchError(ValueError):
    """Raised when downloaded artifact checksum does not match expected SHA-256."""
    pass


class DownloadError(RuntimeError):
    """Raised when a release artifact cannot be downloaded."""
    pass


def get_global_ot_dir() -> Path:
    """Return ~/.ot directory path, falling back to /tmp/ot-cache if ~/.ot is not writable."""
    p = Path(os.getenv("OT_USER_HOME") or "~/.ot").expanduser().resolve()
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except OSError:
        fallback = Path(tempfile.gettempdir()) / f"ot-user-{os.getuid()}"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_cache_dir() -> Path:
    """Return ~/.ot/cache/ directory path."""
    d = get_global_ot_dir() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_versions_cache_dir() -> Path:
    """Return ~/.ot/versions/ directory path."""
    d = get_global_ot_dir() / "versions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_cached_version_path(version: str) -> Path:
    """Return the cached zipapp path for a version in ~/.ot/versions/<version>/ot.zipapp."""
    return get_versions_cache_dir() / version / "ot.zipapp"


def is_version_cached(version: str) -> bool:
    """Check if version artifact is present in local cache."""
    return get_cached_version_path(version).is_file()


def verify_artifact_checksum(artifact_path: Path | str, expected_sha256: str) -> bool:
    """Verify that file's SHA-256 matches expected checksum.

    Raises ChecksumMismatchError on mismatch.
    """
    actual = compute_sha256(artifact_path)
    if actual.lower() != expected_sha256.strip().lower():
        raise ChecksumMismatchError(
            f"Checksum mismatch for {artifact_path}: expected {expected_sha256}, got {actual}"
        )
    return True


def cache_version_artifact(
    version: str,
    artifact_path: Path | str,
    expected_sha256: Optional[str] = None,
) -> Path:
    """Store an artifact into ~/.ot/versions/<version>/ot.zipapp after checksum verification."""
    if not is_valid_version(version):
        raise ValueError(f"Invalid version string: '{version}'")

    src = Path(artifact_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Source artifact not found: {src}")

    if expected_sha256:
        verify_artifact_checksum(src, expected_sha256)

    dest_dir = get_versions_cache_dir() / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_zipapp = dest_dir / "ot.zipapp"

    shutil.copy2(src, dest_zipapp)

    # Save manifest
    manifest_data = {
        "version": version,
        "sha256": compute_sha256(dest_zipapp),
    }
    (dest_dir / "ot-manifest.json").write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return dest_zipapp


def parse_sha256sums(sums_text: str, version: str) -> Optional[str]:
    """Extract expected SHA-256 checksum for `version` from a SHA256SUMS file."""
    clean_ver = version.strip().lstrip("v")
    target_names = {f"ot-{clean_ver}.zipapp", "ot.zipapp"}
    for line in sums_text.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2:
            sha = parts[0]
            filename = parts[1].lstrip("*")
            if Path(filename).name in target_names:
                return sha
    return None


def download_version_artifact(
    version: str,
    base_url: Optional[str] = None,
    timeout: float = 10.0,
) -> Path:
    """Download `version` from GitHub Releases (or `base_url`), verify SHA256SUMS, and cache it."""
    if not is_valid_version(version):
        raise ValueError(f"Invalid version string: '{version}'")

    clean_ver = version.strip().lstrip("v")
    if not base_url:
        env_base = os.getenv("OT_RELEASE_BASE_URL")
        if env_base:
            base_url = env_base.rstrip("/")
        else:
            repo = os.getenv("OT_GITHUB_REPO", DEFAULT_GITHUB_REPO)
            base_url = f"https://github.com/{repo}/releases/download"

    artifact_url = f"{base_url}/v{clean_ver}/ot-{clean_ver}.zipapp"
    sums_url = f"{base_url}/v{clean_ver}/SHA256SUMS"

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        tmp_bin = tmp_path / f"ot-{clean_ver}.zipapp"

        try:
            with urllib.request.urlopen(artifact_url, timeout=timeout) as resp:
                tmp_bin.write_bytes(resp.read())
        except urllib.error.HTTPError as e:
            e.close()
            raise DownloadError(
                f"Failed to download Open Tasks v{clean_ver} from {artifact_url}: {e}"
            ) from e
        except Exception as e:
            raise DownloadError(
                f"Failed to download Open Tasks v{clean_ver} from {artifact_url}: {e}"
            ) from e

        expected_sha: Optional[str] = None
        try:
            with urllib.request.urlopen(sums_url, timeout=timeout) as resp:
                sums_text = resp.read().decode("utf-8", errors="replace")
                expected_sha = parse_sha256sums(sums_text, clean_ver)
        except urllib.error.HTTPError as e:
            e.close()
            expected_sha = None
        except Exception:
            expected_sha = None

        return cache_version_artifact(clean_ver, tmp_bin, expected_sha256=expected_sha)
