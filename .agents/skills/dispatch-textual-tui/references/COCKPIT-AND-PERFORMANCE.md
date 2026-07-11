# Supervision cockpit and performance

Read this reference for Overview, History, Job Detail, refresh loops, log
tailing, large job sets, responsive behavior, or SSH performance.

## Current cockpit

`dispatch/screens/dashboard.py` implements the dominant
launch → watch → diagnose loop as:

1. a compact status strip
2. one jobs table with Running jobs first
3. a live detail pane for the selected job's bounded log tail
4. a docked action bar

Full Job Detail remains a drill-down. Do not reintroduce the removed stat-card
dashboard or split active/recent tables without an explicit product redesign.

The app extends Textual's command palette in `DispatchApp.get_system_commands`.
Keep top-level destinations and Kerberos refresh reachable there when changing
navigation.

## Current limits and breakpoints

Treat these source constants as contracts to inspect, not values to duplicate
in new modules:

| Behavior | Current source |
|---|---|
| Overview row limit: 100 | `dispatch/screens/dashboard.py::JOBS_ROW_LIMIT` |
| Overview detail tail: 4096 bytes / 8 lines | `DETAIL_TAIL_BYTES`, `DETAIL_TAIL_LINES` |
| Overview detail hides below height 30 | `DETAIL_MIN_HEIGHT` |
| Overview refresh: 2 seconds | `DashboardScreen.on_mount` |
| Job Detail display: 200 lines | `dispatch/screens/job_detail.py::LOG_VIEW_LINES` |
| Job Detail read chunk: 65536 bytes | `LOG_READ_CHUNK_BYTES` |
| Job Detail refresh: 1 second | `JobDetailScreen.on_mount` |
| Active supervision window: 7 days | `dispatch/jobs.py::ACTIVE_WINDOW` |
| History page size: 17 | `dispatch/screens/history.py::PAGE_SIZE` |
| Sidebar collapse below width 100 | `dispatch/screens/sidebar.py` |

If changing one, update focused tests that prove the new bound and explain the
SSH/readability trade-off.

## Refresh discipline

Preserve the existing bounded pipeline:

- `dispatch/jobs.py` caches parsed manifests by mtime and prunes deleted paths.
- Overview keeps an `_active_cache`; filter keystrokes and cursor movement must
  not trigger filesystem walks.
- `_row_signature` detects structural changes; elapsed values can update
  cell-by-cell.
- `_static_cache` avoids repainting identical markup over SSH.
- `_tail_cache` avoids rereading unchanged detail logs.
- `_refresh_in_flight` prevents overlapping refresh ticks.
- Overview returns before listing jobs or reading logs while another screen is
  active. Job Detail currently keeps its one-second interval while mounted.
- Visible job IDs constrain View Logs and Cancel after filtering.

Prefer a small invalidation rule over unconditional rebuilding. Test cache
behavior by counting the expensive call or read, not by asserting private cache
contents alone.

## SSH-tight rendering

`dispatch/app.py` disables Textual animations unless `TEXTUAL_ANIMATIONS` is
explicitly set. Headers use `show_clock=False` where repeated clock paints add
noise. Preserve these defaults unless measured evidence supports a change.

For a changed refresh path, inspect:

- number and size of filesystem reads per tick
- table rows/cells repainted
- whether hidden screens still poll
- whether rapid filter input invokes I/O
- whether log rotation/truncation duplicates or loses lines
- whether selection survives structural and state-only updates

## Focused regression routes

- Cockpit structure, ordering, caches, detail tail, filter, palette:
  `tests/test_cockpit.py`
- Bounded logs, filtered selection, sidebar resize:
  `tests/test_qa_fixes.py`
- Minimum-size warning and 80x24 rendering:
  `tests/test_ui_ux_audit_implementation.py`
- Navigation, actions, history, browser:
  `tests/test_ui_ux_closure.py`
- Rendered-state snapshots:
  `tests/test_ui_snapshots.py`

Use `run_test(size=(80, 24))`, `(120, 40)`, and a wider size when layout is
affected. A below-minimum case should assert the warning; 80x24 should assert
that the primary workflow remains usable.
