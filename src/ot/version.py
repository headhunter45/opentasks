"""Version and semver validation utilities for Open Tasks."""

from __future__ import annotations

import re
from typing import Optional, Tuple

VERSION_PATTERN = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)


def parse_semver(v_str: str) -> Tuple[int, int, int, str]:
    """Parse a semantic version string into (major, minor, patch, prerelease)."""
    clean = v_str.strip().lstrip("v")
    m = VERSION_PATTERN.match(clean)
    if not m:
        raise ValueError(f"Invalid semantic version string: '{v_str}'")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    prerelease = m.group(4) or ""
    return major, minor, patch, prerelease


def is_valid_version(v_str: str) -> bool:
    """Check if version string is a valid semantic version."""
    try:
        parse_semver(v_str)
        return True
    except ValueError:
        return False


def compare_versions(v1: str, v2: str) -> int:
    """Compare two semantic versions.

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """
    maj1, min1, pat1, pre1 = parse_semver(v1)
    maj2, min2, pat2, pre2 = parse_semver(v2)

    t1 = (maj1, min1, pat1)
    t2 = (maj2, min2, pat2)
    if t1 < t2:
        return -1
    if t1 > t2:
        return 1

    # Same major.minor.patch: prerelease is lower than release
    if pre1 and not pre2:
        return -1
    if not pre1 and pre2:
        return 1
    if pre1 < pre2:
        return -1
    if pre1 > pre2:
        return 1
    return 0


from pathlib import Path
from ot.config import load_json_file
from ot.discovery import find_project_root


def discover_project_version(project_root: Optional[Path | str] = None) -> Optional[str]:
    """Discover the configured Open Tasks version for a project from .ot/config.json."""
    root = find_project_root(project_root)
    if not root:
        return None
    config_file = root / ".ot" / "config.json"
    if not config_file.is_file():
        return None
    try:
        data = load_json_file(config_file)
        return data.get("system", {}).get("toolVersion")
    except Exception:
        return None


def discover_installed_version(project_root: Optional[Path | str] = None) -> Optional[str]:
    """Discover the version of the installed executable beneath .ot/bin/."""
    root = find_project_root(project_root)
    if not root:
        return None
    bin_dir = root / ".ot" / "bin"
    if not bin_dir.is_dir():
        return None

    configured = discover_project_version(root)
    if configured:
        versioned_manifest = bin_dir / configured / "ot-manifest.json"
        if versioned_manifest.is_file():
            try:
                data = load_json_file(versioned_manifest)
                return data.get("version")
            except Exception:
                pass
        if (bin_dir / configured / "ot.zipapp").is_file():
            return configured

    # Check any versioned subdirectories .ot/bin/<ver>/ot-manifest.json
    found_versions = []
    for child in bin_dir.iterdir():
        if child.is_dir():
            m_file = child / "ot-manifest.json"
            if m_file.is_file():
                try:
                    v = load_json_file(m_file).get("version")
                    if v and is_valid_version(v):
                        found_versions.append(v)
                except Exception:
                    pass
    if found_versions:
        from functools import cmp_to_key
        found_versions.sort(key=cmp_to_key(compare_versions))
        return found_versions[-1]

    # Fallback to legacy flat .ot/bin/ot-manifest.json
    manifest_file = bin_dir / "ot-manifest.json"
    if manifest_file.is_file():
        try:
            data = load_json_file(manifest_file)
            return data.get("version")
        except Exception:
            pass
    return None


def validate_project_version(project_root: Optional[Path | str] = None) -> Tuple[bool, Optional[str]]:
    """Validate project version configuration against installed binary.

    Returns:
        (is_valid, error_message_or_none)
    """
    root = find_project_root(project_root)
    if not root:
        return True, None

    configured = discover_project_version(root)
    if not configured:
        return True, None

    if not is_valid_version(configured):
        return False, f"Configured toolVersion '{configured}' is not a valid semantic version."

    installed = discover_installed_version(root)
    if installed and installed != configured:
        return False, f"Version mismatch: Configured version is '{configured}', but installed binary is '{installed}'."

    return True, None

