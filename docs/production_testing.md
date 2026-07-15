# Production Testing Process

This is the canonical process for validating the real Dispatch Textual TUI on a
Hadoop Edge Node.

For normal production releases, run the shared release orchestrator instead of
driving this harness directly:

```powershell
python -m edge_deploy release
```

Use this document for deeper validation, recovery, or diagnosis after reviewing
the release report.

```text
local machine
  └─ tmux session
       └─ pane: ssh -p 2222 <user>@<edge-node>   ← RSA PASSCODE (2FA)
            └─ remote shell
                 ├─ kinit                          ← Kerberos password
                 └─ dispatch / impala-shell / tests
```

The agent does **not** drive Dispatch with plain `subprocess`, because Dispatch
is a real Textual TUI, not a stdin/stdout CLI. tmux gives persistence, screen
capture, and the ability for a human to attach to the same session.

> **Session model.** tmux runs **locally**; the SSH connection lives *inside*
> the tmux pane. All `send-keys` / `capture-pane` / `attach` calls operate on
> the local session — there is no second SSH hop per command. One-off
> non-interactive remote commands (file writes, `impala-shell`, `klist`) run
> through the already-authenticated tmux pane so a single-use RSA prompt is not
> consumed twice.

## Network Preflight

Before requesting an RSA code or starting the harness, verify the local machine
can reach the configured Edge Node SSH port:

```powershell
python -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json
python -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node04.json
```

For a direct PowerShell check:

```powershell
Test-NetConnection hde2stl020003.mastercard.int -Port 2222 -InformationLevel Detailed
Test-NetConnection hde2stl020004.mastercard.int -Port 2222 -InformationLevel Detailed
```

The harness command should print `TCP preflight: PASS`, or the direct
PowerShell command should report `TcpTestSucceeded : True`. If TCP 2222 times
out, the harness cannot reach the RSA prompt; reconnect to the required
VPN/network path before running Edge validation.

## Authentication

Two interactive secrets are required and must be entered by a human; never
hard-code or echo them:

1. **RSA SecurID PASSCODE** — prompted by SSH (`Enter PASSCODE:`) right after the
   login banner.
2. **Kerberos password** — prompted by `kinit` (`Password for
   <user>@CORP.MASTERCARD.ORG:`).

Confirm the ticket with `klist` before running Level 2 or Level 3 checks.

## Manual session (what the harness automates)

```bash
tmux new-session -d -s robocop-prod-test -x 120 -y 40
tmux send-keys  -t robocop-prod-test "ssh -p 2222 <user>@<edge-node>" Enter
# enter the RSA PASSCODE at the prompt (attach if typing it yourself):
tmux attach -t robocop-prod-test     # Ctrl-b d to detach without killing

# on the remote shell:
tmux send-keys -t robocop-prod-test "kinit" Enter   # enter Kerberos password
tmux send-keys -t robocop-prod-test "klist" Enter
tmux capture-pane -t robocop-prod-test -p
```

To launch the real TUI from a directory of SQL files:

```bash
tmux send-keys -t robocop-prod-test "cd /path/to/sql/files && dispatch" Enter
tmux capture-pane -t robocop-prod-test -p
```

## Harness (preferred)

`tools/prod_tui/` codifies the model above. See
[tools/prod_tui/README.md](../tools/prod_tui/README.md) for full usage. The host,
port, and SSH options live in `tools/prod_tui/config.yaml`.

```bash
# gate before requesting RSA/Kerberos time
py -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json

# start the local tmux session + SSH (sends the PASSCODE for you if provided)
py -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml --passcode <RSA_PASSCODE>

py -m tools.prod_tui tmux send --config tools/prod_tui/config.yaml "dispatch"
py -m tools.prod_tui tmux keys --config tools/prod_tui/config.yaml tab enter
py -m tools.prod_tui tmux capture --config tools/prod_tui/config.yaml
py -m tools.prod_tui tmux attach --config tools/prod_tui/config.yaml
py -m tools.prod_tui tmux stop --config tools/prod_tui/config.yaml

# scripted test levels
py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens
py -m tools.prod_tui job --config tools/prod_tui/config.yaml --dry-run
```

