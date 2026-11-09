"""Transactional upgrade and version management for Open Tasks."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple

from ot.cache import (
    ChecksumMismatchError,
    DownloadError,
    cache_version_artifact,
    download_version_artifact,
    get_cached_version_path,
    is_version_cached,
    parse_sha256sums,
    verify_artifact_checksum,
)
from ot.config import load_config, load_json_file
from ot.discovery import find_project_root
from ot.installation import WRAPPER_SCRIPT_BAT, WRAPPER_SCRIPT_SH
from ot.packaging import build_zipapp_artifact, compute_sha256
from ot.templates import install_default_templates, upgrade_project_templates
from ot.validation import Validator
from ot.version import (
    compare_versions,
    discover_project_version,
    is_valid_version,
)


class UpgradeError(RuntimeError):
    """Raised when an upgrade operation fails."""
    pass


CURRENT_CONFIG_SCHEMA_VERSION = 1

# Registry mapping schema version `v` -> callable migrating config dict from `v` to `v + 1`.
CONFIG_MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}


def run_config_migrations(
    config_data: Dict[str, Any],
    target_schema_version: int = CURRENT_CONFIG_SCHEMA_VERSION,
    update_version_key: bool = True,
) -> Tuple[Dict[str, Any], List[str]]:
    """Run sequential single-integer configuration schema migrations up to `target_schema_version`."""
    data = copy.deepcopy(config_data)
    sys_section = data.get("system", {})
    raw_ver = sys_section.get("configSchemaVersion") if isinstance(sys_section, dict) else None
    current_ver = int(raw_ver) if raw_ver is not None else target_schema_version

    if current_ver > target_schema_version:
        raise UpgradeError(
            f"Configuration schema version {current_ver} is newer than supported target {target_schema_version}."
        )

    steps_applied: List[str] = []
    while current_ver < target_schema_version:
        migrator = CONFIG_MIGRATIONS.get(current_ver)
        if migrator is None:
            raise UpgradeError(
                f"No configuration migration registered for schema version {current_ver} -> {current_ver + 1}."
            )
        data = migrator(data)
        next_ver = current_ver + 1
        if update_version_key or ("system" in data and "configSchemaVersion" in data.get("system", {})):
            data.setdefault("system", {})["configSchemaVersion"] = next_ver
        steps_applied.append(f"{current_ver}->{next_ver}")
        current_ver = next_ver

    if update_version_key:
        data.setdefault("system", {})["configSchemaVersion"] = target_schema_version

    return data, steps_applied


def install_artifact_to_project_bin(
    project_root: Path,
    version: str,
    artifact_path: Path,
) -> Path:
    """Copy a verified artifact into .ot/bin/<version>/ot.zipapp with its manifest."""
    dest_dir = project_root / ".ot" / "bin" / version
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_zipapp = dest_dir / "ot.zipapp"
    shutil.copy2(artifact_path, dest_zipapp)
    dest_zipapp.chmod(0o755)

    manifest_data = {
        "version": version,
        "sha256": compute_sha256(dest_zipapp),
        "artifact_name": "ot.zipapp",
    }
    (dest_dir / "ot-manifest.json").write_text(
        json.dumps(manifest_data, indent=2), encoding="utf-8"
    )
    return dest_zipapp


def fetch_version_artifact(
    version: str,
    mirror_dir: Optional[Path | str] = None,
) -> Path:
    """Obtain the zipapp artifact for `version`, checking cache, mirror, GitHub Releases, or source."""
    if not is_valid_version(version):
        raise UpgradeError(f"Invalid version string: '{version}'")

    if is_version_cached(version):
        return get_cached_version_path(version)

    # Check optional mirror directory (e.g. dist/ or local release repository)
    effective_mirror = mirror_dir or os.getenv("OT_MIRROR_DIR")
    if effective_mirror:
        m = Path(effective_mirror)
        candidate = m / f"ot-{version}.zipapp"
        if not candidate.is_file():
            candidate = m / "v" / version / f"ot-{version}.zipapp"
        if not candidate.is_file():
            candidate = m / "ot.zipapp"
        if candidate.is_file():
            sums_file = candidate.parent / "SHA256SUMS"
            expected_sha = None
            if sums_file.is_file():
                expected_sha = parse_sha256sums(sums_file.read_text(encoding="utf-8"), version)
            return cache_version_artifact(version, candidate, expected_sha256=expected_sha)

    # Try downloading from GitHub Releases (or configured OT_RELEASE_BASE_URL)
    download_err: Optional[Exception] = None
    if os.getenv("OT_OFFLINE") != "1":
        try:
            return download_version_artifact(version)
        except ChecksumMismatchError as e:
            raise UpgradeError(str(e)) from e
        except Exception as e:
            download_err = e

    # Fallback: package from local developer source checkout if available and allowed
    if os.getenv("OT_DISABLE_SOURCE_FALLBACK") != "1":
        src_dir = Path(__file__).resolve().parent.parent
        if (src_dir / "ot").is_dir():
            with tempfile.NamedTemporaryFile("w", suffix=".zipapp", delete=False) as tf:
                temp_out = tf.name
            try:
                build_zipapp_artifact(src_dir, temp_out, version)
                return cache_version_artifact(version, temp_out)
            finally:
                if os.path.exists(temp_out):
                    os.remove(temp_out)

    raise UpgradeError(
        f"Unable to obtain Open Tasks v{version}: {download_err or 'no release source available'}"
    )


def perform_transactional_upgrade(
    project_root: Path | str,
    target_version: str,
    mirror_dir: Optional[Path | str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Execute a transactional upgrade of a project to target_version.

    Guarantees that if any failure occurs during download, schema migration,
    template generation, or validation, the existing project files remain untouched.
    """
    root = find_project_root(project_root)
    if not root:
        raise UpgradeError("No Open Tasks project found (.ot).")

    if not is_valid_version(target_version):
        raise UpgradeError(f"Target version '{target_version}' is not a valid semantic version.")

    current_version = discover_project_version(root) or "0.0.0"

    cmp_res = compare_versions(target_version, current_version)
    if cmp_res < 0:
        raise UpgradeError(
            f"Downgrades are not supported (current: {current_version}, target: {target_version})."
        )
    if cmp_res == 0:
        return {
            "status": "already_up_to_date",
            "current_version": current_version,
            "target_version": target_version,
            "message": f"Project is already on version {current_version}.",
        }

    # 1. Fetch and verify target version artifact
    artifact_path = fetch_version_artifact(target_version, mirror_dir=mirror_dir)

    if dry_run:
        return {
            "status": "dry_run_success",
            "current_version": current_version,
            "target_version": target_version,
            "artifact": str(artifact_path),
        }

    # 2. Transactional Staging
    ot_dir = root / ".ot"
    config_file = ot_dir / "config.json"
    local_config_file = ot_dir / "config.local.json"

    with tempfile.TemporaryDirectory() as staging_dir:
        staging = Path(staging_dir)
        staged_ot = staging / ".ot"
        # Copy current .ot to staging
        shutil.copytree(ot_dir, staged_ot)

        # 3. Run sequential schema migrations and update version in staged config.json & config.local.json
        migration_steps: List[str] = []
        staged_config_path = staged_ot / "config.json"
        if staged_config_path.is_file():
            cfg_data = load_json_file(staged_config_path)
            cfg_data, steps = run_config_migrations(cfg_data, update_version_key=True)
            migration_steps.extend(steps)
            cfg_data.setdefault("system", {})["toolVersion"] = target_version
            staged_config_path.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")

        staged_local_path = staged_ot / "config.local.json"
        if staged_local_path.is_file():
            local_data = load_json_file(staged_local_path)
            local_data, local_steps = run_config_migrations(local_data, update_version_key=False)
            migration_steps.extend(local_steps)
            staged_local_path.write_text(json.dumps(local_data, indent=2), encoding="utf-8")

        # Ensure any custom configured paths outside .ot exist in staging before template upgrade & validation
        try:
            staged_cfg = load_config(staging)
            for d in (staged_cfg.tasks_dir, staged_cfg.meetings_dir, staged_cfg.templates_dir):
                d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        # 4. Install new binary in staged .ot/bin/<target_version>/
        install_artifact_to_project_bin(staging, target_version, artifact_path)

        # 5. Non-destructively upgrade templates in staging
        upgrade_project_templates(staging)

        # 6. Validate staged project state
        validator = Validator(staging)
        diags = validator.validate_all()
        from ot.validation import Severity
        errors = [d for d in diags if d.severity == Severity.ERROR]
        if errors:
            err_msgs = "; ".join(e.message for e in errors)
            raise UpgradeError(f"Upgrade validation failed: {err_msgs}")

        # 7. Atomically commit staged changes into real .ot/
        if staged_config_path.is_file():
            shutil.copy2(staged_config_path, config_file)
        if staged_local_path.is_file():
            shutil.copy2(staged_local_path, local_config_file)

        # Update .ot/bin/<target_version>/ while preserving older versions
        install_artifact_to_project_bin(root, target_version, artifact_path)

        # Upgrade project templates in real project root
        template_changes = upgrade_project_templates(root)

        # Update project wrapper scripts (oat / oat.bat) and remove legacy otw / otw.bat
        oat_sh = root / "oat"
        oat_sh.write_text(WRAPPER_SCRIPT_SH, encoding="utf-8")
        oat_sh.chmod(0o755)
        oat_bat = root / "oat.bat"
        oat_bat.write_text(WRAPPER_SCRIPT_BAT, encoding="utf-8")
        for legacy_name in ("otw", "otw.bat"):
            legacy_path = root / legacy_name
            if legacy_path.is_file():
                legacy_path.unlink()

    msg = f"Successfully upgraded Open Tasks from {current_version} to {target_version}."
    if template_changes["preserved_with_default"]:
        preserved_list = ", ".join(template_changes["preserved_with_default"])
        msg += f" Preserved customized template(s) ({preserved_list}); new defaults written to .default files."

    return {
        "status": "upgraded",
        "previous_version": current_version,
        "new_version": target_version,
        "schema_migrations": migration_steps,
        "template_changes": template_changes,
        "message": msg,
    }
