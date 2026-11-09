# ADR-0019 - Export as a Separate Concern

Status:
Accepted

Context:

Users may wish to publish data from OT to:

- Reporting systems
- Dashboards
- Wikis
- Issue trackers
- Internal tooling

OT cannot realistically support every target system.

Decision:

OT shall expose repository data using open file formats.

Exporters are separate tools that consume repository data and publish it elsewhere.

OT itself does not own downstream integrations.

Reasoning:

OT should focus on maintaining repository-native project data.

Export processes are naturally isolated from planning workflows.

Alternatives Considered:

### Built-In Integrations

Pros:

- Convenience

Cons:

- Large support burden
- Expanding scope

### Bidirectional Synchronization

Pros:

- Near real-time updates

Cons:

- Multiple sources of truth
- Conflict resolution complexity

Consequences:

Positive:

- Smaller core system
- Easier maintenance
- Clear ownership boundaries

Negative:

- External tools must be developed separately

## Amendments (As-Built)

- **Built-in JSON CLI Output & JSON Schema Export (`src/ot/cli.py`, `src/ot/schema.py`)**: In addition to storing open Markdown/YAML files on disk, `ot task list --json`, `ot meeting list --json`, `ot attachment list --json`, `ot config list --json`, and `ot check --json` emit structured JSON directly from the CLI, and `ot schema [all|config|work-item|meeting] [--output <path>]` (plus `ot config schema`) generates JSON Schema Draft 2020-12 definitions dynamically tailored to the project's configured types, statuses, and sizes (Epic `474111`, Task `d2c34f`).

