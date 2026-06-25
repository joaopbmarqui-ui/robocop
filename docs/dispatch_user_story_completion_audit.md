# Dispatch User Story Completion Audit

Date: 2026-06-22

## Objective

Act as the agent orchestrator for Dispatch and:

1. Inventory every application feature.
2. Create a user story and expected behavior for each feature based on the code.
3. Keep one canonical spreadsheet tracking feature status.
4. Test every user story and document all errors found.
5. Fix every logistical or UX error found.
6. Retest every user behavior after fixes.

## Canonical Tracker

The single canonical tracker is:

- `docs/dispatch_user_story_tracker.csv`

Current tracker audit:

- Rows: 64
- Feature status values: all 64 rows are `Implemented`
- Remaining real-environment retest gates: 1 row

Current verdict:

- Not complete. The local inventory, fixes, and retests are complete; a first
  authenticated node03 Edge session on 2026-06-24 closed 11 harness gates
  (preflight, smoke, the controlled job, and Levels 4-6); a 2026-06-24 local
  Textual SVG-capture pass closed 4 pure-UI gates (APP-002, APP-003, SIDE-002,
  PREV-002); JOB-018 was accepted as mock-covered; and a second human-driven
  node03 session on 2026-06-24 closed 10 more gates (Impala browse/describe/drop,
  live-log follow/pause/search/copy, process-group cancellation, ticket-refusal
  plus the in-app credential refresh, and the scratch-only cleanup doc
  execution). The active objective has
  1 real-environment user-story gate pending.
  TCP 2222 is reachable; the one remaining gate, BR-001, is blocked by
  a metadata-list header defect found during the live session — its fix is
  landed and locally tested but awaits redeployment and a list/count/auto-describe
  retest.

Pending retest rows by area:

| Area | Count |
|---|---:|
| Browser | 1 |

The tracker columns are:

- `feature_id`
- `area`
- `user_story`
- `expected_behavior`
- `code_evidence`
- `test_evidence`
- `manual_test`
- `status`
- `local_test_status`
- `errors_found`
- `fix_status`
- `retest_status`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Current result |
|---|---|---|
| Use subagents to inventory features | Explorer agents inspected UI shell/screens, New Job/browser validation, runner/manifest/install/mocks, test coverage, and pending local-testable gaps. | Complete for local code inventory. |
| Every feature has a user story and expected behavior | `docs/dispatch_user_story_tracker.csv` has 64 rows with `feature_id`, `area`, `user_story`, and `expected_behavior`. | Complete. |
| Single canonical spreadsheet tracks feature status | `docs/dispatch_user_story_tracker.csv` is the only canonical tracker. | Complete. |
| Test every user story | Local automated coverage was expanded and rerun; tracker records local and manual evidence per row; two 2026-06-24 node03 sessions added real Edge evidence for 21 rows. | Locally complete; 1 Edge-only user story (BR-001) awaits a post-redeploy retest; JOB-018 accepted as mock-covered. |
| Document all errors | `errors_found`, `fix_status`, and `retest_status` columns document discovered issues and remaining gaps. | Complete for discovered local/logistical/UX issues. |
| Fix logistical or UX errors | Fixed sidebar shortcut/action scope, docs policy conflicts, Python version smoke command, stale audit wording, and CSV launch-CWD smoke guidance. | Complete for locally reproducible logistical/UX errors found. |
| Retest post-fix behavior | Focused tests plus full local test workflow passed. | Locally complete. |
| Complete real Edge validation | 2026-06-24 node03 session: preflight `connected: true`, smoke 21/22 (psmux geometry host limit), controlled job and Levels 4-6 all passed; reports under `tools/prod_tui/reports/*-node03-edge.json`. | Partially complete: 26 gates closed (21 via two node03 Edge sessions, 4 via local Textual UI captures under `tools/prod_tui/reports/ui-captures/`, JOB-018 accepted as mock-covered), 1 human-at-terminal gate (BR-001) remains pending a post-redeploy retest. |

## Code-Surface Coverage Spot Check

A current code-surface scan checked Textual screens, bindings, and action methods
under `dispatch/` against the tracker. The scan covered these user-facing
surfaces:

