"""Command-line interface for Open Tasks (ot)."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import List, Optional

from ot.config import Config, get_flattened_keys, load_config, set_config_key
from ot.discovery import check_vcs_safety, discover_root, find_project_root
from ot.identifiers import generate_uuid
from ot.models import Author, Comment, Meeting, WorkItem, WorkItemMetadata, now_iso
from ot.parser import (
    parse_meeting_content,
    parse_work_item_content,
    read_meeting,
    read_work_item,
    render_meeting,
    render_work_item,
    scan_meetings,
    write_meeting,
    write_work_item,
)
from ot.scanner import WorkItemIndex, load_index


def sanitize_folder_name(title: str) -> str:
    """Convert title to a PascalCase / CamelCase folder name."""
    words = re.findall(r"[a-zA-Z0-9]+", title)
    if not words:
        return "Task"
    return "".join(w.capitalize() for w in words[:6])


def resolve_output_width(
    args: Optional[argparse.Namespace] = None,
    config: Optional[Config] = None,
) -> int:
    """Resolve CLI output width in columns.

     Precedence:
      1. Explicit `--width` CLI flag
      2. Configured `user.outputWidth` / `output.width`
      3. Terminal width: if interactive / piped (stdin/stdout/stderr tty or COLUMNS)
         and >= 120, use full terminal width; if < 120, use 80.
      4. Default fallback when no terminal size is available: 120.
    """
    if args is not None and getattr(args, "width", None) is not None:
        return max(40, int(args.width))

    if config is not None and config.output_width is not None:
        return max(40, int(config.output_width))

    env_cols = os.environ.get("COLUMNS")
    if env_cols:
        try:
            cols = int(env_cols)
            if cols > 0:
                return cols if cols >= 120 else 80
        except ValueError:
            pass

    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            if hasattr(stream, "fileno"):
                cols = os.get_terminal_size(stream.fileno()).columns
                if cols > 0:
                    return cols if cols >= 120 else 80
        except Exception:
            continue

    return 120


def format_task_row(short_id: str, item: WorkItem, total_width: int = 120) -> str:
    status_display = item.status.replace("_", "-").capitalize()
    type_display = item.type.capitalize()
    title_width = max(20, total_width - 35)
    title_str = item.title
    if len(title_str) > title_width and title_width > 3:
        title_str = title_str[: title_width - 3] + "..."
    return f"{short_id:<8} {title_str:<{title_width}} {type_display:<12} {status_display:<12}"


def cmd_task_list(args: argparse.Namespace, config: Config) -> int:
    """List WorkItems in project."""
    index = load_index(config.project_root)

    # Validate --type filter tokens against allowed types
    type_tokens = index._normalize_filter_values(getattr(args, "type", None))
    valid_types = list(config.work_item_types.keys()) if config.work_item_types else []
    if type_tokens and valid_types:
        for tok in type_tokens:
            tok_low = tok.lower()
            if not any(vt.lower().startswith(tok_low) for vt in valid_types):
                print(
                    f"Error: Invalid type filter '{tok}'. Allowed types: {', '.join(valid_types)}",
                    file=sys.stderr,
                )
                return 1

    # Validate --status filter tokens against allowed statuses
    status_tokens = index._normalize_filter_values(getattr(args, "status", None))
    valid_statuses = list(config.work_item_statuses.keys()) if config.work_item_statuses else []
    if status_tokens and valid_statuses:
        for tok in status_tokens:
            tok_norm = tok.lower().replace("-", "_")
            if not any(vs.lower().replace("-", "_").startswith(tok_norm) for vs in valid_statuses):
                print(
                    f"Error: Invalid status filter '{tok}'. Allowed statuses: {', '.join(valid_statuses)}",
                    file=sys.stderr,
                )
                return 1

    items = index.filter(
        item_id=getattr(args, "id", None),
        title=getattr(args, "title", None),
        item_type=args.type,
        status=args.status,
        size=args.size,
        tag=args.tag,
        author_name=args.author,
    )

    pos_id_tokens = index._normalize_filter_values(getattr(args, "ids", None))
    unmatched_ids: List[str] = []
    if pos_id_tokens:
        all_items = index.all()
        for tok in pos_id_tokens:
            tok_low = tok.lower()
            if not any(
                (it.id or "").lower().startswith(tok_low)
                or index.get_short_id(it.id).lower().startswith(tok_low)
                for it in all_items
            ):
                unmatched_ids.append(tok)

        pos_lower = [t.lower() for t in pos_id_tokens]
        items = [
            it
            for it in items
            if any(
                (it.id or "").lower().startswith(p)
                or index.get_short_id(it.id).lower().startswith(p)
                for p in pos_lower
            )
        ]

    if getattr(args, "json", False):
        data = []
        for item in items:
            d = item.meta.to_dict()
            d["short_id"] = index.get_short_id(item.id)
            data.append(d)
        for missing_id in unmatched_ids:
            data.append({"id": missing_id, "exists": False})
        print(json.dumps(data, indent=2))
        return 1 if unmatched_ids else 0

    if not items:
        if not unmatched_ids:
            print("No work items found.")
            return 0
    else:
        total_width = resolve_output_width(args, config)
        title_width = max(20, total_width - 35)
        header = f"{'ID':<8} {'Title':<{title_width}} {'Type':<12} {'Status':<12}"
        divider = f"{'-'*8} {'-'*title_width} {'-'*12} {'-'*12}"
        print(header)
        print(divider)
        for item in items:
            short_id = index.get_short_id(item.id)
            print(format_task_row(short_id, item, total_width=total_width))

    if unmatched_ids:
        print(f"Error: Task ID(s) not found: {', '.join(unmatched_ids)}", file=sys.stderr)
        return 1
    return 0


def cmd_task_show(args: argparse.Namespace, config: Config) -> int:
    """Show details of a WorkItem."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    short_id = index.get_short_id(item.id)
    print(f"ID:          {item.id} ({short_id})")
    print(f"Title:       {item.title}")
    print(f"Type:        {item.type}")
    print(f"Status:      {item.status}")
    if item.meta.size:
        print(f"Size:        {item.meta.size}")
    if item.meta.author:
        author_str = item.meta.author.name
        if item.meta.author.email:
            author_str += f" <{item.meta.author.email}>"
        print(f"Author:      {author_str}")
    print(f"Created:     {item.meta.created_at}")
    if item.meta.updated_at:
        print(f"Updated:     {item.meta.updated_at}")
    if item.meta.parent:
        parent = index.get_parent(item)
        parent_title = parent.title if parent else "Unknown"
        parent_short = index.get_short_id(item.meta.parent)
        print(f"Parent:      {parent_short} ({parent_title})")

    children = index.get_children(item.id)
    if children:
        print("\nChildren:")
        for child in children:
            c_short = index.get_short_id(child.id)
            print(f"  - {c_short}: {child.title} [{child.status}]")

    deps = index.get_dependencies(item)
    if deps:
        print("\nDepends on:")
        for dep in deps:
            d_short = index.get_short_id(dep.id)
            print(f"  - {d_short}: {dep.title} [{dep.status}]")

    dependents = index.get_dependents(item)
    if dependents:
        print("\nBlocks:")
        for dep in dependents:
            d_short = index.get_short_id(dep.id)
            print(f"  - {d_short}: {dep.title} [{dep.status}]")

    if item.body:
        print(f"\n--- Description ---\n{item.body}")

    if item.comments:
        from ot.templates import get_template
        comment_tmpl = get_template("shared/comment.md", config.project_root)
        print("\n--- Comments ---")
        for comment in item.comments:
            print()
            print(comment.to_markdown(template_text=comment_tmpl).strip())

    return 0


