# Dispatch Production TUI Harness

This directory contains the **local tmux/psmux + SSH** harness for validating the real Dispatch Textual TUI on a Hadoop Edge Node.

Instead of SSHing into the Edge Node and spinning up tmux there, the harness creates a **local** tmux session whose pane is the SSH connection itself.  All pane control (key injection, screen capture, attach) happens locally.  One-off remote commands (file writes, `impala-shell` queries) still use a separate SSH connection.

## Prerequisites

**Local machine:**

- **Linux / macOS:** `tmux` available on `PATH`.
- **Windows:** [`psmux`](https://github.com/nicholasgasior/psmux) installed — provides a `tmux.exe` shim with the same CLI.  Install via `winget install psmux`, `scoop install psmux`, or `cargo install psmux`.
- `ssh` available on `PATH` and configured for key-based (or agent-forwarded) auth to the Edge Node.

**Edge Node:**

- `python3.10`, `klist`, and `impala-shell` are available.
- The Dispatch repo is deployed at `repo_path`.
- Kerberos has been initialized before Level 2 or Level 3 checks.

**Optional local dep for config parsing:** `python -m pip install -r tools/prod_tui/requirements.txt` (adds PyYAML).

## Configure

Edit `tools/prod_tui/config.yaml`:

```yaml
host: "your-user@edge-node"
repo_path: "/ads_storage/dispatch"
session_name: "robocop-prod-test"
terminal_width: 120
terminal_height: 40
ssh_options: "-o StrictHostKeyChecking=no"
smoke_query_sql: "SELECT 1 AS smoke_test_value"
scratch_schema: "dw_settle"
table_prefix: "dispatch_smoke"
max_smoke_job_wait_seconds: 120
operator_email: "you@example.com"
```

`ssh_options` accepts normal OpenSSH options such as `-J jump-host`, `-i ~/.ssh/key`, or `-o StrictHostKeyChecking=no`.

## How sessions work

```
┌─────────────────────────────────┐
│  local machine                  │
│  tmux session "robocop-prod-…"  │
│  ┌───────────────────────────┐  │
│  │  pane: ssh user@edge-node │  │
│  │   cd /ads_storage/dispatch│  │
│  │   $ _                     │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

`start` → opens the session above.
`send` / `keys` → `tmux send-keys -t <session>` locally.
`capture` → `tmux capture-pane -t <session>` locally.
`attach` → `tmux attach -t <session>` locally.
`stop` → `tmux kill-session -t <session>` locally.

## Manual tmux CLI

```bash
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml start
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml send "dispatch"
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml keys tab enter
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml capture
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml attach
python tools/prod_tui/robocop_tmux.py --config tools/prod_tui/config.yaml stop
```

`capture` prints the current tmux pane. `attach` hands your terminal to the local tmux session; detach with the normal tmux prefix sequence (`Ctrl-b d`).

## Level 1 and 2 Smoke Tests

Level 1 validates SSH/tmux, compileall, dashboard rendering, navigation, preview, and clean quit. Level 2 validates the real Edge Node environment without launching a job.

```bash
python tools/prod_tui/smoke_test.py --config tools/prod_tui/config.yaml --level 1 --save-screens
python tools/prod_tui/smoke_test.py --config tools/prod_tui/config.yaml --level 2 --save-screens
python tools/prod_tui/smoke_test.py --config tools/prod_tui/config.yaml --level all --save-screens
```

Each run prints a pass/fail summary and writes a JSON report under `tools/prod_tui/reports/`. Failed checks include the last captured screen. Use `--json-report path/to/report.json` to choose the report path and `--fail-fast` to stop after the first failure.

Exit codes are:

- `0`: all requested checks passed
- `1`: at least one check failed
- `2`: harness-level error such as config or SSH/tmux failure

## Level 3 Controlled Job

The controlled runner creates one tiny SQL file on the Edge Node, fills the Dispatch New Job form, verifies preview, and only launches when safety preconditions pass:

- Kerberos TTL is at least five minutes.
- Fewer than two jobs are currently Running.
- Schema is the configured scratch schema.
- Table name starts with `dispatch_smoke_`.
- SQL is exactly the configured smoke query or an equivalent `SELECT ... AS smoke_test_value`.

Dry run fills the form and previews without launching:

```bash
python tools/prod_tui/controlled_job.py --config tools/prod_tui/config.yaml --dry-run
```

Full run executes the smoke query, waits for completion, verifies the table exists through `impala-shell`, then attempts cleanup in all cases:

```bash
python tools/prod_tui/controlled_job.py --config tools/prod_tui/config.yaml
```

By default Level 3 first runs Level 1 and 2. Use `--skip-level12` only when an operator has just completed those checks manually and wants to repeat the controlled launch path.

## Agent Loop

`agent_loop.py` provides a safety-gated loop for automation:

1. Capture the tmux pane.
2. Parse the screen into `ScreenState`.
3. Ask a step to choose an `Action`.
4. Classify the action with `safety.classify()`.
5. Refuse `BLOCKED` actions.
6. Verify preconditions for `CONTROLLED` actions.
7. Send keys/text, capture again, and log the step.

Audit logs are written as JSONL under `tools/prod_tui/logs/`.

## Generated Artifacts

The following directories are intentionally ignored by git:

- `tools/prod_tui/screens/`
- `tools/prod_tui/reports/`
- `tools/prod_tui/logs/`

They contain screen captures, JSON reports, and agent audit logs for post-mortem review.