- App shell/global bindings and startup diagnostics: `APP-*`.
- Sidebar and Kerberos chip: `SIDE-*`, `DASH-002`.
- Dashboard cockpit actions, empty state, and event trail: `DASH-*`, `JOB-003`.
- History paging/sort/search/detail navigation: `HIST-*`.
- Help modal: `HELP-001`.
- New Job source/destination matrix, preview, launch, edit SQL, and kinit:
  `NJ-*`, `JOB-014`, `JOB-015`.
- SQL preview accept/copy behavior: `PREV-*`.
- Browser show/describe/drop behavior: `BR-*`, `JOB-016`.
- Confirmation modal: `NJ-011`, `BR-003`, `JOB-003`.
- Job detail log, clone, copy, and cancel behavior: `JOB-001` through
  `JOB-004`, `JOB-013`.
- Manifest, process, runner, SQL, Kerberos, Impala, install, mocks, and
  production harness surfaces: `JOB-005` through `JOB-021`, `DOC-*`.

No additional local user-facing screen/action family was found outside the
canonical tracker during this spot check.

## Local Validation Evidence

Commands run successfully on 2026-06-22:

```powershell
.\tools\dev\local_check.ps1
```

Result:

```text
296 passed, 1 skipped in 84.08s
Local check passed.
```

The local check now uses repo-local `TEMP` / `TMP` and `--basetemp` for pytest
because a prior full-suite attempt exhausted C: temporary space and produced
`No space left on device` setup errors. The script restored the original temp
environment and removed its `.local-check-tmp` / `.local-check-pytest`
directories after the successful run.

Latest local drift scan on `2026-06-22 06:07 -03:00` found no remaining
locally fixable pending rows. A targeted search across the tracker, audit,
production docs, README, and test suites for stale/manual/pending/logistical
phrases found only documented external gates, historical fixed-issue wording,
and intentional regression assertions. A structured tracker query for pending
retests that did not name Edge, SSH, terminal, Kerberos, Impala, Linux, CSV
smoke, Level 4, cluster, install, TCP, CWD, or queue evidence returned no rows;
the only `local_test_status` match was the phrase `manual override` in the
already-covered sidebar collapse row.

Additional network diagnostics on `2026-06-22 06:08 -03:00` confirmed the
configured harness files still target `ssh_options: "-p 2222 -o
StrictHostKeyChecking=no"`. Direct `Test-NetConnection` checks to the default
SSH port also failed for both Edge nodes while ICMP ping still succeeded:
`hde2stl020003.mastercard.int:22` (`10.154.178.38`, ping RTT 182 ms,
`TcpTestSucceeded: False`) and `hde2stl020004.mastercard.int:22`
(`10.154.178.39`, ping RTT 183 ms, `TcpTestSucceeded: False`). This makes the
blocker an SSH-port reachability problem from the current network path, not a
missing DNS route or a config fallback to port 22.

```powershell
py -m compileall dispatch scr
```

Result: passed.

```powershell
py -m dispatch --help
```

Result: printed Dispatch CLI help successfully.

```powershell
Import-Csv docs\dispatch_user_story_tracker.csv
```

Result: parsed successfully with 64 rows.

## Fixed Issues

