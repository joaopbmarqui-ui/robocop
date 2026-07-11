# Dispatch TUI validation

Match validation to the changed path. Automated Pilot tests are the default;
perceptible UI changes also require a real mocked TUI walkthrough.

## Cursor Cloud manual setup

Use bash and the project virtualenv. Start from the repository root:

```bash
repo=$PWD
source "$repo/mocks/dev-env.sh"
DISPATCH_EMAIL=test@example.com \
  DISPATCH_PYTHON_BIN="$repo/.venv/bin/python" \
  "$repo/install.sh"
launch_dir=$(mktemp -d)
printf 'SELECT 1 AS smoke_check;\n' > "$launch_dir/smoke.sql"
cd "$launch_dir"
DISPATCH_MOCK_SCENARIO=happy_path "$repo/.venv/bin/python" -m dispatch
```

`install.sh` supplies the local config and `installed_version`; rerun it when
the app reports either missing. The launch directory must contain at least one
`.sql` file or the New Job picker is empty. `mocks/dev-env.sh` supplies fake
`kinit`, `klist`, and `impala-shell`, starts mock SMTP, and redirects the data
root away from `/ads_storage/`.

Useful seams:

- `DISPATCH_MOCK_SCENARIO`: select a JSON file name from `mocks/scenarios/`
  without `.json`
- `DISPATCH_MOCK_DELAY=0`: remove scenario delays in automated tests
- `DISPATCH_MOCK_KLIST_TTL`: set mock Kerberos ticket lifetime
- `DISPATCH_TEST_PREFILL`: open New Job from a JSON prefill file; use only for
  deterministic smoke harnesses, not to bypass normal interaction tests
- `TEXTUAL_ANIMATIONS=1`: opt into animations; the SSH-safe default is off

Leave development services running for follow-up testing. Do not commit
captured emails, reports, screenshots, temporary SQL, or data-root contents.

## Automated TUI tests

Reuse fixtures from `tests/conftest.py`:

- `mock_env` isolates `PATH`, data root, mock state, scripts, delay, and SMTP
- `mock_env_with_config` also writes a minimal `config.json`

Write Textual tests with `DispatchApp.run_test()` and Pilot. After key presses,
clicks, pushes, or resize events, `await pilot.pause(...)` before asserting.
Assert widget state/content and behavior, not terminal escape sequences.

Focused routes:

| Change | Start with |
|---|---|
| Launch-slot cap and job reconciliation | `tests/test_pure_logic.py`, `tests/test_jobs_reconcile.py`, `tests/test_qa_fixes.py` |
| Overview/cockpit/filter/palette/performance | `tests/test_cockpit.py` |
| New Job, legal matrix, preview, validation | `tests/test_cockpit.py`, `tests/test_production_polish.py`, `tests/test_prefill_seam.py` |
| Logs, selection, sidebar, regression behavior | `tests/test_qa_fixes.py` |
| 80x24 and below-minimum behavior | `tests/test_ui_ux_audit_implementation.py` |
| Cross-screen navigation and destructive confirmation | `tests/test_ui_ux_closure.py` |
| Rendered snapshots | `tests/test_ui_snapshots.py` |
| Runner/process integration and scenarios | `tests/test_runner_integration.py`, `tests/test_mock_contract.py` |

Run the smallest focused test first, then the full suite:

```bash
.venv/bin/python -m pytest path/to/focused_test.py -q
.venv/bin/python -m pytest -n 4 --dist loadfile
```

Consult `AGENTS.md` before interpreting a known repository-level failure.

## Mock scenario matrix

Exercise `happy_path` plus every failure family touched by the change. The
current scenario files are:

- capacity/retry: `all_queues_full`, `backpressure`, `memory_exceeded`, `slow`
- query/metadata: `syntax_error`, `duplicate_column`, `table_not_found`
- authentication: `auth_error`
- network: `connection_error`, `host_resolution_error`, `host_unreachable`,
  `timeout`
- storage: `disk_full`, `space_limit`
- fallback: `generic_error`

`tests/test_mock_contract.py` is the contract for the complete directory. Any
new scenario needs contract and runner coverage.

## CI-equivalent checks

Use `.venv` in Cursor Cloud:

```bash
.venv/bin/python -m compileall dispatch scr
.venv/bin/ruff check dispatch tests
.venv/bin/ruff check scr
.venv/bin/ruff format --check dispatch tests
.venv/bin/mypy dispatch/sql.py dispatch/jobs.py dispatch/manifest.py
.venv/bin/python -m dispatch --help
.venv/bin/python -m pytest -n 4 --dist loadfile
```

## Visual and terminal evidence

For layout, styling, keyboard, focus, filtering, or resize changes:

1. Run the mocked app at 80x24, 120x40, and a wider terminal as applicable.
2. Verify keyboard-only access and visible focus.
3. Verify status meaning without depending on red/green alone.
4. Exercise resize in both directions and preserve selection/action targets.
5. Exercise the relevant mock success and failure scenarios.

`tools/dev/ui_captures.py` drives self-checking SVG captures for global help,
command palette, sidebar collapse, minimum size, and preview. Do not treat a
snapshot alone as proof of interaction behavior.

## Production evidence boundary

Local mocks cannot prove the corporate SSH chain, real `/ads_storage`, Kerberos
client output, Impala behavior, or production terminal latency. When a Release
Operator explicitly requires Edge evidence, follow `tools/prod_tui/README.md`
and `docs/release-workflow.md`.

The production harness has levelled SSH/tmux smoke tests and a deterministic
`DISPATCH_TEST_PREFILL` path. It is diagnostic/release tooling, not the default
local loop. Do not deploy, run controlled jobs, or mutate production without
explicit Release Operator instruction.