Do not run `tmux start`, `smoke`, `job`, or `level` until the selected node's
preflight report shows `connected: true`. A failed preflight is the validation artifact
for `DOC-010`, not a reason to consume an RSA code.

For node 04, use `tools/prod_tui/config-node04.yaml` consistently for the
preflight, tmux, smoke, job, level, and deploy commands.

The agent loop is: capture screen → reason about the visible UI → send a
key/action → capture again → assert the expected state.

## Recovery or Diagnostic Deployment Before Testing

Use [release-workflow.md](release-workflow.md) as the canonical
workflow. The paths below are recovery and diagnostic options when the shared
release command is unavailable or a release report points to node-specific
follow-up:

- **Bitbucket reset via `update.sh`:** recovery path for committed, reviewable
  snapshots. Use the public harness commands so the node update, install
  decision, drift evidence, and JSON report share one command shape:

  ```powershell
  py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto --json-report tools/prod_tui/reports/deploy-node03.json
  py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha> --json-report tools/prod_tui/reports/drift-node03.json
  ```

  Exact-SHA rollback uses the same surface:

  ```powershell
  py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <previous-good-sha> --rollback-from <current-bad-sha> --json-report tools/prod_tui/reports/rollback-node03.json
  ```
- **`_seam_deploy sync`:** fast iteration for authenticated sessions. It syncs
  drifted `dispatch/` Python files and reports `scr/` drift without deploying
  it.
- **`_seam_deploy deploy-all`:** explicit node parity operation that may include
  `scr/`; ADR-0005 still governs whether that change is safe to merge.
- **Zip deploy:** first-time setup, vendor refresh, offline install, or recovery
  when the server working tree is not usable.

Node 03 and node 04 use independent filesystems. Update and validate both nodes
separately when the goal is production parity.

## Test levels

The detailed, checkable steps live in
[docs/edge-node-smoke-test.md](./edge-node-smoke-test.md). In short:

- **Level 1 — safe production smoke (no job launch):** SSH + tmux work,
  `compileall` is clean, the dashboard renders, Kerberos status shows, navigation
  works, SQL browser / history / preview open, quit is clean.
- **Level 2 — real environment checks (no destructive actions):** `install.sh`
  works against the real `/ads_storage/<user>/` path, `klist` is detected,
  `impala-shell` is on PATH, the launch CWD is captured, Textual renders over the
  corporate SSH chain.
- **Level 3 — controlled real job:** only a trivial scratch query
  (`SELECT 1 AS smoke_test_value`) into a writable scratch schema, with a
  destination table named `dispatch_smoke_<user>_<date>`.
- **Level 3a - manual CSV smoke:** the same trivial scratch query exported as
  an uncompressed CSV in the launch-time working directory. This is the manual
  checklist counterpart to the automated Level 4 CSV cells.
- **Level 4 - job-type breadth:** executable harness coverage for every legal
  Source x Destination cell, including `SqlFile -> Csv`, `SqlFile -> Table+Csv`,
  and `ExistingTable -> Csv`. This is the acceptance path for CSV output and
  Table+Csv decomposition changes.

## Safety classification

```text
SAFE:       navigate, preview, capture, inspect logs/history, --help, compileall
CONTROLLED: launch the smoke query with a dispatch_smoke_ prefixed table only
BLOCKED:    drop non-smoke tables, run arbitrary SQL, modify scr/, delete
            non-smoke files, launch unknown user SQL
```

A `CONTROLLED` launch is allowed only when:

- the target schema is explicitly scratch/writable,
- the SQL file is known and tiny,
- the destination table/output name starts with `dispatch_smoke_`,
- the Kerberos TTL is healthy (≥ 5 minutes), and
- no more than the allowed running-job cap (2) is active.

These mirror the app's own invariants (refuse missing/low Kerberos tickets and
more than two simultaneously Running jobs).

Cleanup is also controlled only for resources created by this smoke run: a
`dispatch_smoke_` table may be dropped through Browser after typed
confirmation, and the matching temporary smoke SQL/CSV files may be removed.
Dropping any other table remains blocked.

`pytest` / Textual `Pilot` remain the tool for deterministic, non-prod
regression tests; SSH + tmux + a real Edge Node is the acceptance harness.
