# Shared global Dispatch runtime

## Decision

Each Edge Node has one Release Operator-managed Dispatch dependency runtime.
The runtime lives under `/ads_storage/dispatch/.venv/`, while configuration,
jobs, logs, and telemetry remain private under
`/ads_storage/<user>/.dispatch/`.

Runtimes are immutable after construction and are identified by the verified
dependency bundle's 64-character SHA-256 `bundle_digest`, not by a Git commit.
They are built at their final physical path,
`.venv/releases/<bundle-digest>/`, because virtual-environment entry points
embed absolute paths. A runtime becomes eligible for use only after its
dependencies install offline, `pip check` succeeds, required imports succeed,
and completion metadata is written.

Activation atomically replaces the `.venv/current` symlink. The shared
launcher resolves that symlink to a physical directory before executing
Python, so a process that is already running remains bound to its original
runtime when a later release is activated. Completed runtimes are reusable,
including for source-only releases and explicit rollback. Old runtimes are not
deleted automatically.

`install.sh` is the non-interactive Release Operator interface. It installs or
reactivates the shared runtime and never changes user state. `onboard.sh` is
the user interface. It creates or repairs private state and a thin launcher,
but never reads dependency bundles, creates a virtual environment, or runs
pip.

## Ownership and permissions

The Release Operator owns `.venv/`, its installation lock, every release
directory, and the `current` symlink. Completed runtimes are readable and
executable by analysts but writable only by their owner. The shared repository
is readable and traversable by analysts. Repository updates must not
recursively change `.venv/` permissions.

Each analyst owns their `.dispatch` directory with mode `0700`; configuration
and source-version metadata use mode `0600`. One user's state is never shared
with another user.

## Consequences

- A dependency change creates and validates a new digest-specific runtime.
- A source-only release reuses the active dependency runtime.
- Failed construction cannot replace the active runtime.
- Rollback is an activation of a previously completed runtime and needs no
  download or rebuild.
- Existing personal virtual environments are left untouched during migration.
- Users repair stale launchers by rerunning `onboard.sh`; they never run pip.