def cmd_task_create(args: argparse.Namespace, config: Config) -> int:
    """Create a new WorkItem."""
    if not config.project_root:
        print("Error: No Open Tasks project found (.ot). Run 'ot init' first.", file=sys.stderr)
        return 1

    title = args.title or getattr(args, "positional_title", None) or ""
    if not title and getattr(args, "no_edit", False):
        print("Error: Title is required when --no-edit is specified.", file=sys.stderr)
        return 1

    item_id = generate_uuid()
    item_type = args.type or "task"
    status = args.status or "triage"
    size = args.size
    created_at = now_iso()

    author = Author(name=config.user_name, email=config.user_email)

    parent_id = None
    if args.parent:
        index = load_index(config.project_root)
        try:
            parent_item = index.resolve(args.parent)
            parent_id = parent_item.id
        except Exception as e:
            print(f"Error resolving parent '{args.parent}': {e}", file=sys.stderr)
            return 1

    from ot.templates import get_template, render_template

    tmpl_text = (
        get_template(f"tasks/{item_type}.md", config.project_root)
        or get_template("tasks/default.md", config.project_root)
    )
    if tmpl_text:
        rendered_tmpl = render_template(
            tmpl_text,
            {
                "id": item_id,
                "title": title,
                "type": item_type,
                "status": status,
                "size": size or "",
                "created_at": created_at,
                "author_name": author.name,
                "author_email": author.email or "",
            },
        )
        item = parse_work_item_content(rendered_tmpl)
        item.meta.id = item_id
        item.meta.title = title
        item.meta.type = item_type
        item.meta.status = status
        item.meta.size = size if size else None
        item.meta.created_at = created_at
        item.meta.author = author
        item.meta.parent = parent_id
    else:
        meta = WorkItemMetadata(
            id=item_id,
            title=title,
            type=item_type,
            status=status,
            size=size,
            author=author,
            parent=parent_id,
            created_at=created_at,
        )
        body = f"# {title}\n\n## Overview\n\n" if title else ""
        item = WorkItem(meta=meta, body=body)

    if args.overview is not None:
        if "## Overview" in item.body:
            item.body = re.sub(
                r"(## Overview\s*\n)(.*?)(?=\n## |\Z)",
                rf"\g<1>{args.overview}\n\n",
                item.body,
                count=1,
                flags=re.DOTALL,
            ).rstrip()
        else:
            prefix = f"# {title}\n\n" if not item.body.strip() else f"{item.body.rstrip()}\n\n"
            item.body = f"{prefix}## Overview\n{args.overview}\n"

    # Determine file location
    tasks_dir = config.tasks_dir
    folder_name = sanitize_folder_name(title) if title else f"Task-{item_id[:6]}"

    if parent_id:
        parent_item = load_index(config.project_root).get_by_id(parent_id)
        if parent_item and parent_item.path:
            target_path = parent_item.path.parent / folder_name / "index.md"
        else:
            target_path = tasks_dir / folder_name / "index.md"
    else:
        target_path = tasks_dir / folder_name / "index.md"

    # If interactive edit requested or title missing without no_edit
    if getattr(args, "edit", False) or (not title and not getattr(args, "no_edit", False)):
        rendered = render_work_item(item, project_root=config.project_root)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
            tf.write(rendered)
            tf_path = tf.name

        editor = config.editor
        preserve_temp = False
        try:
            subprocess.run(f"{editor} {tf_path}", shell=True, check=True)
            new_content = Path(tf_path).read_text(encoding="utf-8")
            item = parse_work_item_content(new_content)
            validator = Validator(config.project_root)
            diags = validator.validate_single_work_item(item)
            errors = [d for d in diags if d.severity == Severity.ERROR]
            if errors:
                preserve_temp = True
                print("Error: Validation failed for edited WorkItem:", file=sys.stderr)
                for err in errors:
                    print(f"  - {err.message}", file=sys.stderr)
                print(f"Edited content preserved at: {tf_path}", file=sys.stderr)
                return 1
            if not title and item.title:
                folder_name = sanitize_folder_name(item.title)
                if parent_id:
                    parent_item = load_index(config.project_root).get_by_id(parent_id)
                    if parent_item and parent_item.path:
                        target_path = parent_item.path.parent / folder_name / "index.md"
                    else:
                        target_path = tasks_dir / folder_name / "index.md"
                else:
                    target_path = tasks_dir / folder_name / "index.md"
        finally:
            if not preserve_temp and os.path.exists(tf_path):
                os.remove(tf_path)

    written = write_work_item(item, target_path)
    short_id = item.id[:6]
    print(f"Created WorkItem {short_id} ({item.title}) at {written}")
    return 0


