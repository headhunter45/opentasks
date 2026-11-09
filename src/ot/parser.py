"""WorkItem document reader, writer, and round-trip parser."""

from __future__ import annotations

import os
from pathlib import Path
import re
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from ot.models import Author, Comment, WorkItem, WorkItemMetadata, generate_uuid, now_iso

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
COMMENT_HEADER_PATTERN = re.compile(
    r"^###\s+Comment\s+by\s+(.*?)\s+on\s+([^\n]+)", re.MULTILINE
)
COMMENT_ID_PATTERN = re.compile(r"<!--\s*comment-id:\s*([^\s]+)\s*-->")


def parse_yaml_frontmatter(yaml_text: str) -> Dict[str, Any]:
    """Parse YAML frontmatter text into a Python dictionary.

    Supports key-value pairs, nested 2-space indented dicts, and list items.
    """
    data: Dict[str, Any] = {}
    lines = yaml_text.splitlines()
    current_key: Optional[str] = None
    list_accumulator: List[Any] = []
    dict_accumulator: Dict[str, Any] = {}

    def flush():
        nonlocal current_key, list_accumulator, dict_accumulator
        if current_key:
            if list_accumulator:
                data[current_key] = list(list_accumulator)
            elif dict_accumulator:
                data[current_key] = dict(dict_accumulator)
        current_key = None
        list_accumulator = []
        dict_accumulator = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("  - "):
            val = line[4:].strip()
            # Unquote string if quoted
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            list_accumulator.append(val)
        elif line.startswith("  ") and ":" in line:
            k, v = line.strip().split(":", 1)
            k = k.strip()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            dict_accumulator[k] = v if v else None
        elif ":" in line:
            flush()
            k, v = line.split(":", 1)
            current_key = k.strip()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            if v:
                data[current_key] = v
            else:
                data[current_key] = None

    flush()
    return data


def serialize_yaml_frontmatter(meta: WorkItemMetadata) -> str:
    """Serialize WorkItemMetadata to YAML frontmatter string."""
    lines = ["---"]
    lines.append(f"id: {meta.id}")
    lines.append(f"title: {meta.title}")
    lines.append(f"type: {meta.type}")
    lines.append(f"status: {meta.status}")
    if meta.size:
        lines.append(f"size: {meta.size}")
    lines.append(f"created_at: {meta.created_at}")
    if meta.updated_at:
        lines.append(f"updated_at: {meta.updated_at}")
    if meta.parent:
        lines.append(f"parent: {meta.parent}")
    if meta.author:
        lines.append("author:")
        lines.append(f"  name: {meta.author.name}")
        if meta.author.email:
            lines.append(f"  email: {meta.author.email}")
    if meta.dependencies:
        lines.append("dependencies:")
        for dep in meta.dependencies:
            lines.append(f"  - {dep}")
    if meta.tags:
        lines.append("tags:")
        for tag in meta.tags:
            lines.append(f"  - {tag}")

    # Preserve custom/unknown metadata fields
    for k, v in meta.custom.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        elif isinstance(v, dict):
            lines.append(f"{k}:")
            for sub_k, sub_v in v.items():
                lines.append(f"  {sub_k}: {sub_v}")
        else:
            lines.append(f"{k}: {v}")

    lines.append("---")
    return "\n".join(lines)


def split_comments_section(markdown_text: str) -> Tuple[str, List[Comment]]:
    """Split markdown text into body content and list of Comments."""
    # Look for top-level ## Comments heading
    comments_marker = re.search(r"\n##\s+Comments\s*\n", markdown_text, re.IGNORECASE)
    if not comments_marker:
        return markdown_text.strip(), []

    body = markdown_text[: comments_marker.start()].strip()
    comments_raw = markdown_text[comments_marker.end() :]

    comments: List[Comment] = []
    # Split individual comments by "### Comment by "
    comment_blocks = re.split(r"(?=^###\s+Comment\s+by\s+)", comments_raw, flags=re.MULTILINE)

    for block in comment_blocks:
        block = block.strip()
        if not block:
            continue
        header_match = COMMENT_HEADER_PATTERN.search(block)
        if not header_match:
            continue

        author_raw = header_match.group(1).strip()
        timestamp = header_match.group(2).strip()

        author_name = author_raw
        author_email = None
        email_match = re.search(r"<([^>]+)>", author_raw)
        if email_match:
            author_email = email_match.group(1)
            author_name = re.sub(r"<[^>]+>", "", author_raw).strip()

        # Check for comment-id
        id_match = COMMENT_ID_PATTERN.search(block)
        comment_id = id_match.group(1) if id_match else generate_uuid()

        # Body of comment is after the header and comment-id lines
        lines = block.splitlines()
        body_lines = []
        for line in lines[1:]:
            if COMMENT_ID_PATTERN.search(line):
                continue
            body_lines.append(line)

        comment_body = "\n".join(body_lines).strip()
        comments.append(
            Comment(
                id=comment_id,
                author=Author(name=author_name, email=author_email),
                timestamp=timestamp,
                body=comment_body,
            )
        )

    return body, comments


def parse_work_item_content(content: str, file_path: Optional[Path] = None) -> WorkItem:
    """Parse raw text content of a WorkItem document into a WorkItem instance."""
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        yaml_text = match.group(1)
        body_text = content[match.end() :]
        meta_dict = parse_yaml_frontmatter(yaml_text)
    else:
        meta_dict = {}
        body_text = content

    meta = WorkItemMetadata.from_dict(meta_dict)
    body, comments = split_comments_section(body_text)

    return WorkItem(
        meta=meta,
        body=body,
        comments=comments,
        path=file_path,
    )


def read_work_item(path: Path | str) -> WorkItem:
    """Read and parse a WorkItem from a file (e.g. index.md)."""
    p = Path(path).resolve()
    if p.is_dir():
        p = p / "index.md"
    if not p.is_file():
        raise FileNotFoundError(f"WorkItem file not found at {p}")

    content = p.read_text(encoding="utf-8")
    return parse_work_item_content(content, file_path=p)


def render_work_item(item: WorkItem, project_root: Optional[Path | str] = None) -> str:
    """Render a WorkItem instance to standard markdown with frontmatter, body, and comments."""
    parts = [serialize_yaml_frontmatter(item.meta)]
    if item.body:
        parts.append("")
        parts.append(item.body.strip())

    if item.comments:
        from ot.templates import get_template

        comment_tmpl = get_template("shared/comment.md", project_root or (item.path.parent if item.path else None))
        parts.append("")
        parts.append("## Comments")
        for comment in item.comments:
            parts.append("")
            parts.append(comment.to_markdown(template_text=comment_tmpl).strip())

    parts.append("")  # Trailing newline
    return "\n".join(parts)


def write_work_item(item: WorkItem, target_path: Optional[Path | str] = None) -> Path:
    """Atomically write a WorkItem to target_path or its existing path."""
    dest = Path(target_path or item.path).resolve()
    if dest.is_dir():
        dest = dest / "index.md"
    dest.parent.mkdir(parents=True, exist_ok=True)

    rendered = render_work_item(item)

    # Atomic write via temp file in same directory
    with tempfile.NamedTemporaryFile("w", dir=dest.parent, delete=False, encoding="utf-8") as tf:
        tf.write(rendered)
        temp_name = tf.name

    os.replace(temp_name, dest)
    item.path = dest
    return dest
