"""Template generation, installation, and rendering for Open Tasks."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from ot.discovery import find_project_root

DEFAULT_TEMPLATES: Dict[str, str] = {
    "tasks/default.md": """---
id: {{id}}
title: {{title}}
type: {{type}}
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags: []
---

# {{title}}

## Overview

Describe the goal, context, and requirements for this work item.

## Acceptance Criteria

- [ ] Define requirements
- [ ] Implement changes
- [ ] Verify functionality
""",
    "tasks/bug.md": """---
id: {{id}}
title: {{title}}
type: bug
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags:
  - bug
---

# {{title}}

## Problem Summary

Describe the unexpected behavior or error observed.

## Steps to Reproduce

1. First step
2. Second step
3. Observe failure

## Expected Behavior

Describe what should have happened instead.
""",
    "tasks/feature.md": """---
id: {{id}}
title: {{title}}
type: feature
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags:
  - feature
---

# {{title}}

## Summary

Describe the user-facing feature or enhancement.

## Requirements

- [ ] Requirement 1
- [ ] Requirement 2

## Design / Technical Notes

Architecture decisions and technical implementation details.
""",
    "tasks/epic.md": """---
id: {{id}}
title: {{title}}
type: epic
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags:
  - epic
---

# {{title}}

## Objective

High-level goals and deliverables for this initiative.

## Subtasks & Deliverables

- [ ] Core milestone deliverables
""",
    "tasks/spike.md": """---
id: {{id}}
title: {{title}}
type: spike
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags:
  - spike
  - research
---

# {{title}}

## Research Questions

What questions must this time-boxed investigation answer?

## Findings & Recommendations

Record investigation results and next steps.
""",
    "tasks/chore.md": """---
id: {{id}}
title: {{title}}
type: chore
status: {{status}}
size: {{size}}
created_at: {{created_at}}
author:
  name: {{author_name}}
  email: {{author_email}}
tags:
  - chore
---

# {{title}}

## Task Summary

Routine maintenance, cleanup, or dependencies update.
""",
    "meetings/grooming.md": """---
type: grooming
date: {{date}}
attendees: []
---

# Backlog Grooming - {{date}}

## Agenda

- Review incoming triage items
- Estimate sizing and requirements

## Action Items

- [ ] Item 1
""",
    "meetings/planning.md": """---
type: planning
date: {{date}}
attendees: []
---

# Sprint Planning - {{date}}

## Goals

- Prioritize items for next cycle

## Selected WorkItems

- [ ] Item 1
""",
    "meetings/retrospective.md": """---
type: retrospective
date: {{date}}
attendees: []
---

# Retrospective - {{date}}

## What Went Well

## What Could Be Improved

## Action Items
""",
    "meetings/ideation.md": """---
type: ideation
date: {{date}}
attendees: []
---

# Ideation & Brainstorming - {{date}}

## Topic

## Discussion Notes
""",
    "shared/comment.md": """### Comment by {{author_name}} on {{timestamp}}
<!-- comment-id: {{comment_id}} -->

{{body}}
""",
}


def install_default_templates(project_root: Optional[Path | str] = None, overwrite: bool = False) -> int:
    """Install default template files into configured templates directory (default .ot/templates/).

    Returns the count of new templates installed.
    """
    root = find_project_root(project_root)
    if not root:
        return 0

    try:
        from ot.config import load_config
        templates_dir = load_config(root).templates_dir
    except Exception:
        templates_dir = root / ".ot" / "templates"
    installed_count = 0

    for rel_path, content in DEFAULT_TEMPLATES.items():
        dest = templates_dir / rel_path
        if not dest.exists() or overwrite:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content.strip() + "\n", encoding="utf-8")
            installed_count += 1

    return installed_count


def get_template(
    name: str,
    project_root: Optional[Path | str] = None,
) -> Optional[str]:
    """Retrieve template content by name (e.g. 'tasks/bug.md' or 'tasks/default.md').

    Checks project-local configured templates directory first, falling back to built-in templates.
    """
    root = find_project_root(project_root)
    if root:
        try:
            from ot.config import load_config
            templates_dir = load_config(root).templates_dir
        except Exception:
            templates_dir = root / ".ot" / "templates"
        local_file = templates_dir / name
        if local_file.is_file():
            return local_file.read_text(encoding="utf-8")

    return DEFAULT_TEMPLATES.get(name)


def render_template(template_text: str, context: Dict[str, Optional[str]]) -> str:
    """Substitute `{{key}}` placeholders in `template_text` with values from `context`."""
    import re

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        if key in context:
            val = context[key]
            return "" if val is None else str(val)
        return match.group(0)

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", _replace, template_text)