def cmd_task_edit(args: argparse.Namespace, config: Config) -> int:
    """Open WorkItem in editor and validate on save."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not item.path or not item.path.is_file():
        print(f"Error: WorkItem file not found on disk for {item.id}", file=sys.stderr)
        return 1

    # Write copy to temporary file
    rendered = render_work_item(item, project_root=config.project_root)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(rendered)
        tf_path = tf.name

    editor = config.editor
    preserve_temp = False
    try:
        subprocess.run(f"{editor} {tf_path}", shell=True, check=True)
        new_content = Path(tf_path).read_text(encoding="utf-8")
        updated_item = parse_work_item_content(new_content, file_path=item.path)
        validator = Validator(config.project_root)
        diags = validator.validate_single_work_item(updated_item)
        errors = [d for d in diags if d.severity == Severity.ERROR]
        if errors:
            preserve_temp = True
            print("Error: Validation failed for edited WorkItem:", file=sys.stderr)
            for err in errors:
                print(f"  - {err.message}", file=sys.stderr)
            print(f"Edited content preserved at: {tf_path}", file=sys.stderr)
            return 1
        updated_item.meta.updated_at = now_iso()
        write_work_item(updated_item)
        print(f"Updated WorkItem {index.get_short_id(item.id)} ({updated_item.title})")
        return 0
    finally:
        if not preserve_temp and os.path.exists(tf_path):
            os.remove(tf_path)


def cmd_task_status(args: argparse.Namespace, config: Config) -> int:
    """Update status of a WorkItem."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    new_status = args.status.lower().replace("-", "_")
    valid_statuses = config.work_item_statuses
    if valid_statuses and new_status not in valid_statuses:
        print(
            f"Warning: '{new_status}' is not in configured statuses: {', '.join(valid_statuses.keys())}",
            file=sys.stderr,
        )

    item.meta.status = new_status
    item.meta.updated_at = now_iso()
    write_work_item(item)
    print(f"Updated status for {index.get_short_id(item.id)} -> {new_status}")
    return 0


def cmd_task_comment(args: argparse.Namespace, config: Config) -> int:
    """Add a comment to a WorkItem."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    body = args.message
    if not body:
        # Open editor for comment message
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
            tf.write("\n# Enter comment above. Lines starting with '#' will not be ignored.\n")
            tf_path = tf.name
        try:
            subprocess.run(f"{config.editor} {tf_path}", shell=True, check=True)
            body = Path(tf_path).read_text(encoding="utf-8").strip()
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    if not body:
        print("Aborted: Empty comment body.", file=sys.stderr)
        return 1

    author = Author(name=config.user_name, email=config.user_email)
    comment = Comment(
        author=author,
        timestamp=now_iso(),
        body=body,
    )
    item.comments.append(comment)
    item.meta.updated_at = now_iso()
    write_work_item(item)
    print(f"Added comment to {index.get_short_id(item.id)} ({item.title})")
    return 0


def cmd_task_add_dependency(args: argparse.Namespace, config: Config) -> int:
    """Add dependency: child depends on dependency."""
    index = load_index(config.project_root)
    try:
        child = index.resolve(args.child)
        dep = index.resolve(args.dependency)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if dep.id == child.id:
        print("Error: A WorkItem cannot depend on itself.", file=sys.stderr)
        return 1

    child.add_dependency(dep.id)
    child.meta.updated_at = now_iso()
    write_work_item(child)
    print(f"Added dependency: {index.get_short_id(child.id)} depends on {index.get_short_id(dep.id)}")
    return 0


def cmd_task_remove_dependency(args: argparse.Namespace, config: Config) -> int:
    """Remove dependency."""
    index = load_index(config.project_root)
    try:
        child = index.resolve(args.child)
        dep = index.resolve(args.dependency)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    removed = child.remove_dependency(dep.id)
    if removed:
        child.meta.updated_at = now_iso()
        write_work_item(child)
        print(f"Removed dependency: {index.get_short_id(child.id)} on {index.get_short_id(dep.id)}")
    else:
        print(f"Notice: {index.get_short_id(child.id)} did not depend on {index.get_short_id(dep.id)}")
    return 0


def cmd_task_get_dependencies(args: argparse.Namespace, config: Config) -> int:
    """Display dependencies of a WorkItem."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    short_id = index.get_short_id(item.id)
    print(f"Dependencies for {short_id} ({item.title}):")
    deps = index.get_dependencies(item)
    if not deps:
        print("  None")
    else:
        for dep in deps:
            d_short = index.get_short_id(dep.id)
            print(f"  - {d_short}: {dep.title} [{dep.status}]")

    dependents = index.get_dependents(item)
    if dependents:
        print(f"\nItems blocked by {short_id}:")
        for dep in dependents:
            d_short = index.get_short_id(dep.id)
            print(f"  - {d_short}: {dep.title} [{dep.status}]")
    return 0


