# Shared Global Dispatch Runtime Implementation Plan

## Problem statement

Dispatch's source tree is shared, but its Python virtual environment and
dependency bundle are currently user-specific. Users can see and execute
`/ads_storage/dispatch`, yet their personal runtime may be absent, stale, or
incomplete.

The desired model is:

- one Release Operator-managed Python runtime per Edge Node;
- immutable, versioned dependency environments;
- atomic activation and rollback;
- private configuration, jobs, logs, and telemetry per user;
- no dependency bundle or package installation during user onboarding.

## Target architecture

```text
/ads_storage/dispatch/
|-- .venv/
|   |-- releases/
|   |   |-- <bundle-digest-A>/
|   |   `-- <bundle-digest-B>/
|   |-- current -> releases/<active-bundle-digest>
|   `-- install.lock
|-- bin/
|   `-- dispatch
|-- dispatch/
|-- scr/
|-- install.sh
`-- onboard.sh

/ads_storage/<user>/.dispatch/
|-- config.json
|-- jobs/
|-- telemetry/
`-- dispatch.log

~/.local/bin/dispatch
`-- thin wrapper pointing to /ads_storage/dispatch/bin/dispatch
```

The runtime identifier is the verified dependency bundle digest, not the Git
commit. Source-only releases can reuse the same environment; dependency
changes create a new one.

## Module design

### Shared Runtime module

Its interface accepts:

- the verified dependency bundle;
- the approved Python interpreter;
- the shared repository root.

Its guarantees:

- the active runtime always passed offline installation and `pip check`;
- failed installation never changes the active runtime;
- consumers cannot modify the runtime;
- activation is an atomic `current` symlink update;
- an existing complete runtime with the same bundle digest is reused;
- the installer never modifies user configuration or jobs.

All locking, bundle-manifest parsing, runtime reuse, permissions, completion
markers, and activation stay behind this interface.

### Shared Launcher module

Its interface is simply "launch Dispatch with the caller's arguments."

Its implementation:

- resolves `current` to a physical runtime path before starting Python;
- exports the shared source and orchestrator locations;
- preserves the caller's current directory;
- leaves user identity and data-root discovery unchanged;
- fails clearly if no runtime is active.

Resolving the physical path is important: a process already running must
remain tied to its original environment if `current` changes later.

### User Onboarding module

Its interface creates or repairs one user's private Dispatch state.

It:

- creates private configuration and job directories;
- collects the user's email if necessary;
- installs a thin launcher in the user's existing `PATH`;
- verifies that the global runtime is active;
- never reads a dependency bundle;
- never creates a venv;
- never runs pip.

## Tiny-commit implementation plan

### Commit 1 - Document the runtime ownership decision

Record the architectural decision that dependencies are Edge Node-global while
configuration, jobs, logs, and telemetry remain per-user.

Define:

- ownership and permission invariants;
- runtime digest identity;
- activation and rollback behavior;
- the distinction between release installation and user onboarding;
- retention of old runtimes for rollback.

No production behavior changes.

### Commit 2 - Characterize existing private user-state behavior

Add behavior-level tests proving that:

- each user resolves a different private data root;
- configuration and jobs remain isolated;
- launch-time working-directory behavior is unchanged;
- the application does not depend on a per-user venv path internally.

This protects the user-data side while the installer is refactored.

### Commit 3 - Add the shared launcher behind an inactive interface

Introduce the shared launcher without switching installation to it.

Test:

- argument forwarding;
- launch-time working-directory preservation;
- physical runtime-path resolution;
- shared source and orchestrator environment;
- actionable failure when `current` is absent or invalid.

### Commit 4 - Introduce shared-runtime path and manifest handling

Add the internal Shared Runtime module that:

- validates the bundle manifest;
- extracts the bundle digest;
- derives the release and completion-marker locations;
- rejects malformed digests or paths;
- detects a previously completed matching runtime.

Keep it unused by the production installer for this commit.

### Commit 5 - Add locked shared-runtime construction

Teach the module to acquire one installation lock and build directly into an
inactive digest-specific directory.

The venv must be created at its final physical location because venv scripts
embed absolute interpreter paths. It must not be built elsewhere and moved
afterward.

On failure:

- do not create the completion marker;
- do not update `current`;
- return a non-zero result;
- make a later retry rebuild the incomplete directory safely.

### Commit 6 - Install and validate dependencies offline

Install dependencies through the candidate environment's own `python -m pip`,
using only the verified wheel directory.

Require:

- `pip check`;
- imports of required top-level dependencies, including `sqlglot`;
- metadata recording the bundle digest, Python executable and version;
- no online index access.

Only then write the completion marker.

### Commit 7 - Add atomic activation and reuse

Activate a complete runtime by replacing `current` atomically.

Test:

