"""WorkItem and related data models for Open Tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


def generate_uuid() -> str:
    """Generate a canonical UUIDv4 string."""
    return str(uuid.uuid4())


def now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Author:
    """Author metadata for work items, comments, and revisions."""

    name: str
    email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"name": self.name}
        if self.email:
            data["email"] = self.email
        return data

    @classmethod
    def from_dict(cls, data: Any) -> Optional[Author]:
        if not data:
            return None
        if isinstance(data, str):
            return cls(name=data)
        if isinstance(data, dict):
            return cls(name=data.get("name", ""), email=data.get("email"))
        return None


@dataclass
class WorkItemMetadata:
    """Canonical machine-readable metadata for a WorkItem.

    Stored in the YAML frontmatter of the WorkItem's markdown document.
    """

    id: str = field(default_factory=generate_uuid)
    title: str = ""
    type: str = "task"
    status: str = "triage"
    size: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    updated_at: Optional[str] = None
    author: Optional[Author] = None
    parent: Optional[str] = None  # UUID of parent WorkItem
    dependencies: List[str] = field(default_factory=list)  # UUIDs this item depends on
    tags: List[str] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to a dictionary suitable for YAML frontmatter."""
        data: Dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "status": self.status,
        }
        if self.size:
            data["size"] = self.size
        data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
        if self.author:
            data["author"] = self.author.to_dict()
        if self.parent:
            data["parent"] = self.parent
        if self.dependencies:
            data["dependencies"] = list(self.dependencies)
        if self.tags:
            data["tags"] = list(self.tags)
        for k, v in self.custom.items():
            if k not in data:
                data[k] = v
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkItemMetadata:
        """Deserialize metadata from a dictionary."""
        known_keys = {
            "id",
            "title",
            "type",
            "status",
            "size",
            "created_at",
            "updated_at",
            "author",
            "parent",
            "dependencies",
            "tags",
        }
        item_id = str(data.get("id") or generate_uuid())
        title = str(data.get("title") or "")
        item_type = str(data.get("type") or "task")
        status = str(data.get("status") or "triage")
        size = data.get("size")
        created_at = str(data.get("created_at") or now_iso())
        updated_at = data.get("updated_at")
        if updated_at is not None:
            updated_at = str(updated_at)
        author = Author.from_dict(data.get("author"))
        parent = data.get("parent")
        if parent is not None:
            parent = str(parent)
        dependencies_raw = data.get("dependencies") or []
        dependencies = [str(d) for d in dependencies_raw] if isinstance(dependencies_raw, list) else []
        tags_raw = data.get("tags") or []
        tags = [str(t) for t in tags_raw] if isinstance(tags_raw, list) else []
        custom = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            id=item_id,
            title=title,
            type=item_type,
            status=status,
            size=size,
            created_at=created_at,
            updated_at=updated_at,
            author=author,
            parent=parent,
            dependencies=dependencies,
            tags=tags,
            custom=custom,
        )


from enum import Enum
from pathlib import Path


class RelationshipType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    DEPENDS_ON = "depends_on"
    BLOCKS = "blocks"


@dataclass
class Comment:
    """A comment on a WorkItem."""

    id: str = field(default_factory=generate_uuid)
    author: Optional[Author] = None
    timestamp: str = field(default_factory=now_iso)
    body: str = ""

    def to_markdown(self, template_text: Optional[str] = None) -> str:
        """Render comment to markdown format."""
        author_str = self.author.name if self.author else "Anonymous"
        if self.author and self.author.email:
            author_str += f" <{self.author.email}>"
        if template_text:
            from ot.templates import render_template

            rendered = render_template(
                template_text,
                {
                    "author_name": author_str,
                    "author_email": (self.author.email or "") if self.author else "",
                    "timestamp": self.timestamp,
                    "comment_id": self.id,
                    "body": self.body.strip(),
                },
            ).strip()
            if f"<!-- comment-id: {self.id} -->" not in rendered:
                lines = rendered.splitlines()
                if lines:
                    lines.insert(1, f"<!-- comment-id: {self.id} -->")
                    rendered = "\n".join(lines)
            return rendered + "\n"
        lines = [
            f"### Comment by {author_str} on {self.timestamp}",
            f"<!-- comment-id: {self.id} -->",
            "",
            self.body.strip(),
            "",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "timestamp": self.timestamp,
            "body": self.body,
        }
        if self.author:
            data["author"] = self.author.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Comment:
        return cls(
            id=str(data.get("id") or generate_uuid()),
            author=Author.from_dict(data.get("author")),
            timestamp=str(data.get("timestamp") or now_iso()),
            body=str(data.get("body") or ""),
        )


@dataclass
class WorkItem:
    """Represents a loaded WorkItem document."""

    meta: WorkItemMetadata
    body: str = ""
    comments: List[Comment] = field(default_factory=list)
    path: Optional[Path] = None

    @property
    def id(self) -> str:
        return self.meta.id

    @property
    def title(self) -> str:
        return self.meta.title

    @property
    def type(self) -> str:
        return self.meta.type

    @property
    def status(self) -> str:
        return self.meta.status

    @property
    def parent_id(self) -> Optional[str]:
        return self.meta.parent

    @property
    def dependencies(self) -> List[str]:
        return self.meta.dependencies

    def add_dependency(self, target_id: str) -> None:
        if target_id not in self.meta.dependencies and target_id != self.id:
            self.meta.dependencies.append(target_id)

    def remove_dependency(self, target_id: str) -> bool:
        if target_id in self.meta.dependencies:
            self.meta.dependencies.remove(target_id)
            return True
        return False


