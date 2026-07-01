# Dispatch Production TUI Harness

This directory contains the **local tmux/psmux + SSH** harness for validating and diagnosing the real Dispatch Textual TUI on a Hadoop Edge Node.

The default release workflow is not this harness directly. For normal
production releases, run the shared orchestrator:

```powershell
python -m edge_deploy release
```

Use this harness when the release report calls for deeper node diagnosis or
when a controlled manual recovery needs extra smoke/drift evidence.

Instead of SSHing into the Edge Node and spinning up tmux there, the harness creates a **local** tmux session whose pane is the SSH connection itself. All pane control (key injection, screen capture, attach) happens locally. One-off remote commands (file writes, `impala-shell` queries) run through the already-authenticated tmux pane so the harness does not burn a second RSA prompt.

## Prerequisites

**Local machine:**

- **Linux / macOS:** `tmux` available on `PATH`.
- **Windows:** [`psmux`](https://github.com/nicholasgasior/psmux) installed — provides a `tmux.exe` shim with the same CLI.  Install via `winget install psmux`, `scoop install psmux`, or `cargo install psmux`.
- `ssh` available on `PATH` and configured for key-based (or agent-forwarded) auth to the Edge Node.

**Edge Node:**

- `python3.11` or `python3.10`, `klist`, and `impala-shell` are available
  (the harness accepts python3.11 or python3.10).
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
ssh_options: "-p 2222 -o StrictHostKeyChecking=no"
smoke_query_sql: "SELECT 1 AS smoke_test_value"
scratch_schema: "aa_enc"
table_prefix: "dispatch_smoke"
max_smoke_job_wait_seconds: 120
operator_email: "you@example.com"
```

`ssh_options` accepts normal OpenSSH options such as `-J jump-host`, `-i ~/.ssh/key`, or `-o StrictHostKeyChecking=no`.

## Network Preflight

Before requesting an RSA code or starting the harness, verify TCP 2222 reaches
the target Edge Node selected by the harness config:

```powershell
python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json
python -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node04.json
```

For a direct PowerShell check against both known Edge nodes:

```powershell
Test-NetConnection hde2stl020003.mastercard.int -Port 2222 -InformationLevel Detailed
Test-NetConnection hde2stl020004.mastercard.int -Port 2222 -InformationLevel Detailed
```

The harness command should print `TCP preflight: PASS`, or the direct
PowerShell command should report `TcpTestSucceeded : True`. If TCP 2222 times
out, the harness cannot reach the RSA prompt; reconnect to the required
VPN/network path before running Edge validation.

Do not run `tmux start`, `smoke`, `job`, or `level` until the selected node's
preflight JSON report shows `connected: true`. When it shows
`connected: false`, keep that report as the current network-blocker evidence.

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
python -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml
python -m tools.prod_tui tmux send --config tools/prod_tui/config.yaml "dispatch"
python -m tools.prod_tui tmux keys --config tools/prod_tui/config.yaml tab enter
python -m tools.prod_tui tmux capture --config tools/prod_tui/config.yaml
python -m tools.prod_tui tmux attach --config tools/prod_tui/config.yaml
python -m tools.prod_tui tmux stop --config tools/prod_tui/config.yaml
```

`capture` prints the current tmux pane. `attach` hands your terminal to the local tmux session; detach with the normal tmux prefix sequence (`Ctrl-b d`).

## Level 1 and 2 Smoke Tests

Level 1 validates SSH/tmux, compileall, dashboard rendering, navigation, preview, and clean quit. Level 2 validates the real Edge Node environment without launching a job.

```bash
python -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level 1 --save-screens
python -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level 2 --save-screens
python -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens
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
- Schema is one of the approved schemas (`aa_enc` or `coe_enc`).
- Table name starts with `dispatch_smoke_`.
- SQL is exactly the configured smoke query or an equivalent `SELECT ... AS smoke_test_value`.

Dry run fills the form and previews without launching:

```bash
python -m tools.prod_tui job --config tools/prod_tui/config.yaml --dry-run
```

Full run executes the smoke query, waits for completion, verifies the table exists through `impala-shell`, then attempts cleanup in all cases:

```bash
python -m tools.prod_tui job --config tools/prod_tui/config.yaml
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

## Recovery deployment / keeping nodes in sync (`_seam_deploy.py`)

For the complete contributor workflow, including GitHub + Bitbucket remote
policy and when to use each deploy path, see
[`docs/release-workflow.md`](../../docs/release-workflow.md).

Normal releases are handled by `edge_deploy release`. Use the public
deploy/drift commands below only when the orchestrator is unavailable or a
release report calls for node-specific recovery against an already-authenticated
session:

```powershell
py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto --json-report tools/prod_tui/reports/deploy-node03.json --reuse-session
py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha> --json-report tools/prod_tui/reports/drift-node03.json --reuse-session
py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <previous-good-sha> --rollback-from <current-bad-sha> --json-report tools/prod_tui/reports/rollback-node03.json --reuse-session
```

Use `tools/prod_tui/config-node04.yaml` for the same node-04 command shapes.
Under the hood the deploy command drives `DISPATCH_UPDATE_REMOTE=bitbucket
DISPATCH_UPDATE_BRANCH=main ./update.sh <commit-sha>` on the node and records
whether `install.sh` ran or was skipped.

The edge nodes are **independent filesystems** (e.g. `hde2stl020003` and
`hde2stl020004` do not share `/ads_storage/dispatch`), so each must be deployed
and verified separately, over its own authenticated session. One config file
per node selects the target:

- `config.yaml` → node 03 (`robocop-prod-test`, the default target)
- `config-node04.yaml` → node 04 (`robocop-prod-test-04`)

Start that node's session first (each needs its own SSH passcode), then act on
it with `--config`:

```bash
# bring up an authenticated pane for the node you want to touch
python -m tools.prod_tui tmux start --config tools/prod_tui/config-node04.yaml --passcode <RSA_CODE>

# compare every deployed *.py on that node against the local repo
python -m tools.prod_tui._seam_deploy --config tools/prod_tui/config-node04.yaml verify

# push only drifted dispatch/ files (scr/ is reported but NOT auto-deployed)
python -m tools.prod_tui._seam_deploy --config tools/prod_tui/config-node04.yaml sync

# push every drifted file INCLUDING scr/ (use to bring a fresh node to parity)
python -m tools.prod_tui._seam_deploy --config tools/prod_tui/config-node04.yaml deploy-all

# push a single explicit file
python -m tools.prod_tui._seam_deploy --config tools/prod_tui/config-node04.yaml deploy-path dispatch/sql.py /ads_storage/dispatch/dispatch/sql.py
```

`--config` defaults to node 03, so omitting it acts on node 03. Each transfer
backs up the remote file to `*.seam_bak`, base64-streams the new content, and
syntax-validates it with the node's own venv Python. `verify` reporting
`MATCH=N DRIFT=0 IN_SYNC` against the same local tree on two nodes guarantees
those nodes are byte-identical to each other.

`sync` deliberately refuses to auto-deploy `scr/` (the production-sensitive
orchestrators, ADR-0005); `deploy-all` includes them on purpose for parity and
prints a `[scr/]` tag per file. Deploying `scr/` to a node does not waive the
ADR-0005 human review for merging that change.

### Which deploy path to use

- Use `py -m tools.prod_tui deploy` plus `py -m tools.prod_tui drift` for
  recovery or diagnostic work against committed deployment snapshots.
- Use `_seam_deploy sync` for fast local-to-node iteration after the node's
  tmux/SSH/Kerberos session is already healthy.
- Use `_seam_deploy deploy-all` only for an intentional parity operation that
  may include `scr/`.
- Use the zip deploy flow for first-time setup, vendor refreshes, offline
  installs, or recovery.

## Generated Artifacts

The following directories are intentionally ignored by git:

- `tools/prod_tui/screens/`
- `tools/prod_tui/reports/`
- `tools/prod_tui/logs/`

They contain screen captures, JSON reports, and agent audit logs for post-mortem review.