| Area | Issue | Fix | Retest |
|---|---|---|---|
| App shell / sidebar | `Ctrl+B` conflicts with tmux/SSH usage and the toggle action queried the wrong scope. | Changed shortcut to `F2`, updated help text, and queried the active screen for `Sidebar`. | Focused sidebar test and full local suite passed. |
| Sidebar narrow layout | Manual collapse needed to survive auto-collapse sync. | Added manual collapse override in `Sidebar`. | Focused narrow/sidebar test passed. |
| Production docs | Smoke DROP guidance conflicted with destructive-action safety policy. | Clarified scratch-only cleanup for `dispatch_smoke_*` resources created by the smoke run. | Local doc review and full suite passed. |
| Edge smoke docs | Python command hardcoded `python3.10` after probing multiple versions. | Switched smoke command to `PYTHON_BIN=$(command -v python3.11 || command -v python3.10)`. | Local doc review passed; Edge command still pending. |
| CSV launch-CWD smoke docs | Controlled CSV behavior lacked an explicit smoke path. | Added Level 3a controlled CSV launch checks for plain CSV in `/tmp` and no gzip/job-dir CSV output. | Local test coverage added; Edge CSV smoke pending. |
| Historical audit doc | Old audit wording implied a stale test count was current. | Marked the old count as historical/audit-time evidence. | Local doc review passed. |
| Historical implementation plans | Older implementation-plan docs still looked canonical, including one marked `Status: Active`, while containing outdated dashboard and harness assumptions. | Marked implementation-plan docs as historical, pointed readers to the canonical tracker/audit, then moved superseded root docs into `docs/archive/legacy-plans/`. | Focused source-of-truth and docs-root cleanup regressions passed. |
| Goal-backed handoff | The current goal handoff initially lived only in the OS temp directory. | Copied the handoff into `docs/robocop-dispatch-goal-handoff-2026-06-22.md` and kept stale prior handoffs archived. | Handoff file existence and key-section checks passed. |
| Production harness CLI | `py -m tools.prod_tui --help` returned `Unknown command` with exit code 1. | Added shared top-level usage handling for `-h` and `--help`. | Focused CLI help regression and full local suite passed. |
| Production harness start | `py -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml` printed a raw traceback, used direct-command psmux startup that rendered blank, used Unix single-quote SSH remote command quoting on Windows, and left stale sessions after failed starts. | Starts a local shell first, sends SSH into it with Windows-safe quoting, catches failures, prints `Failed to start tmux/SSH session`, and cleans up stale sessions. | Focused psmux/quoting/failure regressions and full local suite passed. |
| Production harness operator instructions | The auth-prompt fallback, smoke/job/level reuse-session hints, and development workflow still told operators to run old direct `tools/prod_tui/robocop_tmux.py` script commands. | Updated active harness output/help and workflow text to the current `py -m tools.prod_tui tmux ... --config ...` module CLI, then added an active harness/docs scan that rejects old direct tmux script commands. | Focused harness CLI, smoke/job/level help, workflow-doc, and active-surface regressions passed. |
| Production harness README | README described one-off remote commands as separate SSH, showed older script entrypoints, and its sample `ssh_options` omitted the required Edge SSH port. | Updated docs to the module CLI, the already-authenticated-pane model, and `ssh_options: "-p 2222 -o StrictHostKeyChecking=no"`. | Focused README consistency regression passed. |
| Production harness install smoke | Automated smoke install still omitted `DISPATCH_PYTHON_BIN` while docs required detected Python. | Added `DISPATCH_PYTHON_BIN=$(command -v python3.11 || command -v python3.10)` to the harness install command. | Focused smoke-install regression and full local suite passed. |
| Production CSV docs | Manual Level 3a CSV smoke was not tied to executable Level 4 Csv/Table+Csv coverage. | Mapped Level 3a to `py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 4` in production docs. | Focused production-doc regression and full local suite passed. |
| Development workflow remote naming | Bitbucket remote URL ending in `autobench.git` was surprising in the Robocop repo. | Documented it as the configured Edge-pull remote naming artifact unless the owner changes it. | Local doc review and full local suite passed. |
| Prefill rerun seam | Prefilled destination could intermittently revert to `Csv` after Textual default radio mount. | Reapplied forced radio selection after refresh and a short timer. | Prefill seam tests and full local suite passed. |
| Manifest writes on Windows | Runner completion could fail when Windows briefly denied replacing `manifest.tmp` with `manifest.json`. | Added retry/backoff around atomic manifest replacement. | Manifest retry regression, runner integration, and full local suite passed. |
| New Job matrix coverage | `NJ-002` had contract coverage but stale `UI manual pending` wording for a local-testable matrix toggle. | Added `test_new_job_matrix_shows_legal_cells_and_toggles` to verify matrix rows and `M` collapse/expand behavior, then updated the tracker evidence/status. | Focused matrix UI regression and full local suite passed. |
| Cancellation gateway coverage | Cancellation rows had UI confirmation coverage and Edge/Linux runner validation pending, but no direct local regression for the TUI gateway sending SIGTERM to the process group. | Added `tests/test_process.py::test_cancel_process_group_sends_sigterm_to_group` and updated `JOB-003` / `JOB-013` tracker evidence. | Focused process regression passed; full Linux runner cancellation still requires Edge/Linux validation. |
| Kerberos timeout and UI matrix coverage | Pending Kerberos rows had parser and basic missing/healthy coverage, but no direct timeout-fallback regression and no dashboard/New Job low-ticket state-matrix assertion. | Added timeout fallback tests for `has_ticket()` / `ticket_ttl_seconds()`, dashboard missing/low/healthy rendering coverage, and New Job low-TTL launch-blocking/summary coverage. | Focused Kerberos regressions passed; real `klist` / `kinit` behavior still requires Edge validation. |
| Install artifact smoke coverage | `JOB-019` only inspected installer text locally even though the story expects runtime directories, config, version, and launcher artifacts. | Added a temp-home/temp-data-root `install.sh` smoke with mocked `klist`, `impala-shell`, and fake Python venv creation. | Focused install smoke passed; real Edge install still pending. |
| Local validation temp pressure | Full pytest failed when C: temporary space filled and pytest could not create `tmp_path` directories. | Updated `tools/dev/local_check.ps1` to use repo-local pytest temp directories and clean them; ignored interrupted temp folders. | Focused script regression and actual `local_check.ps1` passed. |
| Edge network preflight command/docs | Production docs did not tell testers to verify TCP 2222 before requesting RSA/Kerberos time, one page still implied separate direct SSH for one-off commands, the harness had no config-driven preflight command or durable preflight report output, the harness section could still lead operators to start tmux/smoke/job/level after a failed preflight, node-selection handoff could fall back to node 03 when node 04 was intended, and a blank `TimeoutError()` could print an empty failure reason. | Added `python -m tools.prod_tui preflight`, optional `--json-report`, direct `Test-NetConnection` fallback, single authenticated-pane wording, explicit stop-until-connected guidance, node 04 preflight path, selected-node `--config` discipline, timeout fallback text, and current tmux module documentation for the authenticated-pane model. | Focused preflight/docs regressions passed; harness preflight currently reports Edge TCP 2222 timeout for both configured nodes and writes ignored JSON reports. |
| Edge smoke checklist diagnostics | The smoke checklist had stale dashboard-render copy, stale empty-dashboard copy, and startup diagnostics were only indirectly represented in the tracker. | Updated the dashboard render expectation to the current status strip, updated the empty-dashboard expected text, added explicit `APP-004` startup log/version-warning and `DASH-006` empty-state/event-trail tracker rows, and added focused cockpit/docs regressions. | Focused cockpit, doc, and tracker regressions passed locally. |
| Tracker/audit drift | The canonical tracker and completion audit had no executable guard against future row, column, status, evidence-reference, evidence-line-range, local-pending wording, external-gate pending wording, error/fix bookkeeping, pending-summary, pending-matrix, or competing-tracker drift. | Added `tests/test_user_story_tracker.py` to validate tracker columns, unique feature IDs, required story/behavior/evidence fields, all implemented statuses, code/test evidence paths and line ranges, local pending wording, external-gate pending wording, documented-error fix/retest fields, pending rows mirrored in the audit matrix, pending area counts mirrored in the audit summary, and the absence of another tracker spreadsheet under `docs/`. Corrected stale `JOB-021` mock-layer line ranges and filled `JOB-003`'s external-gate disposition while adding the guard. | Focused tracker regression and full local suite passed. |