- first activation;
- reuse of an identical completed digest;
- switching to a new digest;
- failed candidate installation preserving the previous `current`;
- reactivation of a previous digest for rollback;
- launcher resolution to the physical target.

Do not delete old runtimes automatically.

### Commit 8 - Enforce shared-runtime permissions

After successful construction, make the runtime readable and executable by
analysts but writable only by the Release Operator.

Verify:

- users cannot install or replace packages;
- users can traverse directories and import dependencies;
- the install lock and runtime root are not publicly writable;
- repository updates do not recursively rewrite runtime permissions.

### Commit 9 - Split release installation from user onboarding

Change the release installer so it only installs and activates the shared
runtime.

Move these responsibilities into User Onboarding:

- private data directories;
- email configuration;
- shell `PATH` setup;
- per-user thin launcher.

The release installer becomes non-interactive. User onboarding may prompt for
email.

### Commit 10 - Switch the launcher contract

Make the per-user launcher call the shared launcher rather than a personal
venv.

Running onboarding again must replace an old launcher that references
`/ads_storage/<user>/.dispatch/venv` with a launcher that delegates to the
shared runtime.

Existing personal venv directories remain untouched during migration.

### Commit 11 - Update the deployment profile and smoke contract

Change standard deployment smoke verification to invoke the shared launcher
explicitly, avoiding any stale Release Operator launcher on `PATH`.

The deployment must prove:

- the active runtime exists;
- its completion metadata matches the delivered bundle;
- `pip check` passed during installation;
- `dispatch --help` works through the shared launcher;
- `sqlglot` imports from the active runtime.

The existing edge-deploy bundle-delivery interface should be sufficient. A
core change is required only if testing reveals a missing generic verification
seam.

### Commit 12 - Update first-time setup and user documentation

Replace the current "every user runs the dependency installer" guidance with:

- the Release Operator installs the global runtime once per node;
- each user runs the lightweight onboarding command;
- troubleshooting distinguishes shared-runtime failures from private
  configuration failures;
- no user runs pip manually;
- no user needs a personal dependency bundle.

Document how existing users repair stale launchers without deleting their jobs
or configuration.

### Commit 13 - Add migration and rollback integration tests

Exercise the complete transition:

1. An existing user has an old personal venv and launcher.
2. The Release Operator installs the shared runtime.
3. User onboarding replaces only the launcher.
4. User configuration and jobs remain unchanged.
5. Two users resolve the same physical Python runtime.
6. Their data roots remain different.
7. A failed upgrade leaves the previous runtime active.
8. Rollback reactivates the previous completed runtime.

### Commit 14 - Remove obsolete per-user installation behavior

After all migration and integration tests pass, remove:

- per-user venv construction;
- per-user bundle lookup from onboarding;
- personal installed-version markers that describe runtime dependencies;
- tests that encode the old architecture.

Keep compatibility diagnostics that detect an old launcher and direct the user
to rerun onboarding.

## Testing decisions

Good tests exercise observable contracts rather than grep shell-script
implementation text.

Required automated coverage:

- Shared Runtime construction, validation, reuse and activation.
- Failure atomicity.
- Concurrent installer exclusion.
- Runtime permissions.
- Launcher argument and current-working-directory preservation.
- Two-user runtime sharing.
- Per-user data isolation.
- Existing-user migration.
- Rollback.
- Missing-runtime and corrupt-runtime errors.
- Offline dependency enforcement.
- Deployment smoke through the shared launcher.

Existing installer onboarding tests provide the correct integration-test seam
and should be reshaped around the new contracts.

## Controlled Edge Node rollout

1. Deploy to node03 with a fresh shared runtime.
2. Verify the Release Operator can run the shared launcher.
3. Run onboarding as a second analyst who has no bundle and no personal venv.
4. Confirm both users resolve the same physical interpreter.
5. Confirm their configuration and job directories remain separate.
6. Start a Dispatch process, activate another test runtime, and verify the
   existing process remains healthy.
7. Test rollback to the previous runtime.
8. Repeat on node04.
9. Retain old personal venvs and the previous global runtime during an
   observation period.
10. Handle cleanup as a separate, explicitly approved operation.

## Acceptance criteria

The change is complete when a new user with no personal bundle and no personal
venv can run onboarding and then successfully execute `dispatch --help`.

Additionally:

- `sqlglot` imports successfully;
- two users resolve the same global Python runtime;
- user state remains private;
- users cannot modify the global environment;
- a failed install cannot break the active runtime;
- rollback does not require downloading or rebuilding dependencies.

## Out of scope

- Sharing user configuration, jobs, logs, or telemetry.
- Installing into system Python.
- Online pip access.
- Writing to `/usr/local/bin` or requiring root access.
- Automatically deleting existing personal venvs.
- Automatically deleting old shared runtimes.
- Redesigning Dispatch's Job or orchestrator model.
- Changing Edge Node authentication or transport behavior.
