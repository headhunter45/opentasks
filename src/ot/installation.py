"""Project initialization and tool installation for Open Tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import zipfile
from typing import Any, Dict, Optional

from ot import __version__ as DEFAULT_LAUNCHER_VERSION
from ot.config import DEFAULT_CONFIG
from ot.packaging import ReleaseManifest, build_zipapp_artifact, compute_sha256
from ot.templates import install_default_templates
from ot.version import is_valid_version


WRAPPER_SCRIPT_SH = """#!/usr/bin/env bash
set -euo pipefail
PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="${PROJ_ROOT}/.ot/bin/ot.zipapp"

if [ -f "$BIN" ]; then
    exec python3 "$BIN" "$@"
else
    exec ot "$@"
fi
"""

WRAPPER_SCRIPT_BAT = """@echo off
set "PROJ_ROOT=%~dp0"
set "BIN=%PROJ_ROOT%.ot\\bin\\ot.zipapp"

if exist "%BIN%" (
    python "%BIN%" %*
) else (
    ot %*
)
"""


def _running_zipapp() -> Optional[Path]:
    """Return the on-disk archive if ``ot`` is executing from inside a .zipapp.

    When distributed as a .zipapp (e.g. the globally installed
    ``~/.local/bin/ot``, or a project's ``.ot/bin/ot.zipapp``), the ``ot``
    modules are served by ``zipimport`` and there is no ``src/ot`` tree on
    disk beside the binary. Detecting this lets ``init`` install the project
    binary by copying the running artifact instead of trying to rebuild from a
    source tree that isn't present next to it.
    """
    import sys

        # A packaged ``ot`` is served by ``zipimport.ZipImporter``, whose
        # ``.archive`` attribute is the on-disk archive path we can copy.
    ot_module = sys.modules.get("ot")
    if ot_module is not None:
        loader = getattr(ot_module, "__loader__", None)
        archive = getattr(loader, "archive", None)
        if archive:
            return Path(archive)

        # The program we launched as, if it is a zip/zipapp (content check, so the
    # extension/name is irrelevant: covers the extensionless global `ot`).
    argv0 = sys.argv[0] if sys.argv else ""
    if argv0 and os.path.isfile(argv0) and zipfile.is_zipfile(argv0):
        return Path(argv0)
    return None


def _install_running_artifact(
    archive: Path, out_zipapp: Path, version: str
) -> Path:
    """Copy the running .zipapp into the project's .ot/bin/ and write its manifest."""
    archive = Path(archive)
    out_zipapp = Path(out_zipapp)

    shutil.copy2(archive, out_zipapp)
    if os.access(archive, os.X_OK):
        out_zipapp.chmod(0o755)

        # Mirror the manifest shape build_zipapp_artifact writes so that
    # discover_installed_version / version validation behave identically.
    from ot.models import now_iso  # local import: avoid a module-level cycle
    manifest = ReleaseManifest(
        version=version,
        build_date=now_iso(),
        sha256=compute_sha256(out_zipapp),
        artifact_name=out_zipapp.name,
    )
    manifest_path = out_zipapp.parent / f"{out_zipapp.stem}-manifest.json"
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")
    return out_zipapp


def install_project_binary(
    project_root: Path,
    version: str,
    src_dir: Optional[Path | str] = None,
) -> Path:
    """Install Open Tasks executable zipapp and manifest into .ot/bin/.

    Resolution order:
      1. An explicit ``src_dir`` builds the artifact from that source tree.
      2. If ``ot`` is running from a distributed .zipapp, that very artifact is
         copied into the project — the running binary *is* the source, so no
         source tree needs to exist beside it.
      3. Otherwise (a developer source checkout) the local ``src/ot`` tree is
         discovered and built.
    """
    bin_dir = project_root / ".ot" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    out_zipapp = bin_dir / "ot.zipapp"

    # 1. Explicit source directory always wins: build from source.
    if src_dir:
        build_zipapp_artifact(src_dir, out_zipapp, version)
        return out_zipapp

    # 2. Running as a distributed .zipapp: copy the running artifact itself.
    archive = _running_zipapp()
    if archive is not None:
        return _install_running_artifact(archive, out_zipapp, version)

    # 3. Developer source checkout: locate the package and build.
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "ot").is_dir():
        src_dir = candidate
    else:
        src_dir = Path(__file__).resolve().parent.parent.parent / "src"
    if not (src_dir / "ot").is_dir():
        raise FileNotFoundError(
            f"Cannot locate the 'ot' source package to build a project binary "
            f"from {src_dir}. Install 'ot' so the global binary ships as a "
            f".zipapp, or pass --src-dir."
        )

    build_zipapp_artifact(src_dir, out_zipapp, version)
    return out_zipapp


def _ensure_gitignore_entry(project_root: Path) -> None:
    """Ensure .ot/bin/ is ignored in the project's .gitignore file."""
    gitignore_path = project_root / ".gitignore"
    accepted_entries = {
        ".ot/bin",
        ".ot/bin/",
        ".ot/bin/*",
        "/.ot/bin",
        "/.ot/bin/",
        "/.ot/bin/*",
    }
    if gitignore_path.is_file():
        content = gitignore_path.read_text(encoding="utf-8")
        existing_lines = {
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        if existing_lines & accepted_entries:
            return
        prefix = "" if (not content or content.endswith("\n")) else "\n"
        gitignore_path.write_text(f"{content}{prefix}.ot/bin/\n", encoding="utf-8")
    else:
        gitignore_path.write_text(".ot/bin/\n", encoding="utf-8")


def init_project(
    target_dir: Path | str,
    project_name: Optional[str] = None,
    version: Optional[str] = None,
    description: str = "",
    install_binary: bool = True,
    create_wrappers: bool = True,
) -> Dict[str, Any]:
    """Initialize a new Open Tasks project in target_dir."""
    root = Path(target_dir).resolve()
    ot_dir = root / ".ot"
    ot_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create directory structure
    for sub in ["tasks", "meetings", "templates", "bin"]:
        (ot_dir / sub).mkdir(parents=True, exist_ok=True)

    # Ensure .ot/bin/ is ignored by git
    _ensure_gitignore_entry(root)

    tool_version = version or DEFAULT_LAUNCHER_VERSION
    if not is_valid_version(tool_version):
        raise ValueError(f"Invalid version for initialization: '{tool_version}'")

    proj_name = project_name or root.name

    # 2. Generate .ot/config.json
    config_data = json.loads(json.dumps(DEFAULT_CONFIG))
    config_data["system"]["toolVersion"] = tool_version
    config_data["project"]["name"] = proj_name
    config_data["project"]["description"] = description

    config_path = ot_dir / "config.json"
    if not config_path.exists():
        config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    # 3. Install default templates
    templates_count = install_default_templates(root)

    # 4. Install project binary
    binary_path = None
    if install_binary:
        binary_path = install_project_binary(root, tool_version)

    # 5. Create wrapper scripts
    if create_wrappers:
        otw = root / "otw"
        if not otw.exists():
            otw.write_text(WRAPPER_SCRIPT_SH, encoding="utf-8")
            otw.chmod(0o755)
        otw_bat = root / "otw.bat"
        if not otw_bat.exists():
            otw_bat.write_text(WRAPPER_SCRIPT_BAT, encoding="utf-8")

    return {
        "project_root": root,
        "name": proj_name,
        "version": tool_version,
        "templates_count": templates_count,
        "binary_path": binary_path,
    }