## Remaining Real-Environment Gates

Two 2026-06-24 node03 sessions closed the harness-coverable gates (launch CWD,
plain CSV, Table+CSV, detached survival, install/upgrade, Python detection,
preflight, harness SSH smoke, and the healthy `klist` status strip) and then the
human-driven interactive gates: low/missing Kerberos launch refusal and the
status strip's missing/low states, real interactive `kinit`, Impala metadata
browse/describe/UI DROP confirmation, POSIX job cancellation, noisy live-log
follow/pause/search/copy, and the Level 3/3a safety and scratch-only cleanup doc
execution. One gate remains:

- BR-001: after redeploying the metadata-list header fix, confirm the Browser
  table list excludes the column header, the count is accurate, and the first
  row auto-describes a real table.

Pending tracker rows mapped to the next Edge validation route:

| Feature | Route | Required evidence |
|---|---|---|
| BR-001 | Impala smoke / redeploy | Header fix redeployed; the Browser table list excludes the column header, the count is accurate, and auto-describe targets a real table. |

No active local tmux sessions named `robocop-prod-test` or `robocop-prod-test-04` were found during this audit; `psmux ls` on `2026-06-22 06:05 -03:00` showed only unrelated `autobench-bitbucket-auth` and `autobench-workflow` sessions. DNS still resolves the configured hosts to `hde2stl020003.mastercard.int` -> `10.154.178.38` and `hde2stl020004.mastercard.int` -> `10.154.178.39`. After the local psmux startup fix, non-secret start attempts against both configured nodes sent the SSH command correctly, but timed out before any Edge shell or authentication prompt appeared. Direct TCP checks on `2026-06-22 05:54 -03:00` showed both hosts reachable by ping from `172.30.19.54` on `Ethernet 6`, but both failed TCP 2222: `hde2stl020003.mastercard.int:2222` (`10.154.178.38`, ping RTT 189 ms, `TcpTestSucceeded: False`) and `hde2stl020004.mastercard.int:2222` (`10.154.178.39`, ping RTT 185 ms, `TcpTestSucceeded: False`). Bounded socket preflights at `2026-06-21 21:52:10 -03:00`, `2026-06-21 22:05:53 -03:00`, and `2026-06-21 22:40:46 -03:00` all timed out after 5 seconds for both hosts on port 2222. The config-driven harness preflight was also run at `2026-06-21 22:48 -03:00`: `py -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5` resolved `10.154.178.38` and failed with `TCP preflight: FAIL - timed out`; `py -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5` resolved `10.154.178.39` and failed with `TCP preflight: FAIL - timed out`. The latest report-producing rerun at `2026-06-22 06:05 -03:00` refreshed `tools/prod_tui/reports/preflight-node03.json` and `tools/prod_tui/reports/preflight-node04.json`; the node 03 report has `generated_at: 2026-06-22T09:06:04.538545+00:00`, the node 04 report has `generated_at: 2026-06-22T09:06:04.571257+00:00`, and both reports have `connected: false`, `error: timed out`, and the expected resolved addresses (`10.154.178.38` and `10.154.178.39`). Failed starts now clean up their local tmux sessions, so there is no reusable Robocop session. The available production reports from before these preflight runs are historical and predate the current local changes, so they are not accepted as completion evidence for the post-fix retest requirement.

