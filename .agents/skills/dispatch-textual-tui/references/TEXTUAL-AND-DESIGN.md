# Textual and design rules

Dispatch pins Textual in `pyproject.toml`. Check that pin and the current code
before relying on remembered framework APIs.

## Ownership and data flow

- `dispatch/app.py` owns the shell, global bindings, command-palette entries,
  startup routing, launch CWD, and `CSS_PATH`.
- Screens own screen composition, bindings, orchestration, and screen-local
  widgets. Shared chrome currently lives in `dispatch/screens/sidebar.py`.
- Domain modules own manifest, launch-slot, SQL, Kerberos, process, and runner
  rules. Screens render those rules; they do not duplicate them.
- Prefer attributes down and typed Textual messages up. Keep child widgets from
  reaching into parent internals.
- Keep immutable constructor inputs in `__init__`, child creation in `compose`,
  and focus, watchers, intervals, and initial refresh in `on_mount`.
- Stop screen-owned workers, intervals, file handles, and tailers when the
  screen no longer owns their result.

## Async and worker safety

Move subprocess calls, filesystem walks, manifest batches, log reads, Impala
calls, and expensive parsing off the event loop. Existing code primarily uses
async workers and `asyncio.to_thread`.

- Prevent overlapping refreshes where stale results are harmful.
- Check that a screen/result is still current before painting worker output.
- Return snapshots from thread work; update widgets on Textual's UI thread.
- Handle success, cancellation, stale results, and failure explicitly.
- Use `await asyncio.sleep()` on async paths.
- Interactive `kinit` and editor flows may use the established
  `app.suspend()` plus `dispatch.process.run_interactive()` gateway.

## Styling

`dispatch/app.tcss` is the design system. Keep `CSS_PATH = "app.tcss"` and do
not introduce an inline stylesheet in `dispatch/app.py`.

- Reuse the docked `.action-bar` pattern.
- Reserve accent for focus, selection, primary actions, and semantic state.
- Pair every state color with a label, symbol, position, or emphasis so
  `NO_COLOR` and limited-color terminals remain understandable.
- Keep focus visible and controls keyboard reachable.
- Use borders to clarify grouping or focus, not as decoration.
- Prefer dense, stable tables and logs over card-heavy presentation.

The manifest states are `Pending`, `Running`, `Succeeded`, `Failed`, and
`Cancelled`. Use those names; there is no `Queued` job state.

## Interaction

- Preserve stable global bindings: `q`, `?`, and `F2`.
- Preserve screen-specific bindings unless the task explicitly redesigns them.
  `/` is a filter/search binding only where the screen currently implements it;
  it is not a universal list-screen contract.
- Keep primary actions in the footer or `.action-bar`; keep less common actions
  discoverable through help or the command palette.
- Keep `Tab` / `Shift+Tab` focus order predictable.
- Preserve durable row keys such as job IDs and selection across refresh.
- Restrict actions to visible rows so filtering cannot leave a hidden job as
  the cancel/view target.
- Name the exact resource in destructive confirmations. Browser DROP requires
  its existing typed-name confirmation.

## Responsive behavior

The app warns below 80x24; it does not replace the UI with a blocking resize
screen. At supported sizes:

- the sidebar auto-collapses below width 100
- the Overview detail pane hides below height 30
- primary status, table, and actions remain available at 80x24
- 120x40 is the normal interaction-test size
- wider terminals may expose more detail without moving a panel's purpose

Use flexible constraints and collapse secondary detail before primary
interaction. Resizing must preserve selection, focus, and valid action targets.

## Tables, logs, and errors

- Keep columns stable and patch changed cells instead of rebuilding unchanged
  tables.
- Align text for scanning; truncate long values and expose full values in
  detail/preview.
- Tail bounded log windows and state truncation honestly.
- Keep log follow/pause and search state explicit.
- Surface worker/process errors in concise status plus inspectable detail.
- Never hide Kerberos, queue/pool, SQL, disk, network, or authorization reasons
  behind a generic failure when the classifier has a specific result.
