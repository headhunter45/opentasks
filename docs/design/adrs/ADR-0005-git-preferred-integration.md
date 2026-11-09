# ADR-0005 - Git Preferred Integration

Status:
Accepted

Context:

While version control is optional, OT benefits from integrating with available source control systems.

Git has the highest expected usage among OT users.

Mercurial support is desirable but secondary.

Decision:

Recognized version control systems shall be prioritized in the following order:

1. Git
2. No version control
3. Mercurial
4. Other supported systems

Git integration should receive the greatest implementation effort.

Reasoning:

Git provides:

- User identity
- Email configuration
- Editor configuration
- Repository root detection
- Merge and rebase safety information

Most users are expected to use Git.

Alternatives Considered:

### Git Only

Pros:

- Simpler implementation

Cons:

- Excludes valid users

### Equal Support For All Systems

Pros:

- Broad compatibility

Cons:

- Significant implementation effort
- Complex testing requirements
- Unnecessary for early versions

Consequences:

Positive:

- Strong Git experience
- Future Mercurial support remains possible
- Core architecture remains version-control independent

Negative:

- Some integrations may behave differently across systems
- Additional abstraction layers may be required in the future

## Amendments (As-Built)

- **Git, Mercurial, and No-VCS Integration (`src/ot/discovery.py`, `src/ot/config.py`)**:
  - `find_vcs_root` detects both `.git` and `.hg` repositories.
  - Identity and editor resolution queries Git (`git config user.name`, `user.email`, `core.editor`) and Mercurial (`hg config ui.username`, `hg config ui.editor`, with `.hg/hgrc` fallback; task `3109b3`), prioritizing the active repository's VCS before falling back to environment variables and system defaults (`get_system_identity`, `get_system_editor`).


