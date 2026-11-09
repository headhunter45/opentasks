"""Global launcher for Open Tasks."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import List, Optional

from ot.config import load_config, load_json_file
from ot.discovery import find_project_root


def find_project_binary(project_root: Path) -> Optional[Path]:
    """Find the project-installed Open Tasks executable beneath .ot/bin/."""
    candidates = [
        project_root / ".ot" / "bin" / "ot.zipapp",
        project_root / ".ot" / "bin" / "ot.py",
        project_root / ".ot" / "bin" / "ot",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def get_configured_version(project_root: Path) -> Optional[str]:
    """Read system.toolVersion from .ot/config.json."""
    config_file = project_root / ".ot" / "config.json"
    if not config_file.is_file():
        return None
    try:
        data = load_json_file(config_file)
        return data.get("system", {}).get("toolVersion")
    except Exception:
        return None


def launch_project_binary(binary_path: Path, args: List[str]) -> int:
    """Execute the project-installed binary with python3."""
    cmd = [sys.executable, str(binary_path), *args]
    env = dict(os.environ)
    env["OT_PROJECT_BINARY_ACTIVE"] = "1"
    res = subprocess.run(cmd, env=env)
    return res.returncode


def _is_running_binary(binary_path: Path) -> bool:
    """Return True if the current process is already executing `binary_path`."""
    try:
        target = binary_path.resolve()
    except OSError:
        return False

    argv0 = sys.argv[0] if sys.argv else ""
    if argv0:
        try:
            if Path(argv0).resolve() == target:
                return True
        except OSError:
            pass

    ot_module = sys.modules.get("ot")
    if ot_module is not None:
        loader = getattr(ot_module, "__loader__", None)
        archive = getattr(loader, "archive", None)
        if archive:
            try:
                if Path(archive).resolve() == target:
                    return True
            except OSError:
                pass
    return False


def _extract_project_dir(args: List[str]) -> Optional[str]:
    """Extract -C / --project-dir from CLI args if present."""
    for i, arg in enumerate(args):
        if arg in ("-C", "--project-dir") and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith("--project-dir="):
            return arg.split("=", 1)[1]
    return None


def run_launcher(args: Optional[List[str]] = None, start_dir: Optional[Path | str] = None) -> int:
    """Main entry point for the global `ot` launcher."""
    if args is None:
        args = sys.argv[1:]

    # If already delegated into a project binary, execute CLI directly
    if os.environ.get("OT_PROJECT_BINARY_ACTIVE") == "1":
        from ot.cli import main as cli_main
        return cli_main(args)

    effective_start_dir = start_dir if start_dir is not None else _extract_project_dir(args)

    # Intercept top-level --version or version command
    if args and args[0] in ("--version", "-V", "version"):
        from ot import __version__
        print(f"Open Tasks Launcher v{__version__}")
        proj_root = find_project_root(effective_start_dir)
        if proj_root:
            cfg_v = get_configured_version(proj_root)
            bin_p = find_project_binary(proj_root)
            print(f"Project root:       {proj_root}")
            print(f"Configured version: {cfg_v or 'Not specified (using default)'}")
            print(f"Installed binary:   {bin_p or 'None (using fallback implementation)'}")
        return 0

    proj_root = find_project_root(effective_start_dir)

    # If initializing or no project exists yet, run directly via core cli
    if not proj_root or (args and args[0] == "init"):
        from ot.cli import main as cli_main
        return cli_main(args)

    # Check for project-installed implementation beneath .ot/bin/
    project_bin = find_project_binary(proj_root)
    if project_bin and not _is_running_binary(project_bin):
        return launch_project_binary(project_bin, args)

    # Fallback to local / environment package implementation
    from ot.cli import main as cli_main
    return cli_main(args)


if __name__ == "__main__":
    sys.exit(run_launcher())
