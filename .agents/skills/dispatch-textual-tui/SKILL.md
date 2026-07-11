---
name: dispatch-textual-tui
description: Use when building, reviewing, debugging, or testing Dispatch's Textual UI, including dispatch/app.py, dispatch/screens/, app.tcss, mocks, and TUI interaction tests.
---

# Dispatch Textual TUI skill

Dispatch is a server-side supervision cockpit for Impala jobs. The detached
runner owns durable execution; the TUI launches, observes, and diagnoses jobs
over SSH. Repository facts override generic Textual advice.

## Workflow

### 1. Route the task

Read `README.md`, `AGENTS.md`, the affected screen, and the matching row in
[`references/MODULE-MAP.md`](references/MODULE-MAP.md). Read the additional
reference only when its context pointer applies:

- UI structure, bindings, styling, lifecycle, workers, or accessibility:
  [`references/TEXTUAL-AND-DESIGN.md`](references/TEXTUAL-AND-DESIGN.md)
- Overview, refresh loops, logs, large job histories, resize, or SSH latency:
  [`references/COCKPIT-AND-PERFORMANCE.md`](references/COCKPIT-AND-PERFORMANCE.md)
- Local mocks, Pilot tests, screenshots, CI, or Edge Node evidence:
  [`references/VALIDATION.md`](references/VALIDATION.md)

**Complete when:** every changed behavior is mapped to its owning production
module, test file, and product invariant.

### 2. Preserve the product contract

- The TUI is never the durable job owner.
- Capture launch CWD once; write plain, uncompressed CSV output there.
- Persist job state in manifests under the configured data root.
- Decompose `Table+Csv` into table creation and a separate CSV export.
- Enforce the legal source/destination matrix in `dispatch/manifest.py`.
- Two launch slots exist. Both `Pending` and `Running` consume a slot.
- Refuse launch when Kerberos is missing or has less than 300 seconds remaining.
- Keep `scr/` standard-library-only and follow ADR-0005 for any explicit
  orchestrator change.

**Complete when:** the change preserves each applicable invariant in code and
tests; any intentional contract change is called out explicitly.

### 3. Implement on the SSH-tight path

- Keep app shell/routing in `dispatch/app.py`, screen behavior in
  `dispatch/screens/`, domain behavior in the owning `dispatch/*.py` module,
  and styles in `dispatch/app.tcss`.
- Use current screen-local/shared widgets, such as
  `dispatch/screens/sidebar.py`; there is no `dispatch/widgets/` package.
- Move blocking subprocess, filesystem, log, and Impala work off the Textual
  event loop. Return snapshots to the UI thread rather than mutating widgets
  from worker threads.
- Preserve keyboard access, visible focus, semantic labels independent of
  color, bounded displays, and actionable worker errors.
- Extend an existing abstraction only after finding a second concrete use.

**Complete when:** the UI remains responsive, ownership boundaries are clear,
and failure/cancellation paths are visible.

### 4. Validate the behavior

Follow [`references/VALIDATION.md`](references/VALIDATION.md). Use the existing
`mock_env` / `mock_env_with_config` fixtures and Textual `run_test()` Pilot
tests. For perceptible UI changes, exercise the real app with mocks from a
launch directory containing a `.sql` file and capture the relevant terminal
sizes.

**Complete when:** the targeted regression is green, CI-equivalent checks pass,
and manual evidence covers the changed UI or a documented environment blocker
explains why it cannot.

### 5. Review and report

Reject a TUI change that:

- blocks the event loop or leaks refresh workers
- changes job durability, launch-slot, Kerberos, CSV, or `scr/` semantics
  accidentally
- rebuilds tables or rereads full logs on frequent refreshes
- loses selection or targets a filtered-out job
- hides critical actions/status at 80x24
- relies on color, mouse input, or undiscoverable bindings
- adds visual polish without a mock-backed UI check

Report files and behavior changed, exact checks and mock scenarios run,
terminal sizes exercised, and remaining real Edge Node gaps.

**Complete when:** the report lets a reviewer reproduce the evidence without
guessing.
