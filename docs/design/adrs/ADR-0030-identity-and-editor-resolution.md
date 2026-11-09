# ADR-0030 - Identity And Editor Resolution

Status:
Accepted

Context:

OT requires identity information for:

- Comments
- Meeting attendance
- Audit information

OT also requires an editor for interactive workflows.

Identity may originate from:

- OT configuration
- Git configuration
- Mercurial configuration
- Environment variables
- System defaults

Decision:

Identity and editor settings shall be resolved using a deterministic precedence chain.

Resolution order:

1. .ot/config.local.json
2. .ot/config.json
3. ~/.ot/config.json
4. Supported VCS commands
5. Environment variables
6. System defaults

Git and Mercurial configuration shall be obtained using VCS commands rather than direct file parsing.

Reasoning:

Users should have predictable control over configuration.

Using VCS commands delegates configuration discovery to the VCS implementation.

Alternatives Considered:

### Direct File Parsing

Pros:

- No subprocess execution

Cons:

- VCS-specific parsing logic
- Duplicate behavior

### Environment Variables First

Pros:

- Familiar to some users

Cons:

- Less predictable

Consequences:

Positive:

- Deterministic behavior
- Simpler maintenance
- Better VCS compatibility

Negative:

- Some configuration lookups require subprocess execution

## Amendments (As-Built)

- **Environment Variable Names & System Fallbacks (`src/ot/discovery.py`, `src/ot/config.py`)**:
  - **User Name**: After `.ot/config.local.json`, `.ot/config.json`, `~/.ot/config.json`, and `git config user.name`, resolution checks `OT_USER`, `USER`, `USERNAME`, `LOGNAME`, `getpass.getuser()`, and finally `"Anonymous"`.
  - **User Email**: After config layers and `git config user.email`, resolution checks the `EMAIL` environment variable (defaulting to `None` if unset).
  - **Editor**: After config layers and `git config core.editor`, resolution checks `EDITOR`, `VISUAL`, and platform defaults (`notepad.exe` on Windows `win32`, `nano` on POSIX).
- **Mercurial Config Queries Pending**: Only Git (`git config`) is currently queried in step 4; Mercurial (`hg config ui.username` / `ui.editor`) is tracked in task `3109b3` (*Mercurial VCS Integration*).