Update 2026-06-24: TCP 2222 became reachable and an authenticated node03 session completed the harness suite against the current code. `tools/prod_tui/reports/preflight-node03.json` and `preflight-node04.json` now report `connected: true`. Captured reports: `smoke-node03-edge.json` (21/22; the only failure is the psmux host limit that caps the detached window at 120x30 instead of 120x40, still well above the 80x24 minimum), `job-node03-edge.json` (Level 3 controlled job full pass, including an Impala table verify and scratch cleanup), `level4-node03-edge.json` (Level 4 full pass across SqlFile->Csv, SqlFile->Table+Csv, SqlTemplate->Table, the SqlFile->Table seed, and ExistingTable->Csv), `level5-node03-edge.json` (5/5: concurrency cap, illegal-destination auto-correct, and detached-runner survival across a TUI quit), and `level6-node03-edge.json` (27/27: table data correctness, a soak loop, and upgrade-in-place install). Connection stability required running one harness process per authenticated session with no ad-hoc `tmux` pokes; interleaving manual `capture-pane`/`send-keys` against the live pane is what destabilized earlier runs, and SSH keepalives (`ServerAliveInterval=30 ServerAliveCountMax=1000`) were added to both harness configs. This session closed 11 tracker gates; the remaining 16 need a human-at-terminal SSH pass, interactive Kerberos, or forced failure/queue-full conditions that are mock-covered by design.

