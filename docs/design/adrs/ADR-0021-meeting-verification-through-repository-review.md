# ADR-0021 - Meeting Verification Through Repository Review

Status:
Accepted

Context:

Meeting outcomes may affect:

- Work item status
- Priorities
- Sprint assignments
- Requirements

The participants in a meeting should have a mechanism to verify the recorded outcomes.

Decision:

Meeting records should be reviewed through repository workflows.

Team members who attended a meeting should be encouraged to review and approve the resulting changes.

Reasoning:

Pull request approval already provides:

- Identity
- Timestamping
- Discussion
- Audit history

Alternatives Considered:

### Dedicated Approval Tracking

Pros:

- Explicit meeting workflow

Cons:

- Additional system complexity

### No Verification

Pros:

- Simpler workflow

Cons:

- Increased disputes
- Less confidence in records

Consequences:

Positive:

- Shared accountability
- Historical record
- Reduced implementation complexity

Negative:

- Requires repository workflows

## Amendments (As-Built)

- **Meeting Lifecycle & Pull Request Reminder (`src/ot/cli.py`, `src/ot/parser.py`)**: `ot meeting start`, `ot meeting end`, and `ot meeting list` manage meeting records under `<meetings_dir>/<type>/<YYYY-MM-DDTHH-MM-SS>/index.md`, and `ot meeting end` prints a reminder encouraging attendees to review and publish meeting notes and work item changes via pull request (task `a9baac`).

