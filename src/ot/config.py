"""Configuration loading, resolution, and validation for Open Tasks."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ot.discovery import (
    find_project_root,
    get_git_editor,
    get_git_identity,
    get_system_editor,
    get_system_identity,
)

# Protected configuration keys that define shared project-level conventions.
# These should reside in .ot/config.json and not in local overrides (.ot/config.local.json).
PROTECTED_CONFIG_KEYS: Set[str] = {
    "system",
    "system.configSchemaVersion",
    "project",
    "project.name",
    "project.description",
    "workItem.types",
    "workItem.statuses",
    "workItem.sizes",
    "meeting.types",
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "system": {
        "configSchemaVersion": 1,
    },
    "project": {
        "name": "Open Tasks Project",
        "description": "",
    },
    "user": {
        "name": None,
        "email": None,
        "editor": None,
    },
    "workItem": {
        "types": {
            "task": {"label": "Task", "description": "Standard work unit"},
            "bug": {"label": "Bug", "description": "Defect requiring fix"},
            "feature": {"label": "Feature", "description": "New functionality"},
            "epic": {"label": "Epic", "description": "High level initiative"},
            "spike": {"label": "Spike", "description": "Time-boxed research"},
            "chore": {"label": "Chore", "description": "Maintenance or refactoring"},
        },
        "statuses": {
            "triage": {"label": "Triage", "description": "Needs review"},
            "planned": {"label": "Planned", "description": "Ready to work"},
            "in_progress": {"label": "In Progress", "description": "Currently active"},
            "blocked": {"label": "Blocked", "description": "Waiting on dependency"},
            "completed": {"label": "Completed", "description": "Work finished"},
            "closed": {"label": "Closed", "description": "Archived or cancelled"},
        },
        "sizes": {
            "small": {"label": "Small", "description": "1-2 days"},
            "medium": {"label": "Medium", "description": "1 week"},
            "large": {"label": "Large", "description": "Multi-week"},
        },
    },
    "meeting": {
        "types": {
            "grooming": {"label": "Grooming", "description": "Backlog refinement"},
            "planning": {"label": "Planning", "description": "Sprint planning"},
            "retrospective": {"label": "Retrospective", "description": "Sprint retro"},
            "ideation": {"label": "Ideation", "description": "Brainstorming"},
        }
    },
}


def load_json_file(path: Path | str) -> Dict[str, Any]:
    """Load and parse a JSON configuration file. Returns empty dict if file does not exist."""
    p = Path(path).expanduser()
    if not p.is_file():
        return {}
    try:
        content = p.read_text(encoding="utf-8").strip()
        if not content:
            return {}
        data = json.loads(content)
        if isinstance(data, dict):
            return data
        return {}
    except Exception as e:
        raise ValueError(f"Failed to parse JSON from {p}: {e}") from e


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge override dictionary into base dictionary."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_flattened_keys(d: Dict[str, Any], prefix: str = "") -> Set[str]:
    """Get all flattened dot-notation keys from a nested dictionary."""
    keys = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        keys.add(full_key)
        if isinstance(v, dict):
            keys.update(get_flattened_keys(v, full_key))
    return keys


def find_protected_key_violations(local_config: Dict[str, Any]) -> List[str]:
    """Find any protected keys defined in a local or user override config."""
    violations = []
    flat_keys = get_flattened_keys(local_config)
    for protected in PROTECTED_CONFIG_KEYS:
        if protected in flat_keys:
            violations.append(protected)
    return violations


class Config:
    """Resolved configuration object for an Open Tasks project."""

    def __init__(
        self,
        data: Dict[str, Any],
        project_root: Optional[Path] = None,
        warnings: Optional[List[str]] = None,
    ):
        self._data = data
        self.project_root = project_root
        self.warnings: List[str] = warnings or []

    @property
    def raw(self) -> Dict[str, Any]:
        return self._data

    def get(self, key_path: str, default: Any = None) -> Any:
        """Retrieve a value using dot notation (e.g. 'workItem.types.bug.label')."""
        parts = key_path.split(".")
        current: Any = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current if current is not None else default

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    @property
    def user_name(self) -> str:
        return self.get("user.name") or "Anonymous"

    @property
    def user_email(self) -> Optional[str]:
        return self.get("user.email")

    @property
    def editor(self) -> str:
        return self.get("user.editor") or "nano"

    @property
    def output_width(self) -> Optional[int]:
        val = self.get("user.outputWidth") or self.get("output.width")
        if val is not None:
            try:
                return int(val)
            except (TypeError, ValueError):
                return None
        return None

    @property
    def work_item_types(self) -> Dict[str, Any]:
        return self.get("workItem.types", {})

    @property
    def work_item_statuses(self) -> Dict[str, Any]:
        return self.get("workItem.statuses", {})

    @property
    def work_item_sizes(self) -> Dict[str, Any]:
        return self.get("workItem.sizes", {})


def load_config(start_dir: Optional[Path | str] = None) -> Config:
    """Load and resolve configuration according to the precedence rules:
    1. .ot/config.local.json
    2. .ot/config.json
    3. ~/.ot/config.json
    4. VCS (git config user.name, user.email, core.editor)
    5. Environment variables (OT_USER, USER, EMAIL, EDITOR, VISUAL)
    6. System Defaults
    """
    project_root = find_project_root(start_dir)
    warnings: List[str] = []

    # 1. System defaults
    resolved = dict(DEFAULT_CONFIG)

    # 2. Global user config (~/.ot/config.json)
    global_config_path = Path("~/.ot/config.json").expanduser()
    global_config = load_json_file(global_config_path)
    if global_config:
        resolved = deep_merge(resolved, global_config)

    # 3. Project config (.ot/config.json)
    if project_root:
        proj_config_path = project_root / ".ot" / "config.json"
        proj_config = load_json_file(proj_config_path)
        if proj_config:
            resolved = deep_merge(resolved, proj_config)

        # 4. Project local config (.ot/config.local.json)
        local_config_path = project_root / ".ot" / "config.local.json"
        local_config = load_json_file(local_config_path)
        if local_config:
            violations = find_protected_key_violations(local_config)
            for v in violations:
                warnings.append(f"Protected configuration key '{v}' is improperly overridden in {local_config_path.name}")
            resolved = deep_merge(resolved, local_config)

    # 5. VCS & Environment fallbacks for user identity and editor
    user_dict = resolved.setdefault("user", {})
    if not user_dict.get("name") or not user_dict.get("email"):
        git_name, git_email = get_git_identity(project_root)
        sys_name, sys_email = get_system_identity()
        if not user_dict.get("name"):
            user_dict["name"] = git_name or sys_name
        if not user_dict.get("email"):
            user_dict["email"] = git_email or sys_email

    if not user_dict.get("editor"):
        git_editor = get_git_editor(project_root)
        sys_editor = get_system_editor()
        user_dict["editor"] = git_editor or sys_editor

    return Config(resolved, project_root=project_root, warnings=warnings)
