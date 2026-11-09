"""Project and VCS discovery for Open Tasks."""

from __future__ import annotations

import functools
import os
from pathlib import Path
import subprocess
from typing import Optional, Tuple


def find_project_root(start_dir: Optional[Path | str] = None) -> Optional[Path]:
    """Find the Open Tasks project root containing `.ot`.

    Traverses upwards from `start_dir` (defaulting to cwd).
    Also checks OPEN_TASKS_ROOT or OT_ROOT environment variables if set.
    """
    env_root = os.getenv("OPEN_TASKS_ROOT") or os.getenv("OT_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        if (p / ".ot").is_dir():
            return p

    current = Path(start_dir or Path.cwd()).resolve()
    # If a file was passed, start from its parent
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        if (parent / ".ot").is_dir():
            return parent

    return None


def find_vcs_root(start_dir: Optional[Path | str] = None) -> Tuple[Optional[str], Optional[Path]]:
    """Find the root of the containing Version Control System (.git or .hg).

    Returns:
        (vcs_type, root_path) where vcs_type is 'git', 'hg', or None.
    """
    current = Path(start_dir or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent

    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return "git", parent
        if (parent / ".hg").exists():
            return "hg", parent

    return None, None


def discover_root(start_dir: Optional[Path | str] = None, allow_fallback: bool = True) -> Path:
    """Discover the project root using standard priority:
    1. .ot directory
    2. .git root (if .ot not yet created)
    3. .hg root
    4. Current directory (if allow_fallback is True)
    """
    proj_root = find_project_root(start_dir)
    if proj_root:
        return proj_root

    vcs_type, vcs_root = find_vcs_root(start_dir)
    if vcs_root:
        return vcs_root

    if allow_fallback:
        current = Path(start_dir or Path.cwd()).resolve()
        return current.parent if current.is_file() else current

    raise FileNotFoundError("Could not locate Open Tasks project root (.ot).")


@functools.lru_cache(maxsize=4)
def is_git_available() -> bool:
    """Check if git binary is available on PATH."""
    try:
        res = subprocess.run(["git", "--version"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


@functools.lru_cache(maxsize=64)
def get_git_config(key: str, repo_dir: Optional[Path | str] = None) -> Optional[str]:
    """Query git config for a specific key."""
    if not is_git_available():
        return None
    try:
        cmd = ["git", "config", key]
        cwd = str(repo_dir) if repo_dir else None
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            val = res.stdout.strip()
            return val if val else None
    except Exception:
        pass
    return None


def get_git_identity(repo_dir: Optional[Path | str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Get (name, email) from git configuration."""
    name = get_git_config("user.name", repo_dir)
    email = get_git_config("user.email", repo_dir)
    return name, email


def get_git_editor(repo_dir: Optional[Path | str] = None) -> Optional[str]:
    """Get preferred editor from git configuration (core.editor)."""
    return get_git_config("core.editor", repo_dir)


def get_system_identity() -> Tuple[Optional[str], Optional[str]]:
    """Get identity fallback when no VCS is present or configured.

    Checks EMAIL, USER, USERNAME, LOGNAME, and getpass.getuser().
    """
    import getpass

    email = os.getenv("EMAIL")
    name = os.getenv("OT_USER") or os.getenv("USER") or os.getenv("USERNAME") or os.getenv("LOGNAME")
    if not name:
        try:
            name = getpass.getuser()
        except Exception:
            name = "Anonymous"
    return name, email


def get_system_editor() -> str:
    """Get fallback editor when no VCS or configuration specifies one."""
    editor = os.getenv("EDITOR") or os.getenv("VISUAL")
    if editor:
        return editor
    import sys
    if sys.platform == "win32":
        return "notepad.exe"
    return "nano"


