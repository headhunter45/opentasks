"""JSON Schema generator for Open Tasks configuration, WorkItems, and Meetings."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ot.config import Config, DEFAULT_CONFIG

JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
UUID_V4_PATTERN = "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"

DEFAULT_TYPES: List[str] = sorted(DEFAULT_CONFIG["workItem"]["types"].keys())
DEFAULT_STATUSES: List[str] = sorted(DEFAULT_CONFIG["workItem"]["statuses"].keys())
DEFAULT_SIZES: List[str] = sorted(DEFAULT_CONFIG["workItem"]["sizes"].keys())
DEFAULT_MEETING_TYPES: List[str] = sorted(DEFAULT_CONFIG["meeting"]["types"].keys())


def _extract_keys(val: Any, fallback: List[str]) -> List[str]:
    if isinstance(val, dict) and val:
        return sorted(str(k) for k in val.keys())
    if isinstance(val, (list, tuple, set)) and val:
        return sorted(str(x) for x in val)
    return list(fallback)


def _author_schema() -> Dict[str, Any]:
    return {
        "oneOf": [
            {"type": "string", "minLength": 1},
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "email": {"type": ["string", "null"]},
                },
                "required": ["name"],
                "additionalProperties": False,
            },
        ]
    }


def generate_config_schema(config: Optional[Config] = None) -> Dict[str, Any]:
    """Generate JSON Schema for `.ot/config.json` and `.ot/config.local.json`."""
    return {
        "$schema": JSON_SCHEMA_DRAFT,
        "$id": "https://opentasks.dev/schemas/config.schema.json",
        "title": "Open Tasks Configuration",
        "description": "Schema for Open Tasks project (.ot/config.json) and local (.ot/config.local.json) configuration files.",
        "type": "object",
        "properties": {
            "system": {
                "type": "object",
                "description": "Protected system version and schema settings.",
                "properties": {
                    "schemaVersion": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 1,
                        "description": "Configuration and repository schema version.",
                    },
                    "toolVersion": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Pinned Open Tasks tool version for the project.",
                    },
                },
                "additionalProperties": True,
            },
            "workItem": {
                "type": "object",
                "description": "Protected WorkItem lifecycle and taxonomy settings.",
                "properties": {
                    "types": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                        "default": sorted(DEFAULT_TYPES),
                    },
                    "statuses": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                        "default": sorted(DEFAULT_STATUSES),
                    },
                    "sizes": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                        "default": sorted(DEFAULT_SIZES),
                    },
                    "defaults": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "minLength": 1, "default": "task"},
                            "status": {"type": "string", "minLength": 1, "default": "triage"},
                        },
                        "additionalProperties": True,
                    },
                },
                "additionalProperties": True,
            },
            "meeting": {
                "type": "object",
                "description": "Protected Meeting taxonomy settings.",
                "properties": {
                    "types": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "minItems": 1,
                        "uniqueItems": True,
                        "default": ["grooming", "planning", "retrospective", "ideation"],
                    }
                },
                "additionalProperties": True,
            },
            "paths": {
                "type": "object",
                "description": "Project-relative directory layout overrides.",
                "properties": {
                    "tasks": {
                        "type": "string",
                        "minLength": 1,
                        "default": ".ot/tasks",
                        "description": "Relative path within the project root for WorkItem directories.",
                    },
                    "meetings": {
                        "type": "string",
                        "minLength": 1,
                        "default": ".ot/meetings",
                        "description": "Relative path within the project root for Meeting records.",
                    },
                    "templates": {
                        "type": "string",
                        "minLength": 1,
                        "default": ".ot/templates",
                        "description": "Relative path within the project root for Markdown templates.",
                    },
                },
                "additionalProperties": False,
            },
            "user": {
                "type": "object",
                "description": "Local user preferences (typically stored in .ot/config.local.json).",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "editor": {"type": "string"},
                    "outputWidth": {
                        "type": ["integer", "null"],
                        "minimum": 40,
                    },
                },
                "additionalProperties": True,
            },
        },
        "additionalProperties": True,
    }


def generate_work_item_schema(config: Optional[Config] = None) -> Dict[str, Any]:
    """Generate JSON Schema for a WorkItem (frontmatter and JSON export structure)."""
    types = _extract_keys(config.work_item_types if config else None, DEFAULT_TYPES)
    statuses = _extract_keys(config.work_item_statuses if config else None, DEFAULT_STATUSES)
    sizes = _extract_keys(config.work_item_sizes if config else None, DEFAULT_SIZES)

    return {
        "$schema": JSON_SCHEMA_DRAFT,
        "$id": "https://opentasks.dev/schemas/work-item.schema.json",
        "title": "Open Tasks WorkItem",
        "description": "Schema for an Open Tasks WorkItem YAML frontmatter and JSON representation.",
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "pattern": UUID_V4_PATTERN,
                "description": "Canonical UUIDv4 identifier for the WorkItem.",
            },
            "short_id": {
                "type": "string",
                "minLength": 6,
                "description": "Derived short identifier prefix (present in JSON exports).",
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "description": "Human-readable summary title of the WorkItem.",
            },
            "type": {
                "type": "string",
                "enum": types,
                "description": "WorkItem classification type.",
            },
            "status": {
                "type": "string",
                "enum": statuses,
                "description": "Current workflow lifecycle status.",
            },
            "size": {
                "type": ["string", "null"],
                "enum": [*sizes, None],
                "description": "Optional relative effort size estimate.",
            },
            "created_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 creation timestamp.",
            },
            "updated_at": {
                "type": ["string", "null"],
                "format": "date-time",
                "description": "ISO 8601 last-modified timestamp.",
            },
            "author": _author_schema(),
            "parent": {
                "type": ["string", "null"],
                "pattern": UUID_V4_PATTERN,
                "description": "Optional parent WorkItem UUIDv4.",
            },
            "dependencies": {
                "type": "array",
                "items": {"type": "string", "pattern": UUID_V4_PATTERN},
                "uniqueItems": True,
                "default": [],
                "description": "UUIDv4 identifiers of WorkItems this item depends on.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string", "minLength": 1},
                "uniqueItems": True,
                "default": [],
                "description": "Free-form categorization tags.",
            },
            "comments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "author": _author_schema(),
                        "timestamp": {"type": "string", "format": "date-time"},
                        "parent_id": {"type": ["string", "null"]},
                        "content": {"type": "string"},
                    },
                    "required": ["id", "timestamp", "content"],
                    "additionalProperties": True,
                },
            },
        },
        "required": ["id", "title", "type", "status", "created_at"],
        "additionalProperties": True,
    }


def generate_meeting_schema(config: Optional[Config] = None) -> Dict[str, Any]:
    """Generate JSON Schema for a Meeting (frontmatter and JSON export structure)."""
    meeting_types = _extract_keys(
        config.get("meeting.types") if config else None,
        DEFAULT_MEETING_TYPES,
    )
    return {
        "$schema": JSON_SCHEMA_DRAFT,
        "$id": "https://opentasks.dev/schemas/meeting.schema.json",
        "title": "Open Tasks Meeting",
        "description": "Schema for an Open Tasks Meeting YAML frontmatter and JSON representation.",
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "pattern": UUID_V4_PATTERN,
                "description": "Canonical UUIDv4 identifier for the Meeting.",
            },
            "type": {
                "type": "string",
                "enum": meeting_types,
                "description": "Meeting category type.",
            },
            "status": {
                "type": "string",
                "enum": ["active", "ended"],
                "description": "Meeting lifecycle status.",
            },
            "started_at": {
                "type": "string",
                "format": "date-time",
                "description": "ISO 8601 start timestamp.",
            },
            "ended_at": {
                "type": ["string", "null"],
                "format": "date-time",
                "description": "ISO 8601 completion timestamp (null while active).",
            },
            "organizer": _author_schema(),
            "attendees": {
                "type": "array",
                "items": _author_schema(),
                "default": [],
            },
            "body": {
                "type": "string",
                "description": "Markdown meeting notes content.",
            },
        },
        "required": ["id", "type", "status", "started_at"],
        "additionalProperties": True,
    }


def generate_all_schemas(config: Optional[Config] = None) -> Dict[str, Dict[str, Any]]:
    """Return a bundle of all Open Tasks JSON Schemas."""
    return {
        "config": generate_config_schema(config),
        "work-item": generate_work_item_schema(config),
        "meeting": generate_meeting_schema(config),
    }


def get_schema(target: str = "all", config: Optional[Config] = None) -> Dict[str, Any]:
    """Retrieve a specific schema ('config', 'work-item', 'meeting') or 'all'."""
    key = target.strip().lower()
    if key == "config":
        return generate_config_schema(config)
    if key in ("work-item", "work_item", "workitem", "task"):
        return generate_work_item_schema(config)
    if key == "meeting":
        return generate_meeting_schema(config)
    if key == "all":
        return {
            "$schema": JSON_SCHEMA_DRAFT,
            "$id": "https://opentasks.dev/schemas/all.schema.json",
            "title": "Open Tasks Schema Bundle",
            "$defs": generate_all_schemas(config),
        }
    raise ValueError(f"Unknown schema target '{target}'. Expected one of: all, config, work-item, meeting.")
