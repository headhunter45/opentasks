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

from ot.config import Config, load_config
from ot.discovery import discover_root, find_project_root
from ot.identifiers import generate_uuid
from ot.models import Author, Comment, WorkItem, WorkItemMetadata, now_iso
from ot.parser import parse_work_item_content, read_work_item, render_work_item, write_work_item
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
    items = index.filter(
        item_type=args.type,
        status=args.status,
        size=args.size,
        tag=args.tag,
        author_name=args.author,
    )

    if getattr(args, "json", False):
        data = []
        for item in items:
            d = item.meta.to_dict()
            d["short_id"] = index.get_short_id(item.id)
            data.append(d)
        print(json.dumps(data, indent=2))
        return 0

    if not items:
        print("No work items found.")
        return 0

    total_width = resolve_output_width(args, config)
    title_width = max(20, total_width - 35)
    header = f"{'ID':<8} {'Title':<{title_width}} {'Type':<12} {'Status':<12}"
    divider = f"{'-'*8} {'-'*title_width} {'-'*12} {'-'*12}"
    print(header)
    print(divider)
    for item in items:
        short_id = index.get_short_id(item.id)
        print(format_task_row(short_id, item, total_width=total_width))
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
        print("\n--- Comments ---")
        for comment in item.comments:
            print()
            print(comment.to_markdown().strip())

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

    meta = WorkItemMetadata(
        id=item_id,
        title=title,
        type=item_type,
        status=status,
        size=size,
        author=author,
        parent=parent_id,
        created_at=now_iso(),
    )

    body_overview = args.overview or ""
    body = f"# {title}\n\n## Overview\n{body_overview}\n" if title else ""

    item = WorkItem(meta=meta, body=body)

    # Determine file location
    tasks_dir = config.project_root / ".ot" / "tasks"
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
        rendered = render_work_item(item)
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
            tf.write(rendered)
            tf_path = tf.name

        editor = config.editor
        try:
            subprocess.run(f"{editor} {tf_path}", shell=True, check=True)
            new_content = Path(tf_path).read_text(encoding="utf-8")
            item = parse_work_item_content(new_content)
        finally:
            if os.path.exists(tf_path):
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
    rendered = render_work_item(item)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tf:
        tf.write(rendered)
        tf_path = tf.name

    editor = config.editor
    try:
        subprocess.run(f"{editor} {tf_path}", shell=True, check=True)
        new_content = Path(tf_path).read_text(encoding="utf-8")
        updated_item = parse_work_item_content(new_content, file_path=item.path)
        updated_item.meta.updated_at = now_iso()
        write_work_item(updated_item)
        print(f"Updated WorkItem {index.get_short_id(item.id)} ({updated_item.title})")
        return 0
    finally:
        if os.path.exists(tf_path):
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
    init_parser.add_argument("--no-wrappers", action="store_true", help="Skip creating otw / otw.bat scripts")

    # ot upgrade ...
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade project Open Tasks installation")
    upgrade_parser.add_argument("--version", "-v", required=True, help="Target version to upgrade to")
    upgrade_parser.add_argument("--mirror", "-m", help="Directory containing pre-packaged version artifacts")
    upgrade_parser.add_argument("--dry-run", action="store_true", help="Validate without applying changes")

    # ot check ...
    check_parser = subparsers.add_parser("check", help="Validate project state and configuration")
    check_parser.add_argument("--fix", action="store_true", help="Automatically repair fixable issues")
    check_parser.add_argument("--json", action="store_true", help="Output diagnostics in JSON format")

    # ot task ...
    task_parser = subparsers.add_parser("task", help="WorkItem management")
    task_sub = task_parser.add_subparsers(dest="command")

    # list
    list_p = task_sub.add_parser("list", help="List work items")
    list_p.add_argument("--status", "-s", action="append", help="Filter by status (repeatable or comma-separated)")
    list_p.add_argument("--type", "-t", action="append", help="Filter by type (repeatable or comma-separated)")
    list_p.add_argument("--size", action="append", help="Filter by size (repeatable or comma-separated)")
    list_p.add_argument("--tag", action="append", help="Filter by tag (repeatable or comma-separated)")
    list_p.add_argument("--author", action="append", help="Filter by author name (repeatable or comma-separated)")
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

    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.category:
        parser.print_help()
        return 0

    config = load_config(parsed.project_dir)

    if parsed.category == "version":
        return cmd_version(parsed, config)

    if parsed.category == "init":
        return cmd_init(parsed, config)

    if parsed.category == "upgrade":
        return cmd_upgrade(parsed, config)

    if parsed.category == "check":
        return cmd_check(parsed, config)


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