def cmd_task_update(args: argparse.Namespace, config: Config) -> int:
    """Update frontmatter fields of a WorkItem via CLI flags."""
    index = load_index(config.project_root)
    try:
        item = index.resolve(args.id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    changed = False

    if getattr(args, "title", None):
        item.meta.title = args.title
        changed = True

    if getattr(args, "status", None):
        new_status = args.status.lower().replace("-", "_")
        valid_statuses = config.work_item_statuses
        if valid_statuses and new_status not in valid_statuses:
            print(
                f"Error: Invalid status '{args.status}'. Allowed statuses: {', '.join(valid_statuses.keys())}",
                file=sys.stderr,
            )
            return 1
        item.meta.status = new_status
        changed = True

    if getattr(args, "type", None):
        new_type = args.type.lower()
        valid_types = config.work_item_types
        if valid_types and new_type not in valid_types:
            print(
                f"Error: Invalid type '{args.type}'. Allowed types: {', '.join(valid_types.keys())}",
                file=sys.stderr,
            )
            return 1
        item.meta.type = new_type
        changed = True

    if getattr(args, "size", None):
        new_size = args.size.lower()
        valid_sizes = config.work_item_sizes
        if valid_sizes and new_size not in valid_sizes:
            print(
                f"Error: Invalid size '{args.size}'. Allowed sizes: {', '.join(valid_sizes.keys())}",
                file=sys.stderr,
            )
            return 1
        item.meta.size = new_size
        changed = True

    if getattr(args, "parent", None) is not None:
        if args.parent == "" or args.parent.lower() == "none":
            item.meta.parent = None
        else:
            try:
                parent_item = index.resolve(args.parent)
                item.meta.parent = parent_item.id
            except Exception as e:
                print(f"Error resolving parent '{args.parent}': {e}", file=sys.stderr)
                return 1
        changed = True

    if getattr(args, "tag", None):
        tags = list(item.meta.tags or [])
        raw_tags = args.tag if isinstance(args.tag, list) else [args.tag]
        for t_group in raw_tags:
            for t in t_group.split(","):
                t_clean = t.strip()
                if t_clean and t_clean not in tags:
                    tags.append(t_clean)
        item.meta.tags = tags
        changed = True

    if getattr(args, "overview", None) is not None:
        if "## Overview" in item.body:
            item.body = re.sub(
                r"(## Overview\s*\n)(.*?)(?=\n## |\Z)",
                rf"\g<1>{args.overview}\n",
                item.body,
                count=1,
                flags=re.DOTALL,
            )
        else:
            prefix = f"# {item.title}\n\n" if not item.body.strip() else f"{item.body.rstrip()}\n\n"
            item.body = f"{prefix}## Overview\n{args.overview}\n"
        changed = True

    if not changed:
        print("Error: No update fields specified.", file=sys.stderr)
        return 1

    item.meta.updated_at = now_iso()
    write_work_item(item)
    print(f"Updated WorkItem {index.get_short_id(item.id)} ({item.title})")
    return 0


from ot.validation import Diagnostic, Repairer, Severity, Validator


def cmd_check(args: argparse.Namespace, config: Config) -> int:
    """Validate project state and optionally repair fixable issues."""
    if getattr(args, "fix", False):
        repairer = Repairer(config.project_root)
        repairs = repairer.repair()
        if repairs:
            print("Repairs applied:")
            for r in repairs:
                print(f"  - {r}")
        else:
            print("No automatic repairs needed.")

    validator = Validator(config.project_root)
    diagnostics = validator.validate_all()

    if getattr(args, "json", False):
        print(json.dumps([d.to_dict() for d in diagnostics], indent=2))
        has_errors = any(d.severity == Severity.ERROR for d in diagnostics)
        return 2 if has_errors else 0

    if not diagnostics:
        print("Project check passed: No errors or warnings detected.")
        return 0

    errors = [d for d in diagnostics if d.severity == Severity.ERROR]
    warnings = [d for d in diagnostics if d.severity == Severity.WARNING]
    infos = [d for d in diagnostics if d.severity == Severity.INFO]

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for err in errors:
            loc = f" [{err.file_path.name}]" if err.file_path else ""
            print(f"  [x] {err.category.upper()}{loc}: {err.message}")

    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for warn in warnings:
            loc = f" [{warn.file_path.name}]" if warn.file_path else ""
            fix_note = " (Fixable with --fix)" if warn.is_fixable else ""
            print(f"  [!] {warn.category.upper()}{loc}: {warn.message}{fix_note}")

    if infos:
        print(f"\nInfo ({len(infos)}):")
        for info in infos:
            print(f"  [i] {info.message}")

    print(f"\nCheck summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 2 if errors else 0


from ot.installation import init_project


def cmd_init(args: argparse.Namespace, config: Config) -> int:
    """Initialize a new Open Tasks project."""
    target_dir = args.directory or Path.cwd()
    try:
        res = init_project(
            target_dir=target_dir,
            project_name=args.name,
            version=args.version,
            description=args.description or "",
            install_binary=not args.no_binary,
            create_wrappers=not args.no_wrappers,
        )
        print(f"Initialized Open Tasks project in {res['project_root']}")
        print(f"  Tool version:      {res['version']}")
        print(f"  Templates created: {res['templates_count']}")
        if res.get("binary_path"):
            print(f"  Installed binary:  {res['binary_path']}")
        return 0
    except Exception as e:
        print(f"Initialization failed: {e}", file=sys.stderr)
        return 1


from ot.upgrade import perform_transactional_upgrade


def cmd_upgrade(args: argparse.Namespace, config: Config) -> int:
    """Upgrade project to target version."""
    if not config.project_root:
        print("Error: No Open Tasks project found (.ot).", file=sys.stderr)
        return 1

    try:
        res = perform_transactional_upgrade(
            project_root=config.project_root,
            target_version=args.version,
            mirror_dir=args.mirror,
            dry_run=args.dry_run,
        )
        print(res["message"])
        return 0
    except Exception as e:
        print(f"Upgrade failed: {e}", file=sys.stderr)
        return 1


def cmd_version(args: argparse.Namespace, config: Config) -> int:
    """Print version information."""
    from ot import __version__
    print(f"Open Tasks v{__version__}")
    if config.project_root:
        from ot.version import discover_installed_version, discover_project_version
        cfg_v = discover_project_version(config.project_root)
        inst_v = discover_installed_version(config.project_root)
        print(f"Project root:       {config.project_root}")
        print(f"Configured version: {cfg_v or 'Not specified'}")
        print(f"Installed version:  {inst_v or 'Not installed'}")
    return 0


def _format_config_val(val: object) -> str:
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


def cmd_config_get(args: argparse.Namespace, config: Config) -> int:
    """Retrieve a resolved configuration key."""
    flat_keys = get_flattened_keys(config.raw)
    if args.key not in flat_keys:
        print(f"Error: Configuration key '{args.key}' not found.", file=sys.stderr)
        return 1

    val = config.get(args.key)
    formatted = _format_config_val(val)
    if getattr(args, "show_origin", False):
        origin = config.get_origin(args.key)
        print(f"{origin}\t{formatted}")
    else:
        print(formatted)
    return 0


def cmd_config_set(args: argparse.Namespace, config: Config) -> int:
    """Set a configuration key in local, project, or global config."""
    scope: Optional[str] = None
    if getattr(args, "local", False):
        scope = "local"
    elif getattr(args, "project", False):
        scope = "project"
    elif getattr(args, "global_scope", False):
        scope = "global"

    try:
        target_path, parsed_val, warning = set_config_key(
            config.project_root,
            args.key,
            args.value,
            scope=scope,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if warning:
        print(warning, file=sys.stderr)

    print(f"Set '{args.key}' = {_format_config_val(parsed_val)} in {target_path.name}")
    return 0


def cmd_config_list(args: argparse.Namespace, config: Config) -> int:
    """List all resolved configuration values."""
    leaf_items = config.iter_leaf_items()
    show_origin = getattr(args, "show_origin", False)
    if getattr(args, "json", False):
        if show_origin:
            out = [
                {"key": k, "value": v, "origin": origin}
                for k, v, origin in leaf_items
            ]
        else:
            out = {k: v for k, v, _ in leaf_items}
        print(json.dumps(out, indent=2))
        return 0

    for k, v, origin in leaf_items:
        formatted = _format_config_val(v)
        if show_origin:
            print(f"{origin}\t{k}={formatted}")
        else:
            print(f"{k}={formatted}")
    return 0


def cmd_meeting_start(args: argparse.Namespace, config: Config) -> int:
    """Start a new planning meeting."""
    from datetime import datetime, timezone
    from ot.templates import get_template, render_template

    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    mtype = (args.type or "grooming").strip().lower()
    valid_types = config.get("meeting.types", {}) or {}
    if valid_types and mtype not in valid_types:
        allowed = ", ".join(sorted(valid_types.keys()))
        print(
            f"Error: Invalid meeting type '{mtype}'. Allowed types: {allowed}",
            file=sys.stderr,
        )
        return 1

    meeting_id = generate_uuid()
    started_at = now_iso()
    date_str = started_at[:10]
    ts_folder = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    meeting_dir = config.meetings_dir / mtype / ts_folder
    if meeting_dir.exists():
        meeting_dir = config.meetings_dir / mtype / f"{ts_folder}-{meeting_id[:6]}"
    target_path = meeting_dir / "index.md"

    tmpl_text = get_template(f"meetings/{mtype}.md", config.project_root) or get_template(
        "meetings/grooming.md", config.project_root
    )
    organizer = Author(name=config.user_name, email=config.user_email)
    attendees = list(getattr(args, "attendee", None) or [])
    if not attendees and config.user_name:
        attendees = [
            f"{config.user_name} <{config.user_email}>" if config.user_email else config.user_name
        ]

    if tmpl_text:
        rendered_tmpl = render_template(
            tmpl_text,
            {
                "id": meeting_id,
                "type": mtype,
                "status": "active",
                "started_at": started_at,
                "date": date_str,
                "organizer_name": config.user_name,
                "organizer_email": config.user_email or "",
            },
        )
        meeting = parse_meeting_content(rendered_tmpl, file_path=target_path)
        meeting.id = meeting_id
        meeting.type = mtype
        meeting.status = "active"
        meeting.started_at = started_at
        meeting.organizer = organizer
        meeting.attendees = attendees
    else:
        meeting = Meeting(
            id=meeting_id,
            type=mtype,
            status="active",
            started_at=started_at,
            organizer=organizer,
            attendees=attendees,
            body=f"# {mtype.capitalize()} Meeting - {date_str}\n\n## Notes\n",
            path=target_path,
        )

    written = write_meeting(meeting, target_path)

    if getattr(args, "edit", False) or not getattr(args, "no_edit", False):
        editor = config.editor
        subprocess.run(f"{editor} {written}", shell=True, check=True)
        updated = read_meeting(written)
        write_meeting(updated, written)

    print(f"Started {mtype} meeting {meeting_id[:6]} at {written}")
    return 0


def cmd_meeting_end(args: argparse.Namespace, config: Config) -> int:
    """End an active meeting and record its ended_at timestamp."""
    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    all_meetings = scan_meetings(config.project_root)
    active_meetings = [m for m in all_meetings if m.status == "active"]

    target_query = (getattr(args, "target", None) or "").strip().lower()
    if target_query:
        matched = [
            m
            for m in active_meetings
            if m.type.lower() == target_query
            or m.id.lower().startswith(target_query)
            or (m.path and m.path.parent.name.lower().startswith(target_query))
        ]
    else:
        matched = active_meetings

    if not matched:
        print("Error: No matching active meeting found.", file=sys.stderr)
        return 1

    if len(matched) > 1:
        summary = ", ".join(f"{m.id[:6]} ({m.type})" for m in matched)
        print(
            f"Error: Multiple active meetings found: {summary}. Please specify the meeting ID or type.",
            file=sys.stderr,
        )
        return 1

    mtg = matched[0]
    mtg.status = "ended"
    mtg.ended_at = now_iso()
    write_meeting(mtg)
    print(f"Ended {mtg.type} meeting {mtg.id[:6]} ({mtg.path})")
    print("Reminder: Review and publish meeting notes and work item changes via pull request.")
    return 0


def cmd_meeting_list(args: argparse.Namespace, config: Config) -> int:
    """List meetings in the project."""
    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    meetings = scan_meetings(config.project_root)
    if getattr(args, "status", None):
        st = args.status.strip().lower()
        meetings = [m for m in meetings if m.status.lower() == st]
    if getattr(args, "type", None):
        tp = args.type.strip().lower()
        meetings = [m for m in meetings if m.type.lower() == tp]

    if getattr(args, "json", False):
        print(json.dumps([m.to_dict() for m in meetings], indent=2))
        return 0

    if not meetings:
        print("No meetings found.")
        return 0

    print(f"{'ID':<8} {'Type':<16} {'Status':<10} {'Started':<26} {'Ended'}")
    print("-" * 80)
    for m in meetings:
        short_id = m.id[:6]
        ended_str = m.ended_at or "-"
        print(f"{short_id:<8} {m.type:<16} {m.status:<10} {m.started_at:<26} {ended_str}")
    return 0


def _resolve_owner_document(
    project_root: Path,
    owner_query: str,
) -> tuple[str, Path, Optional[WorkItem], Optional[Meeting]]:
    """Resolve `owner_query` to a WorkItem or Meeting document on disk."""
    index = load_index(project_root)
    try:
        item = index.resolve(owner_query)
        if item.path and item.path.is_file():
            return "work_item", item.path, item, None
    except Exception:
        pass

    q = owner_query.strip().lower()
    dir_matches = [
        it for it in index.all() if it.path and it.path.parent.name.lower() == q
    ]
    if len(dir_matches) == 1 and dir_matches[0].path and dir_matches[0].path.is_file():
        return "work_item", dir_matches[0].path, dir_matches[0], None
    meetings = scan_meetings(project_root)
    matched = [
        m
        for m in meetings
        if m.id.lower().startswith(q)
        or m.type.lower() == q
        or (m.path and m.path.parent.name.lower().startswith(q))
    ]
    if len(matched) == 1 and matched[0].path and matched[0].path.is_file():
        return "meeting", matched[0].path, None, matched[0]
    if len(matched) > 1:
        raise ValueError(f"Ambiguous meeting identifier '{owner_query}'.")
    raise ValueError(f"Could not find WorkItem or Meeting matching '{owner_query}'.")


def cmd_attachment_add(args: argparse.Namespace, config: Config) -> int:
    """Copy a file into <OwnerDir>/attachments/ and append a relative Markdown link."""
    import shutil

    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    src_file = Path(args.file_path).expanduser().resolve()
    if not src_file.is_file():
        print(f"Error: Attachment source file not found: {src_file}", file=sys.stderr)
        return 1

    try:
        kind, doc_path, item, mtg = _resolve_owner_document(config.project_root, args.owner_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    att_dir = doc_path.parent / "attachments"
    att_dir.mkdir(parents=True, exist_ok=True)
    dest_file = att_dir / src_file.name
    if src_file != dest_file:
        shutil.copy2(src_file, dest_file)

    label = getattr(args, "label", None) or src_file.name
    is_img = src_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
    rel_target = f"attachments/{src_file.name}"
    md_link = f"![{label}]({rel_target})" if is_img else f"[{label}]({rel_target})"

    if kind == "work_item" and item:
        if rel_target not in item.body:
            item.body = f"{item.body.rstrip()}\n\n{md_link}\n"
        item.meta.updated_at = now_iso()
        write_work_item(item)
    elif kind == "meeting" and mtg:
        if rel_target not in mtg.body:
            mtg.body = f"{mtg.body.rstrip()}\n\n{md_link}\n"
        write_meeting(mtg)

    print(f"Added attachment '{src_file.name}' to {args.owner_id} ({dest_file})")
    return 0


def cmd_attachment_remove(args: argparse.Namespace, config: Config) -> int:
    """Remove an attachment file and its Markdown reference from the owner document."""
    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    try:
        kind, doc_path, item, mtg = _resolve_owner_document(config.project_root, args.owner_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    filename = Path(args.filename).name
    att_file = doc_path.parent / "attachments" / filename
    removed_any = False

    if att_file.is_file():
        att_file.unlink()
        removed_any = True

    link_pattern = re.compile(
        r"\n*!?\[[^\]]*\]\(attachments/" + re.escape(filename) + r"(?:#[^)]*)?\)\s*"
    )
    if kind == "work_item" and item:
        new_body, count = link_pattern.subn("\n", item.body)
        if count > 0:
            item.body = new_body.strip()
            item.meta.updated_at = now_iso()
            write_work_item(item)
            removed_any = True
    elif kind == "meeting" and mtg:
        new_body, count = link_pattern.subn("\n", mtg.body)
        if count > 0:
            mtg.body = new_body.strip()
            write_meeting(mtg)
            removed_any = True

    if not removed_any:
        print(f"Error: Attachment '{filename}' not found on {args.owner_id}.", file=sys.stderr)
        return 1

    print(f"Removed attachment '{filename}' from {args.owner_id}")
    return 0


def cmd_attachment_list(args: argparse.Namespace, config: Config) -> int:
    """List attachments for a WorkItem or Meeting."""
    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    try:
        _, doc_path, _, _ = _resolve_owner_document(config.project_root, args.owner_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    doc_text = doc_path.read_text(encoding="utf-8")
    att_dir = doc_path.parent / "attachments"
    names: set[str] = set()
    if att_dir.is_dir():
        for f in att_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                names.add(f.name)
    for m in re.finditer(r"!?\[[^\]]*\]\(attachments/([^)#\s]+)", doc_text):
        names.add(m.group(1))

    entries = []
    for name in sorted(names):
        fp = att_dir / name
        exists = fp.is_file()
        size = fp.stat().st_size if exists else 0
        referenced = f"attachments/{name}" in doc_text
        entries.append(
            {
                "name": name,
                "filename": name,
                "path": str(fp),
                "exists": exists,
                "size": size,
                "referenced": referenced,
                "is_image": fp.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"},
            }
        )

    if getattr(args, "json", False):
        print(json.dumps(entries, indent=2))
        return 0

    if not entries:
        print("No attachments found.")
        return 0

    print(f"{'Filename':<28} {'Size':<10} {'Exists':<8} {'Referenced'}")
    print("-" * 64)
    for e in entries:
        print(
            f"{e['filename']:<28} {e['size']:<10} {str(e['exists']):<8} {str(e['referenced'])}"
        )
    return 0


def cmd_attachment_show(args: argparse.Namespace, config: Config) -> int:
    """Display attachment details and referencing lines in the owner document."""
    if not config.project_root:
        print("Error: No Open Tasks project root (.ot) found.", file=sys.stderr)
        return 1

    try:
        _, doc_path, _, _ = _resolve_owner_document(config.project_root, args.owner_id)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    filename = Path(args.filename).name
    fp = doc_path.parent / "attachments" / filename
    doc_text = doc_path.read_text(encoding="utf-8")
    ref_lines = [
        line.strip()
        for line in doc_text.splitlines()
        if f"attachments/{filename}" in line
    ]
    exists = fp.is_file()
    if not exists and not ref_lines:
        print(f"Error: Attachment '{filename}' not found on {args.owner_id}.", file=sys.stderr)
        return 1

    size = fp.stat().st_size if exists else 0
    is_img = fp.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
    if getattr(args, "json", False):
        print(
            json.dumps(
                {
                    "name": filename,
                    "filename": filename,
                    "path": str(fp),
                    "exists": exists,
                    "size": size,
                    "is_image": is_img,
                    "references": ref_lines,
                },
                indent=2,
            )
        )
        return 0

    print(f"Filename:   {filename}")
    print(f"Path:       {fp}")
    print(f"Exists:     {exists}")
    print(f"Size:       {size} bytes")
    print(f"References: {len(ref_lines)}")
    for line in ref_lines:
        print(f"  {line}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    from ot import __version__
    parser = argparse.ArgumentParser(prog="ot", description="Open Tasks (ot) CLI")
    parser.add_argument(
        "--project-dir",
        "-C",
        type=str,
        help="Path to project directory (default: discover from cwd)",
    )
    parser.add_argument(
        "--width",
        type=int,
        help="Override output width in columns",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Proceed with write operations even when the repository is in an unsafe VCS state",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"Open Tasks v{__version__}",
    )

    subparsers = parser.add_subparsers(dest="category")

    # ot version
    subparsers.add_parser("version", help="Show version information")

    # ot init ...
    init_parser = subparsers.add_parser("init", help="Initialize a new Open Tasks project")

    init_parser.add_argument("directory", nargs="?", default=".", help="Directory to initialize (default: current)")
    init_parser.add_argument("--name", "-n", help="Project name")
    init_parser.add_argument("--version", "-v", help="Initial tool version")
    init_parser.add_argument("--description", "-d", help="Project description")
    init_parser.add_argument("--no-binary", action="store_true", help="Skip installing executable zipapp")
    init_parser.add_argument("--no-wrappers", action="store_true", help="Skip creating oat / oat.bat scripts")

    # ot upgrade ...
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade project Open Tasks installation")
    upgrade_parser.add_argument("--version", "-v", required=True, help="Target version to upgrade to")
    upgrade_parser.add_argument("--mirror", "-m", help="Directory containing pre-packaged version artifacts")
    upgrade_parser.add_argument("--dry-run", action="store_true", help="Validate without applying changes")

    # ot check ...
    check_parser = subparsers.add_parser("check", help="Validate project state and configuration")
    check_parser.add_argument("--fix", action="store_true", help="Automatically repair fixable issues")
    check_parser.add_argument("--json", action="store_true", help="Output diagnostics in JSON format")

    # ot config ...
    config_parser = subparsers.add_parser("config", help="Inspect and modify configuration")
    config_sub = config_parser.add_subparsers(dest="command")

    cfg_get_p = config_sub.add_parser("get", help="Get resolved value for a configuration key")
    cfg_get_p.add_argument("key", help="Dot-notation configuration key (e.g. user.editor)")
    cfg_get_p.add_argument("--show-origin", action="store_true", help="Show the layer that supplied the value")

    cfg_set_p = config_sub.add_parser("set", help="Set a configuration key")
    cfg_set_p.add_argument("key", help="Dot-notation configuration key")
    cfg_set_p.add_argument("value", help="Value to set")
    scope_grp = cfg_set_p.add_mutually_exclusive_group()
    scope_grp.add_argument("--local", action="store_true", help="Write to .ot/config.local.json")
    scope_grp.add_argument("--project", action="store_true", help="Write to .ot/config.json")
    scope_grp.add_argument("--global", dest="global_scope", action="store_true", help="Write to ~/.ot/config.json")

    cfg_list_p = config_sub.add_parser("list", help="List resolved configuration values")
    cfg_list_p.add_argument("--show-origin", action="store_true", help="Show origin layer for each key")
    cfg_list_p.add_argument("--json", action="store_true", help="Output in JSON format")

    # ot meeting ...
    meeting_parser = subparsers.add_parser("meeting", help="Planning meeting workflows")
    meeting_sub = meeting_parser.add_subparsers(dest="command")

    mtg_start_p = meeting_sub.add_parser("start", help="Start a new meeting")
    mtg_start_p.add_argument("--type", "-t", default="grooming", help="Meeting type (default: grooming)")
    mtg_start_p.add_argument("--attendee", action="append", help="Meeting attendee (repeatable)")
    mtg_start_p.add_argument("--no-edit", action="store_true", help="Do not launch editor")
    mtg_start_p.add_argument("--edit", action="store_true", help="Launch editor after creating meeting")

    mtg_end_p = meeting_sub.add_parser("end", help="End an active meeting")
    mtg_end_p.add_argument("target", nargs="?", help="Optional meeting ID or type to end")

    mtg_list_p = meeting_sub.add_parser("list", help="List meetings")
    mtg_list_p.add_argument("--status", "-s", help="Filter by status (active, ended)")
    mtg_list_p.add_argument("--type", "-t", help="Filter by meeting type")
    mtg_list_p.add_argument("--json", action="store_true", help="Output in JSON format")

    # ot attachment ...
    att_parser = subparsers.add_parser("attachment", help="Manage work item and meeting attachments")
    att_sub = att_parser.add_subparsers(dest="command")

    att_add_p = att_sub.add_parser("add", help="Add an attachment to a WorkItem or Meeting")
    att_add_p.add_argument("owner_id", help="WorkItem or Meeting ID/title/type")
    att_add_p.add_argument("file_path", help="Path to file to attach")
    att_add_p.add_argument("--label", "-l", help="Optional Markdown link label")

    att_rm_p = att_sub.add_parser("remove", help="Remove an attachment from a WorkItem or Meeting")
    att_rm_p.add_argument("owner_id", help="WorkItem or Meeting ID/title/type")
    att_rm_p.add_argument("filename", help="Attachment filename")

    att_list_p = att_sub.add_parser("list", help="List attachments for a WorkItem or Meeting")
    att_list_p.add_argument("owner_id", help="WorkItem or Meeting ID/title/type")
    att_list_p.add_argument("--json", action="store_true", help="Output in JSON format")

    att_show_p = att_sub.add_parser("show", help="Show details of an attachment")
    att_show_p.add_argument("owner_id", help="WorkItem or Meeting ID/title/type")
    att_show_p.add_argument("filename", help="Attachment filename")
    att_show_p.add_argument("--json", action="store_true", help="Output in JSON format")

    # ot task ...
    task_parser = subparsers.add_parser("task", help="WorkItem management")
    task_sub = task_parser.add_subparsers(dest="command")

    # list
    list_p = task_sub.add_parser("list", help="List work items")
    list_p.add_argument("ids", nargs="*", help="Optional task IDs (space or comma separated)")
    list_p.add_argument("--id", action="append", help="Filter by ID prefix (repeatable or comma-separated)")
    list_p.add_argument("--title", action="append", help="Filter by title prefix (repeatable or comma-separated)")
    list_p.add_argument("--status", "-s", action="append", help="Filter by status (repeatable or comma-separated)")
    list_p.add_argument("--type", "-t", action="append", help="Filter by type (repeatable or comma-separated)")
    list_p.add_argument("--size", action="append", help="Filter by size (repeatable or comma-separated)")
    list_p.add_argument("--tag", action="append", help="Filter by tag (repeatable or comma-separated)")
    list_p.add_argument("--author", action="append", help="Filter by author name/email substring or /regex/")
    list_p.add_argument("--width", type=int, default=argparse.SUPPRESS, help="Override output width in columns")
    list_p.add_argument("--json", action="store_true", help="Output in JSON format")

    # show
    show_p = task_sub.add_parser("show", help="Show work item details")
    show_p.add_argument("id", help="WorkItem ID, short ID, or title")

    # create
    create_p = task_sub.add_parser("create", help="Create a new work item")
    create_p.add_argument("positional_title", nargs="?", metavar="title", help="WorkItem title")
    create_p.add_argument("--title", "-m", type=str, help="WorkItem title")
    create_p.add_argument("--type", "-t", type=str, default="task", help="WorkItem type")
    create_p.add_argument("--status", "-s", type=str, default="triage", help="Initial status")
    create_p.add_argument("--size", type=str, help="WorkItem size")
    create_p.add_argument("--parent", "-p", type=str, help="Parent WorkItem ID or short ID")
    create_p.add_argument("--overview", type=str, help="Overview summary")
    create_p.add_argument("--no-edit", action="store_true", help="Do not launch editor")
    create_p.add_argument("--edit", action="store_true", help="Launch editor after setup")

    # edit
    edit_p = task_sub.add_parser("edit", help="Edit a work item")
    edit_p.add_argument("id", help="WorkItem ID, short ID, or title")

    # update
    update_p = task_sub.add_parser("update", help="Update work item fields via CLI flags")
    update_p.add_argument("id", help="WorkItem ID, short ID, or title")
    update_p.add_argument("--title", "-m", type=str, help="New WorkItem title")
    update_p.add_argument("--type", "-t", type=str, help="New WorkItem type")
    update_p.add_argument("--status", "-s", type=str, help="New WorkItem status")
    update_p.add_argument("--size", type=str, help="New WorkItem size")
    update_p.add_argument("--parent", "-p", type=str, help="New parent WorkItem ID or short ID")
    update_p.add_argument("--tag", action="append", help="Tag(s) to add to the WorkItem")
    update_p.add_argument("--overview", type=str, help="New overview text")

    # status
    status_p = task_sub.add_parser("status", help="Update work item status")
    status_p.add_argument("id", help="WorkItem ID or short ID")
    status_p.add_argument("status", help="New status value")

    # comment
    comment_p = task_sub.add_parser("comment", help="Add comment to work item")
    comment_p.add_argument("id", help="WorkItem ID or short ID")
    comment_p.add_argument("message", nargs="?", help="Comment body (optional)")

    # add-dependency
    add_dep_p = task_sub.add_parser("add-dependency", help="Add dependency relationship")
    add_dep_p.add_argument("child", help="Target child WorkItem ID or short ID")
    add_dep_p.add_argument("dependency", help="Dependency WorkItem ID or short ID")

    # remove-dependency
    rm_dep_p = task_sub.add_parser("remove-dependency", help="Remove dependency relationship")
    rm_dep_p.add_argument("child", help="Target child WorkItem ID or short ID")
    rm_dep_p.add_argument("dependency", help="Dependency WorkItem ID or short ID")

    # get-dependencies
    get_dep_p = task_sub.add_parser("get-dependencies", help="Get work item dependencies")
    get_dep_p.add_argument("id", help="WorkItem ID or short ID")

    # Allow --force after mutating subcommands as well
    for mut_p in (
        init_parser,
        upgrade_parser,
        check_parser,
        cfg_set_p,
        mtg_start_p,
        mtg_end_p,
        att_add_p,
        att_rm_p,
        create_p,
        edit_p,
        update_p,
        status_p,
        comment_p,
        add_dep_p,
        rm_dep_p,
    ):
        mut_p.add_argument(
            "--force",
            action="store_true",
            default=argparse.SUPPRESS,
            help="Proceed with write operations even when the repository is in an unsafe VCS state",
        )

    return parser


def _is_mutating_command(parsed: argparse.Namespace) -> bool:
    cat = parsed.category
    cmd = getattr(parsed, "command", None)
    if cat in ("init", "upgrade"):
        return True
    if cat == "check" and getattr(parsed, "fix", False):
        return True
    if cat == "config" and cmd == "set":
        return True
    if cat == "task" and cmd in (
        "create",
        "edit",
        "update",
        "status",
        "comment",
        "add-dependency",
        "remove-dependency",
    ):
        return True
    if cat == "meeting" and cmd in ("start", "end"):
        return True
    if cat == "attachment" and cmd in ("add", "remove"):
        return True
    return False


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.category:
        parser.print_help()
        return 0

    config = load_config(parsed.project_dir)

    if _is_mutating_command(parsed) and not getattr(parsed, "force", False):
        if parsed.category == "init":
            check_dir = Path(getattr(parsed, "directory", ".")).resolve()
        else:
            check_dir = config.project_root or Path(parsed.project_dir or ".").resolve()
        is_safe, reason = check_vcs_safety(check_dir)
        if not is_safe:
            print(f"Error: {reason}", file=sys.stderr)
            return 1

    if parsed.category == "version":
        return cmd_version(parsed, config)

    if parsed.category == "init":
        return cmd_init(parsed, config)

    if parsed.category == "upgrade":
        return cmd_upgrade(parsed, config)

    if parsed.category == "check":
        return cmd_check(parsed, config)

    if parsed.category == "config":
        if parsed.command == "get":
            return cmd_config_get(parsed, config)
        elif parsed.command == "set":
            return cmd_config_set(parsed, config)
        elif parsed.command == "list":
            return cmd_config_list(parsed, config)
        else:
            parser.print_help()
            return 1

    if parsed.category == "meeting":
        if parsed.command == "start":
            return cmd_meeting_start(parsed, config)
        elif parsed.command == "end":
            return cmd_meeting_end(parsed, config)
        elif parsed.command == "list":
            return cmd_meeting_list(parsed, config)
        else:
            parser.print_help()
            return 1

    if parsed.category == "attachment":
        if parsed.command == "add":
            return cmd_attachment_add(parsed, config)
        elif parsed.command == "remove":
            return cmd_attachment_remove(parsed, config)
        elif parsed.command == "list":
            return cmd_attachment_list(parsed, config)
        elif parsed.command == "show":
            return cmd_attachment_show(parsed, config)
        else:
            parser.print_help()
            return 1


    if parsed.category == "task":
        if parsed.command == "list":
            return cmd_task_list(parsed, config)
        elif parsed.command == "show":
            return cmd_task_show(parsed, config)
        elif parsed.command == "create":
            return cmd_task_create(parsed, config)
        elif parsed.command == "edit":
            return cmd_task_edit(parsed, config)
        elif parsed.command == "update":
            return cmd_task_update(parsed, config)
        elif parsed.command == "status":
            return cmd_task_status(parsed, config)
        elif parsed.command == "comment":
            return cmd_task_comment(parsed, config)
        elif parsed.command == "add-dependency":
            return cmd_task_add_dependency(parsed, config)
        elif parsed.command == "remove-dependency":
            return cmd_task_remove_dependency(parsed, config)
        elif parsed.command == "get-dependencies":
            return cmd_task_get_dependencies(parsed, config)
        else:
            parser.print_help()
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())



