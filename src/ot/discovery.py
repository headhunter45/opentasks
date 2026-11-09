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


@functools.lru_cache(maxsize=4)
def is_hg_available() -> bool:
    """Check if hg (Mercurial) binary is available on PATH."""
    try:
        res = subprocess.run(["hg", "--version"], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


def parse_hg_username(raw_username: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Parse Mercurial ui.username ('Name <email@domain>' or 'Name') into (name, email)."""
    if not raw_username or not raw_username.strip():
        return None, None
    import re

    val = raw_username.strip()
    m = re.match(r"^([^<]*?)<([^>]+)>\s*$", val)
    if m:
        name = m.group(1).strip() or None
        email = m.group(2).strip() or None
        return name, email
    return val, None


def get_hg_config(key: str, repo_dir: Optional[Path | str] = None) -> Optional[str]:
    """Query Mercurial configuration for a specific key (e.g. 'ui.username', 'ui.editor')."""
    if is_hg_available():
        try:
            cmd = ["hg", "config", key]
            cwd = str(repo_dir) if repo_dir else None
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
            if res.returncode == 0:
                val = res.stdout.strip()
                if val:
                    return val
        except Exception:
            pass

    # Fallback: check local .hg/hgrc if repo_dir is inside a Mercurial repository
    if repo_dir and "." in key:
        section, option = key.split(".", 1)
        vcs_type, vcs_root = find_vcs_root(repo_dir)
        if vcs_type == "hg" and vcs_root:
            hgrc = vcs_root / ".hg" / "hgrc"
            if hgrc.is_file():
                try:
                    import configparser

                    cp = configparser.ConfigParser()
                    cp.read(hgrc, encoding="utf-8")
                    if cp.has_option(section, option):
                        val = cp.get(section, option).strip()
                        return val if val else None
                except Exception:
                    pass
    return None


def get_hg_identity(repo_dir: Optional[Path | str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Get (name, email) from Mercurial configuration (ui.username)."""
    raw = get_hg_config("ui.username", repo_dir)
    return parse_hg_username(raw)


def get_hg_editor(repo_dir: Optional[Path | str] = None) -> Optional[str]:
    """Get preferred editor from Mercurial configuration (ui.editor)."""
    return get_hg_config("ui.editor", repo_dir)


def check_vcs_safety(start_dir: Optional[Path | str] = None) -> Tuple[bool, Optional[str]]:
    """Inspect the containing Git or Mercurial repository for active unsafe states.

    Returns (is_safe, reason_if_unsafe).
    """
    vcs_type, vcs_root = find_vcs_root(start_dir)
    if not vcs_root:
        return True, None

    if vcs_type == "git":
        git_dir = vcs_root / ".git"
        if git_dir.is_dir():
            git_unsafe_markers = [
                ("MERGE_HEAD", "Git merge in progress (.git/MERGE_HEAD)"),
                ("rebase-merge", "Git rebase in progress (.git/rebase-merge)"),
                ("rebase-apply", "Git rebase/am in progress (.git/rebase-apply)"),
                ("CHERRY_PICK_HEAD", "Git cherry-pick in progress (.git/CHERRY_PICK_HEAD)"),
                ("REVERT_HEAD", "Git revert in progress (.git/REVERT_HEAD)"),
                ("BISECT_LOG", "Git bisect in progress (.git/BISECT_LOG)"),
                ("index.lock", "Active Git lock file present (.git/index.lock)"),
            ]
            for marker, desc in git_unsafe_markers:
                if (git_dir / marker).exists():
                    return (
                        False,
                        f"Repository is in an unsafe VCS state: {desc}. Complete or abort the VCS operation, or pass --force.",
                    )

    elif vcs_type == "hg":
        hg_dir = vcs_root / ".hg"
        if hg_dir.is_dir():
            hg_unsafe_markers = [
                ("merge", "Mercurial merge in progress (.hg/merge)"),
                ("rebasestate", "Mercurial rebase in progress (.hg/rebasestate)"),
                ("histedit-state", "Mercurial histedit in progress (.hg/histedit-state)"),
                ("wlock", "Active Mercurial working-directory lock present (.hg/wlock)"),
            ]
            for marker, desc in hg_unsafe_markers:
                if (hg_dir / marker).exists():
                    return (
                        False,
                        f"Repository is in an unsafe VCS state: {desc}. Complete or abort the VCS operation, or pass --force.",
                    )

    return True, None


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


