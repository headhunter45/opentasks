"""Repository scanner and in-memory WorkItem index."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
from typing import Dict, Iterable, List, Optional, Set

from ot.config import Config, load_config
from ot.discovery import find_project_root
from ot.identifiers import (
    AmbiguousIdentifierError,
    IdentifierNotFoundError,
    compute_short_id,
    resolve_identifier,
)
from ot.models import WorkItem
from ot.parser import read_work_item


class RepositoryScanner:
    """Discovers and scans WorkItem files within an Open Tasks project."""

    def __init__(self, project_root: Optional[Path | str] = None):
        self.project_root = find_project_root(project_root)

    def scan_tasks_directory(self) -> List[WorkItem]:
        """Scan configured tasks directory (default .ot/tasks/) for all WorkItems."""
        if not self.project_root:
            return []

        try:
            cfg = load_config(self.project_root)
            tasks_dir = cfg.tasks_dir
        except Exception:
            tasks_dir = self.project_root / ".ot" / "tasks"

        if not tasks_dir.is_dir():
            return []

        work_items: List[WorkItem] = []
        for path in sorted(tasks_dir.rglob("*.md")):
            # Ignore hidden files or template directories
            if any(part.startswith(".") for part in path.parts):
                # Allow .ot itself
                rel_parts = path.relative_to(self.project_root).parts
                if any(part.startswith(".") and part != ".ot" for part in rel_parts):
                    continue

            try:
                item = read_work_item(path)
                # Only treat as WorkItem if it has a valid title or ID
                if item.meta.id:
                    work_items.append(item)
            except Exception:
                # Malformed files can be flagged by validation later
                pass

        return work_items


class WorkItemIndex:
    """In-memory index and graph of WorkItems in a project."""

    def __init__(self, items: Iterable[WorkItem]):
        self._items_by_id: Dict[str, WorkItem] = {}
        self._children_by_parent: Dict[str, List[WorkItem]] = defaultdict(list)
        self._dependents_by_dep: Dict[str, List[WorkItem]] = defaultdict(list)
        self._short_ids: Dict[str, str] = {}

        for item in items:
            self.add(item)

    def add(self, item: WorkItem) -> None:
        self._items_by_id[item.id] = item
        if item.parent_id:
            self._children_by_parent[item.parent_id].append(item)
        for dep_id in item.dependencies:
            self._dependents_by_dep[dep_id].append(item)
        self._recompute_short_ids()

    def _recompute_short_ids(self) -> None:
        all_ids = list(self._items_by_id.keys())
        self._short_ids = {
            item_id: compute_short_id(item_id, all_ids) for item_id in all_ids
        }

    def get_by_id(self, item_id: str) -> Optional[WorkItem]:
        return self._items_by_id.get(item_id)

    def get_short_id(self, item_id: str) -> str:
        return self._short_ids.get(item_id, item_id[:6])

    def resolve(self, query: str) -> WorkItem:
        """Resolve query (UUID, short ID, or title) to a WorkItem."""
        _, item = resolve_identifier(query, self._items_by_id)
        return item

    def all(self) -> List[WorkItem]:
        return list(self._items_by_id.values())

    def get_children(self, parent_id: str) -> List[WorkItem]:
        return list(self._children_by_parent.get(parent_id, []))

    def get_parent(self, item: WorkItem) -> Optional[WorkItem]:
        if item.parent_id:
            return self.get_by_id(item.parent_id)
        return None

    def get_dependencies(self, item: WorkItem) -> List[WorkItem]:
        """Return list of WorkItems that `item` depends on."""
        deps = []
        for dep_id in item.dependencies:
            dep_item = self.get_by_id(dep_id)
            if dep_item:
                deps.append(dep_item)
        return deps

    def get_dependents(self, item: WorkItem) -> List[WorkItem]:
        """Return list of WorkItems that depend on `item` (items blocked by `item`)."""
        return list(self._dependents_by_dep.get(item.id, []))

    @staticmethod
    def _normalize_filter_values(val: Optional[str | Iterable[str]]) -> List[str]:
        if not val:
            return []
        raw_items = [val] if isinstance(val, str) else list(val)
        tokens: List[str] = []
        for item in raw_items:
            if not item:
                continue
            item_str = str(item).strip()
            if len(item_str) >= 2 and item_str.startswith("/") and item_str.endswith("/"):
                tokens.append(item_str)
                continue
            for part in item_str.split(","):
                cleaned = part.strip()
                if cleaned:
                    tokens.append(cleaned)
        return tokens

    @staticmethod
    def _matches_author(item: WorkItem, author_tokens: List[str]) -> bool:
        if not item.meta.author:
            return False
        name = item.meta.author.name or ""
        email = item.meta.author.email or ""
        for token in author_tokens:
            if len(token) >= 2 and token.startswith("/") and token.endswith("/"):
                pattern = token[1:-1]
                try:
                    if re.search(pattern, name) or re.search(pattern, email):
                        return True
                except re.error:
                    continue
            else:
                tok_low = token.lower()
                if tok_low in name.lower() or tok_low in email.lower():
                    return True
        return False

    def filter(
        self,
        item_id: Optional[str | Iterable[str]] = None,
        title: Optional[str | Iterable[str]] = None,
        item_type: Optional[str | Iterable[str]] = None,
        status: Optional[str | Iterable[str]] = None,
        size: Optional[str | Iterable[str]] = None,
        tag: Optional[str | Iterable[str]] = None,
        author_name: Optional[str | Iterable[str]] = None,
    ) -> List[WorkItem]:
        """Filter work items by criteria.

        Multiple values for the same column are OR-ed together.
        Different columns are AND-ed together.
        Values support case-insensitive prefix matching from the start of the column value
        (except author, which supports /regex/ or case-insensitive substring matching on name/email).
        """
        id_vals = [v.lower() for v in self._normalize_filter_values(item_id)]
        title_vals = [v.lower() for v in self._normalize_filter_values(title)]
        type_vals = [v.lower() for v in self._normalize_filter_values(item_type)]
        status_vals = [v.lower().replace("-", "_") for v in self._normalize_filter_values(status)]
        size_vals = [v.lower() for v in self._normalize_filter_values(size)]
        tag_vals = [v.lower() for v in self._normalize_filter_values(tag)]
        author_vals = self._normalize_filter_values(author_name)

        results = []
        for item in self.all():
            if id_vals:
                full_id = (item.id or "").lower()
                short_id = self.get_short_id(item.id).lower()
                if not any(full_id.startswith(v) or short_id.startswith(v) for v in id_vals):
                    continue
            if title_vals:
                it_title = (item.title or "").lower()
                if not any(it_title.startswith(v) for v in title_vals):
                    continue
            if type_vals:
                it_type = (item.type or "").lower()
                if not any(it_type.startswith(v) for v in type_vals):
                    continue
            if status_vals:
                it_status = (item.status or "").lower().replace("-", "_")
                if not any(it_status.startswith(v) for v in status_vals):
                    continue
            if size_vals:
                it_size = (item.meta.size or "").lower()
                if not it_size or not any(it_size.startswith(v) for v in size_vals):
                    continue
            if tag_vals:
                it_tags = [t.lower() for t in (item.meta.tags or [])]
                if not any(any(t.startswith(v) for t in it_tags) for v in tag_vals):
                    continue
            if author_vals:
                if not self._matches_author(item, author_vals):
                    continue
            results.append(item)
        return results


def load_index(start_dir: Optional[Path | str] = None) -> WorkItemIndex:
    """Scan repository and build WorkItemIndex."""
    scanner = RepositoryScanner(start_dir)
    items = scanner.scan_tasks_directory()
    return WorkItemIndex(items)
