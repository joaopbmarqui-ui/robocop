# Robocop Dispatch Goal Handoff

Generated: 2026-06-22
Workspace: `D:\Projects\robocop`

## Purpose For Next Goal-Backed Agent

Continue the active objective:

> Use subagents to inventory every Dispatch feature, create user stories and expected behavior from code, maintain one canonical spreadsheet, test every story, document all errors, fix logistical or UX errors, and retest every behavior after fixes.

Do **not** mark the goal complete unless the 27 remaining real-environment gates have current Edge evidence, or the user explicitly accepts those gates as out of scope.

## Current Verdict

Local work is complete as of the latest validation. The remaining work is real production/Edge environment validation.

Canonical artifacts:

- `docs/dispatch_user_story_tracker.csv`
- `docs/dispatch_user_story_completion_audit.md`

Current tracker state:

- 64 user-story rows
- 0 non-implemented rows
- 27 pending retests
- Pending rows are all Edge/SSH/Kerberos/Impala/Linux/cluster/real-terminal validation items.

Latest local validation evidence in the audit:

- `.\tools\dev\local_check.ps1`
- Result: `295 passed, 1 skipped in 93.88s`
- `Local check passed.`

## Hard Blocker

The production validation loop is blocked by Edge SSH reachability from the current network path.

Current preflight artifacts:

- `tools/prod_tui/reports/preflight-node03.json`
- `tools/prod_tui/reports/preflight-node04.json`

Both reports show:

- `connected: false`
- `error: timed out`
- endpoint port: `2222`

The completion audit also records direct network diagnostics: both configured Edge hosts resolved and responded to ping, but TCP `2222` failed, and default SSH TCP `22` also failed. There is no active reusable Robocop `psmux` session.

Do not consume RSA/SecurID/Kerberos time until a selected node preflight reports `connected: true`.

## Next Required Commands

Run preflight first:

```powershell
py -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json
py -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node04.json
```

If either selected node becomes reachable, proceed with a human-authenticated harness session. Keep secrets in the interactive prompt; do not paste or echo passcodes/passwords in chat.

```powershell
py -m tools.prod_tui tmux start --config tools/prod_tui/config.yaml --passcode <RSA_CODE>
py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens
py -m tools.prod_tui job --config tools/prod_tui/config.yaml --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 4 --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 5 --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config.yaml --level 6 --reuse-session
```

Repeat with `tools/prod_tui/config-node04.yaml` if node 04 is the intended target.

## Pending Story Groups

The 27 pending tracker rows are:

- App shell / SSH terminal: launch CWD, F2/key delivery, terminal resize
- Sidebar: real SSH visual collapse
- Dashboard/New Job/Kerberos: real `klist`, low-ticket, and `kinit` behavior
- SQL preview: terminal clipboard behavior
- Browser/Impala: real SHOW/DESCRIBE/DROP scratch-schema flow
- Job detail/runner: noisy logs, POSIX cancellation, disconnect survival
- Runner/job breadth: CSV, Table+Csv, Level 4 job-type breadth
- Orchestrators: real cluster retry/fatal/queue-full outcomes
- Install: real Edge install on `/ads_storage/...`
- Production docs/harness: execute documented commands against the real node
- Preflight: TCP 2222 must succeed before consuming auth time

Use `docs/dispatch_user_story_completion_audit.md` for the exact matrix and required evidence per feature ID.

## Recent Local Fixes Already Completed

Do not redo these unless new drift is found:

- Canonical tracker created and guarded.
- Completion audit created and guarded.
- Sidebar shortcut changed from `Ctrl+B` to `F2`; sidebar active-screen lookup fixed.
- Manifest Windows atomic-write retry/backoff added.
- New Job prefill radio reapply fixed.
- CSV launch-CWD coverage and Level 3a/4 docs added.
- Production harness top-level `--help`, local psmux shell startup, Windows SSH quoting, start-failure cleanup, and traceback-free errors fixed.
- `tools.prod_tui preflight` command and JSON reporting added.
- README/docs updated for TCP 2222 preflight, selected-node `--config`, single authenticated-pane model, and module CLI.
- Local check now uses repo-local temp directories and cleans them.
- Startup diagnostics, dashboard empty state/event trail, smoke checklist, and historical implementation-plan source-of-truth drift fixed.
- Active harness/docs now reject old direct `robocop_tmux.py` command hints.

## Suggested Skills

Use these skills first in the next session:

- `dispatch-textual-tui`: if touching `dispatch/app.py`, `dispatch/screens/`, TUI tests, mocks, async/process behavior, or UI/terminal behavior.
- `tdd`: for any new local bugfix or regression.
- `receiving-code-review`: if a subagent or reviewer reports local drift.
- `handoff`: if the next agent needs to transfer state again.

## Validation To Run After Any Local Change

Focused:

```powershell
py -m pytest tests\test_user_story_tracker.py tools\prod_tui\tests\test_cli.py tools\prod_tui\tests\test_tmux_commands.py tools\prod_tui\tests\test_smoke_install.py tools\prod_tui\tests\test_levels_logic.py -q
```

Full:

```powershell
.\tools\dev\local_check.ps1
```

Hygiene:

```powershell
git diff --check
Get-ChildItem -Force .local-check-tmp, .local-check-pytest -ErrorAction SilentlyContinue
```

Known `git diff --check` behavior: it reports LF/CRLF warnings but no whitespace errors.

## Current Dirty Worktree

This branch/worktree is intentionally dirty with the objective work. Preserve unrelated dirty-worktree boundaries; do not revert changes unless explicitly asked.

Expected notable untracked canonical artifacts:

- `docs/dispatch_user_story_tracker.csv`
- `docs/dispatch_user_story_completion_audit.md`
- `tests/test_user_story_tracker.py`
- `tools/prod_tui/preflight.py`
- `tools/prod_tui/tests/test_cli.py`
- `tools/prod_tui/tests/test_preflight.py`
- `tools/prod_tui/tests/test_local_check.py`
- `tools/prod_tui/tests/test_smoke_install.py`
- `tests/test_process.py`

Expected modified areas include Dispatch TUI files, production docs, harness code, and focused tests. Use `git status --short` for exact current state.

## Completion Rule

Only call `update_goal(status="complete")` when the prompt-to-artifact audit proves:

1. The 64 tracker rows remain complete and coherent.
2. The 27 pending real-environment rows have current Edge evidence, or the user explicitly accepts them as out of scope.
3. Post-fix retesting evidence is recorded in the tracker/audit.
4. No local/logistical/UX drift remains.

Until then, keep the goal active.
