# Open Tasks (ot)

Open Tasks is a repository-native, database-free task and planning management tool designed for modern development workflows.

---

## Key Features

- **Repository-Native Storage**: All tasks, bugs, epics, and meeting notes are stored as Markdown documents with YAML frontmatter in `.ot/tasks/`.
- **Database-Free**: Everything is persisted directly in Git or your local filesystem.
- **UUID & Git-Style Short Identifiers**: Stable UUID-backed internal references with convenient, unambiguous short prefix identifiers for human interaction.
- **Direct File Editing**: Seamless round-trip editing via text editors or the CLI without loss of custom user sections.
- **Dependency & Hierarchy Graphs**: Unified WorkItem model supporting arbitrary parent/child nesting and bidirectional blocker/dependency tracking.
- **First-Class Validation & Repair**: `ot check` and `ot check --fix` for automatic detection and repair of configuration and filesystem inconsistencies.

---

## Quick Start

### Installation

Install the standalone executable launcher:

```bash
curl -fsSL https://headhunter45.github.io/opentasks/install.sh | bash
```

Or download the latest standalone binary directly from [GitHub Releases](https://github.com/headhunter45/opentasks/releases/latest).

### Repository Workflow

Open Tasks self-hosts its own task tracking directly within this repository using the `./oat` project wrapper:

```bash
# Verify project version & integrity
./oat version
./oat check

# Query the active backlog (supports multi-column, comma-separated, prefix, and positional ID filtering)
./oat task list -s triage,planned,in_progress

# Create a new feature task
./oat task create "My New Feature" --type feature --size medium

# Update a task's status or frontmatter fields
./oat task update "My New Feature" --status in_progress --tag core
```

### Running Unit Tests & Coverage
 
```bash
# Standard library test runner
PYTHONPATH=src python3 -m unittest discover -s tests

# Run tests with HTML and LCOV coverage reports
pip install -r requirements-dev.txt
./scripts/test-coverage
```

---

## Documentation & Architecture

* **Web Portal & Guides**: [https://headhunter45.github.io/opentasks/](https://headhunter45.github.io/opentasks/)
* **Architecture Decision Records (ADRs)**: [docs/design/adrs/](docs/design/adrs/)
* **Design Specifications**: [docs/design/](docs/design/)
