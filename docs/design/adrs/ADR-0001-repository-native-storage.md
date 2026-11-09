# ADR-0001 - Repository Native Storage

Status:
Accepted

Context:

Open Tasks (ot) is intended to manage work items, planning information, meetings, and related project artifacts.

A fundamental decision is where OT stores its data.

Possible approaches include:

- Repository files
- Local application data
- Hosted services
- Databases
- Hybrid approaches

The project goal is to make work tracking a natural extension of existing development workflows.

Decision:

Store all OT project data inside the project itself.

This includes:

- Work items
- Meetings
- Planning documents
- Templates
- Configuration
- Attachments

The repository contents are the system of record.

Reasoning:

Source control systems already provide:

- History
- Branching
- Merging
- Review workflows
- Distribution
- Backup

Using repository files allows OT to leverage these capabilities rather than reimplementing them.

Alternatives Considered:

### Database Backend

Pros:

- Easy reporting
- Centralized access
- Familiar enterprise workflow

Cons:

- Requires infrastructure
- Requires synchronization
- Requires migration support
- Introduces availability concerns
- Introduces backup concerns

### Hosted Service

Pros:

- Accessible from anywhere
- Familiar user experience

Cons:

- Requires service operation
- Requires authentication
- Requires network access
- Creates vendor dependence

### Local Application Data

Pros:

- Simple implementation

Cons:

- Difficult collaboration
- Hard to review
- Not naturally versioned

Consequences:

Positive:

- Offline operation
- Natural Git workflows
- Reviewable changes
- Portable repositories
- No service dependencies

Negative:

- Reporting may require file scans
- Large repositories may require optimization
- Users must understand source control workflows

## Amendments (As-Built)

- **Implemented Repository Artifacts**: Work items (`.ot/tasks/`), templates (`.ot/templates/`), and project configuration (`.ot/config.json`) are stored and managed in the repository.
- **Deferred / Partial Scope**:
  - Dedicated CLI commands for meetings (`ot meeting ...`) and attachments (`ot attachment ...`) are tracked in tasks `a9baac` and `ba1cd2`.

