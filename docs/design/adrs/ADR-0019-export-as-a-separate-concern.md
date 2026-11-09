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

- **Built-in JSON CLI Output**: In addition to storing open Markdown/YAML files on disk, `ot task list --json` and `ot check --json` emit structured JSON directly from the CLI (`src/ot/cli.py`) so external reporting scripts, dashboards, and CI pipelines can consume Open Tasks data without writing custom Markdown parsers. Formal JSON Schema definitions and export tooling are tracked under Epic `474111` (*Export and Reporting Tooling*) and Task `d2c34f` (*JSON Schema Export*).