Update 2026-06-24 (UI captures): with the node03 SSH session timed out (auto-logout), the four pure-UI gates that depend only on Textual rendering and keybindings — APP-002, APP-003, SIDE-002, and PREV-002 — were validated by driving the real `dispatch.app.DispatchApp` through Textual's `run_test` pilot and exporting native SVG screenshots. `tools/dev/ui_captures.py` builds a clean mock environment (temp data root with config and matching `installed_version`, a healthy ticket TTL, and a launch directory holding a SQL file) and writes nine content-verified SVGs to `tools/prod_tui/reports/ui-captures/`: the global help map and the Ctrl+P command palette listing Overview / New Job / History / Browse metadata / Refresh Kerberos (kinit) (APP-002, also asserted directly against `get_system_commands`); the below-minimum 70x20 size warning and a usable 80x24 layout (APP-003); the expanded sidebar versus auto-collapse under width 100 and manual F2 collapse with the active item and ticket chip retained (SIDE-002); and the SQL preview action bar showing only Copy SQL and Back with no Launch button plus the copy-to-clipboard notification (PREV-002). Toast notifications are not painted by the offline `save_screenshot` compositor, so the size warning and copy notification are asserted from the app's live notification state. SSH keystroke delivery for these bindings was already exercised by the 2026-06-24 node03 harness smoke run; the SVG captures add faithful rendering proof. This closed APP-002, APP-003, SIDE-002, and PREV-002, leaving 12 pending rows that require interactive Kerberos, real Impala metadata, real Linux/POSIX cancellation, a noisy live-log pass, or forced cluster outcomes.

Update 2026-06-24 (JOB-018 disposition): the owner accepted JOB-018 (retryable/fatal/queue-full orchestrator outcomes) as mock-covered rather than deliberately forcing real cluster failure or queue-full conditions on shared capacity. Its behavior is exercised by automated mock scenarios (`syntax_error`, `auth_error`, `table_not_found`, `memory_exceeded`, `all_queues_full`) and the runner/queue-guidance regressions in `tests/test_runner_integration.py`, `tests/test_mock_contract.py`, and `tests/test_production_polish.py::test_job_detail_queue_failure_surfaces_capacity_guidance`. This drops the pending set to 11, all of which require interactive Kerberos, real Impala metadata, real Linux/POSIX cancellation, a noisy live-log pass, or executed smoke-doc confirmation.

Update 2026-06-24 (second node03 session): a second human-driven, authenticated node03 session closed 10 of the 11 remaining gates. Kerberos: the New Job inline summary flagged a missing ticket and disabled launch, and the in-app `k` credential refresh restored a healthy TTL (599m) and re-enabled launch (NJ-007, NJ-008, JOB-015). Impala: the Browser described a scratch table into parsed Column/Type/Comment output and dropped a `dispatch_smoke_*` scratch table after exact-name confirmation, with SHOW/DESCRIBE/DROP exercised through the wrapper (BR-002, BR-003, JOB-016). Live log and cancellation: a synthetic long-running job exercised follow/pause, top/bottom jumps, search, and copy-job-id on a streaming log, and a cancel was rejected then confirmed, sending process-group termination so the runner marked the job Cancelled (JOB-002, JOB-003, JOB-013). Docs: the executed scratch DROP matched the Level 3/3a safety and scratch-only cleanup policy, which read consistently across `docs/production_testing.md` and `docs/edge-node-smoke-test.md` (DOC-001). The session also surfaced one defect: SHOW TABLES kept the `impala-shell --print_header` `name` column header as a phantom table, inflating the count and breaking auto-describe of the first row. The fix (header stripping in `dispatch/impala.py` plus a faithful mock header and a regression test, full suite 224 passed) is landed and locally tested but not yet redeployed, so BR-001 stays pending its post-redeploy retest. This leaves 1 pending row.

## Next Required Action

Run the config-driven preflight first and stop unless the selected node is reachable:

```powershell
py -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json
py -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node04.json
```

If either selected-node report has `connected: false`, keep that report as the
current network-blocker evidence. Do not run `tmux start`, `smoke`, `job`, or `level` until the selected node's preflight report has `connected: true`.

After TCP 2222 is reachable, start or reuse a human-authenticated production
harness session and run the remaining Edge checks against the updated code:

```powershell
py -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml --passcode <RSA_CODE>
py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens
py -m tools.prod_tui job --config tools/prod_tui/config.yaml --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 4 --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 5 --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 6 --reuse-session
```

Repeat with `tools/prod_tui/config-node04.yaml` if node 04 is the intended validation target.

Do not mark the active goal complete until the 1 pending tracker row (BR-001) has current Edge evidence or the user explicitly accepts that row as out of scope.
