"""Validation, diagnostic error reporting, and automatic repair framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ot.config import (
    Config,
    DEFAULT_CONFIG,
    PROTECTED_CONFIG_KEYS,
    find_protected_key_violations,
    get_global_config_path,
    load_config,
    load_json_file,
    relocate_protected_keys,
)
from ot.discovery import find_project_root
from ot.identifiers import is_valid_uuid
from ot.models import WorkItem
from ot.parser import read_work_item, write_work_item
from ot.scanner import RepositoryScanner, WorkItemIndex


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Diagnostic:
    """A single diagnostic issue discovered during validation."""

    severity: Severity
    category: str  # 'config', 'work_item', 'filesystem', 'vcs', 'merge_conflict'
    message: str
    file_path: Optional[Path] = None
    item_id: Optional[str] = None
    is_fixable: bool = False
    repair_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "file_path": str(self.file_path) if self.file_path else None,
            "item_id": self.item_id,
            "is_fixable": self.is_fixable,
            "repair_action": self.repair_action,
        }


class Validator:
    """Validates project state and generates diagnostics."""

    def __init__(self, project_root: Optional[Path | str] = None):
        self.project_root = find_project_root(project_root)
        self.config: Optional[Config] = None
        if self.project_root:
            try:
                self.config = load_config(self.project_root)
            except Exception:
                self.config = Config(dict(DEFAULT_CONFIG), project_root=self.project_root)

    def validate_all(self) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if not self.project_root:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="filesystem",
                    message="No Open Tasks project root (.ot) discovered.",
                    is_fixable=False,
                )
            )
            return diagnostics

        diagnostics.extend(self.validate_filesystem())
        diagnostics.extend(self.validate_configuration())
        diagnostics.extend(self.validate_work_items())
        return diagnostics

    def validate_filesystem(self) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if not self.project_root:
            return diagnostics

        required_dirs = [
            (".ot", "Canonical tool root", True),
            (".ot/tasks", "WorkItem repository", True),
            (".ot/templates", "Templates directory", True),
            (".ot/meetings", "Meetings directory", True),
        ]

        for rel_path, desc, fixable in required_dirs:
            p = self.project_root / rel_path
            if not p.exists():
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        category="filesystem",
                        message=f"Missing required directory: {rel_path} ({desc})",
                        file_path=p,
                        is_fixable=fixable,
                        repair_action=f"Create directory {rel_path}",
                    )
                )

        return diagnostics

    def validate_configuration(self) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if not self.project_root:
            return diagnostics

        layer_schema_versions: Dict[str, Any] = {}

        # 1. Global user configuration (~/.ot/config.json or $OT_USER_HOME/config.json)
        global_cfg_path = get_global_config_path()
        if global_cfg_path.is_file():
            try:
                global_data = load_json_file(global_cfg_path)
                global_schema = global_data.get("system", {}).get("configSchemaVersion")
                if global_schema is not None:
                    layer_schema_versions["global"] = global_schema
                    if global_schema != 1:
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.ERROR,
                                category="config",
                                message=f"Unsupported configuration schema version in global config: {global_schema}",
                                file_path=global_cfg_path,
                                is_fixable=False,
                            )
                        )
                violations = find_protected_key_violations(global_data)
                for v in violations:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARNING,
                            category="config",
                            message=f"Protected configuration key '{v}' is improperly placed in global config ({global_cfg_path.name}).",
                            file_path=global_cfg_path,
                            is_fixable=False,
                        )
                    )
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="config",
                        message=f"Failed to parse global config {global_cfg_path.name}: {e}",
                        file_path=global_cfg_path,
                        is_fixable=False,
                    )
                )

        # 2. Local project configuration (.ot/config.local.json)
        local_cfg_path = self.project_root / ".ot" / "config.local.json"
        if local_cfg_path.is_file():
            try:
                local_data = load_json_file(local_cfg_path)
                local_schema = local_data.get("system", {}).get("configSchemaVersion")
                if local_schema is not None:
                    layer_schema_versions["local"] = local_schema
                    if local_schema != 1:
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.ERROR,
                                category="config",
                                message=f"Unsupported configuration schema version in {local_cfg_path.name}: {local_schema}",
                                file_path=local_cfg_path,
                                is_fixable=False,
                            )
                        )
                violations = find_protected_key_violations(local_data)
                for v in violations:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARNING,
                            category="config",
                            message=f"Protected configuration key '{v}' is improperly placed in {local_cfg_path.name}.",
                            file_path=local_cfg_path,
                            is_fixable=True,
                            repair_action=f"Move protected key '{v}' to .ot/config.json",
                        )
                    )
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="config",
                        message=f"Failed to parse {local_cfg_path.name}: {e}",
                        file_path=local_cfg_path,
                        is_fixable=False,
                    )
                )

        # 3. Canonical project configuration (.ot/config.json)
        proj_cfg_path = self.project_root / ".ot" / "config.json"
        if proj_cfg_path.is_file():
            try:
                proj_data = load_json_file(proj_cfg_path)
                schema_version = proj_data.get("system", {}).get("configSchemaVersion")
                if schema_version is not None:
                    layer_schema_versions["project"] = schema_version
                    if schema_version != 1:
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.ERROR,
                                category="config",
                                message=f"Unsupported configuration schema version: {schema_version}",
                                file_path=proj_cfg_path,
                                is_fixable=False,
                            )
                        )
            except Exception as e:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="config",
                        message=f"Failed to parse {proj_cfg_path.name}: {e}",
                        file_path=proj_cfg_path,
                        is_fixable=False,
                    )
                )

        # 4. Cross-layer configSchemaVersion compatibility check
        if len(set(layer_schema_versions.values())) > 1:
            details = ", ".join(f"{layer}={ver}" for layer, ver in sorted(layer_schema_versions.items()))
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="config",
                    message=f"Configuration schema version mismatch across layers ({details}).",
                    file_path=proj_cfg_path,
                    is_fixable=False,
                )
            )

        from ot.version import validate_project_version
        is_v_valid, v_err = validate_project_version(self.project_root)
        if not is_v_valid and v_err:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="version",
                    message=v_err,
                    file_path=proj_cfg_path,
                    is_fixable=False,
                )
            )

        return diagnostics


    def validate_single_work_item(
        self,
        item: WorkItem,
        existing_items: Optional[List[WorkItem]] = None,
    ) -> List[Diagnostic]:
        """Validate a single WorkItem (e.g. before saving interactive edits)."""
        diagnostics: List[Diagnostic] = []
        item_file = item.path or Path("edited-work-item.md")

        valid_types = set(self.config.work_item_types.keys()) if self.config else set()
        valid_statuses = set(self.config.work_item_statuses.keys()) if self.config else set()
        valid_sizes = set(self.config.work_item_sizes.keys()) if self.config else set()

        if existing_items is None and self.project_root:
            scanner = RepositoryScanner(self.project_root)
            existing_items = scanner.scan_tasks_directory()
        existing_items = existing_items or []

        other_uuids = {
            other.id: (other.path or Path("unknown"))
            for other in existing_items
            if other.path is None or item.path is None or other.path.resolve() != item.path.resolve()
        }
        all_known_uuids = set(other_uuids.keys()) | ({item.id} if item.id else set())

        if not item.id or not is_valid_uuid(item.id):
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"WorkItem has missing or invalid UUID: '{item.id}'",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )
        elif item.id in other_uuids:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"Duplicate UUID '{item.id}' detected (already used in {other_uuids[item.id]})",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if not item.title or not item.title.strip():
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message="WorkItem title cannot be empty.",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if valid_types and item.type not in valid_types:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"Invalid type '{item.type}'. Expected one of: {', '.join(valid_types)}",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if valid_statuses and item.status not in valid_statuses:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"Invalid status '{item.status}'. Expected one of: {', '.join(valid_statuses)}",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if valid_sizes and item.meta.size and item.meta.size not in valid_sizes:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"Invalid size '{item.meta.size}'. Expected one of: {', '.join(valid_sizes)}",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if item.id in item.dependencies or item.parent_id == item.id:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"WorkItem '{item.title}' cannot depend on or parent itself.",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        if item.parent_id and item.parent_id != item.id and item.parent_id not in all_known_uuids:
            diagnostics.append(
                Diagnostic(
                    severity=Severity.ERROR,
                    category="work_item",
                    message=f"Broken parent reference: parent UUID '{item.parent_id}' does not exist.",
                    file_path=item_file,
                    item_id=item.id,
                    is_fixable=False,
                )
            )

        for dep_id in item.dependencies:
            if dep_id != item.id and dep_id not in all_known_uuids:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="work_item",
                        message=f"Broken dependency reference: target UUID '{dep_id}' does not exist.",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )

        return diagnostics

    def validate_work_items(self) -> List[Diagnostic]:
        diagnostics: List[Diagnostic] = []
        if not self.project_root:
            return diagnostics

        tasks_dir = self.project_root / ".ot" / "tasks"
        if not tasks_dir.is_dir():
            return diagnostics

        scanner = RepositoryScanner(self.project_root)
        items = scanner.scan_tasks_directory()

        valid_types = set(self.config.work_item_types.keys()) if self.config else set()
        valid_statuses = set(self.config.work_item_statuses.keys()) if self.config else set()
        valid_sizes = set(self.config.work_item_sizes.keys()) if self.config else set()

        seen_uuids: Dict[str, Path] = {}

        for item in items:
            item_file = item.path or Path("unknown")

            # Check merge conflict markers in file
            if item.path and item.path.is_file():
                try:
                    content = item.path.read_text(encoding="utf-8")
                    if "<<<<<<<" in content or ">>>>>>>" in content:
                        diagnostics.append(
                            Diagnostic(
                                severity=Severity.ERROR,
                                category="merge_conflict",
                                message=f"Unresolved merge conflict markers found in {item.path.name}",
                                file_path=item.path,
                                item_id=item.id,
                                is_fixable=False,
                            )
                        )
                except Exception:
                    pass

            # UUID checks
            if not item.id or not is_valid_uuid(item.id):
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="work_item",
                        message=f"WorkItem has missing or invalid UUID: '{item.id}'",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )
            elif item.id in seen_uuids:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="work_item",
                        message=f"Duplicate UUID '{item.id}' detected in {item_file} (first seen in {seen_uuids[item.id]})",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )
            else:
                seen_uuids[item.id] = item_file

            # Type validation
            if valid_types and item.type not in valid_types:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="work_item",
                        message=f"Invalid type '{item.type}'. Expected one of: {', '.join(valid_types)}",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )

            # Status validation
            if valid_statuses and item.status not in valid_statuses:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.ERROR,
                        category="work_item",
                        message=f"Invalid status '{item.status}'. Expected one of: {', '.join(valid_statuses)}",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )

            # Size validation
            if valid_sizes and item.meta.size and item.meta.size not in valid_sizes:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        category="work_item",
                        message=f"Invalid size '{item.meta.size}'. Expected one of: {', '.join(valid_sizes)}",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )

            # Self-dependency check
            if item.id in item.dependencies:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        category="work_item",
                        message=f"WorkItem '{item.title}' depends on itself.",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=True,
                        repair_action=f"Remove self-dependency from {item.id}",
                    )
                )

        # Cross-reference check (broken parent or dependency UUIDs)
        for item in items:
            item_file = item.path or Path("unknown")
            if item.parent_id and item.parent_id not in seen_uuids:
                diagnostics.append(
                    Diagnostic(
                        severity=Severity.WARNING,
                        category="work_item",
                        message=f"Broken parent reference: parent UUID '{item.parent_id}' does not exist.",
                        file_path=item_file,
                        item_id=item.id,
                        is_fixable=False,
                    )
                )

            for dep_id in item.dependencies:
                if dep_id != item.id and dep_id not in seen_uuids:
                    diagnostics.append(
                        Diagnostic(
                            severity=Severity.WARNING,
                            category="work_item",
                            message=f"Broken dependency reference: target UUID '{dep_id}' does not exist.",
                            file_path=item_file,
                            item_id=item.id,
                            is_fixable=False,
                        )
                    )

        return diagnostics


class Repairer:
    """Performs safe automatic repairs of fixable validation issues."""

    def __init__(self, project_root: Optional[Path | str] = None):
        self.project_root = find_project_root(project_root)
        self.validator = Validator(self.project_root)

    def repair(self) -> List[str]:
        """Run validation and execute repairs for all fixable issues.

        Returns list of human-readable descriptions of repairs made.
        """
        repairs_made: List[str] = []
        if not self.project_root:
            return repairs_made

        diagnostics = self.validator.validate_all()

        for diag in diagnostics:
            if not diag.is_fixable:
                continue

            # 1. Missing directory repair
            if diag.category == "filesystem" and diag.file_path:
                diag.file_path.mkdir(parents=True, exist_ok=True)
                repairs_made.append(f"Created missing directory: {diag.file_path.relative_to(self.project_root)}")

            # 2. Protected config key relocation
            elif diag.category == "config" and diag.file_path and diag.file_path.name == "config.local.json":
                local_path = diag.file_path
                proj_path = self.project_root / ".ot" / "config.json"
                try:
                    local_data = load_json_file(local_path)
                    proj_data = load_json_file(proj_path)

                    new_local, new_proj, moved = relocate_protected_keys(local_data, proj_data)
                    if moved:
                        for key_path in moved:
                            repairs_made.append(
                                f"Moved protected configuration key '{key_path}' from config.local.json to config.json"
                            )
                        proj_path.write_text(json.dumps(new_proj, indent=2), encoding="utf-8")
                        local_path.write_text(json.dumps(new_local, indent=2), encoding="utf-8")
                except Exception:
                    pass

            # 3. WorkItem self-dependency removal
            elif diag.category == "work_item" and diag.item_id and "depends on itself" in diag.message:
                scanner = RepositoryScanner(self.project_root)
                items = scanner.scan_tasks_directory()
                for item in items:
                    if item.id == diag.item_id and item.remove_dependency(item.id):
                        write_work_item(item)
                        repairs_made.append(f"Removed self-dependency from WorkItem {item.title} ({item.id[:6]})")

        return repairs_made
