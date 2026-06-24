# Implementation Plan: Consolidated Edge Workflow

> Historical / non-canonical planning reference. The canonical Dispatch product
> truth remains `docs/dispatch_user_story_tracker.csv` and
> `docs/dispatch_user_story_completion_audit.md`.
>
> Status: Draft implementation plan, written against commit `9ff568d` on
> 2026-06-24.
>
> Executor rule: implement this plan in small slices and run the verification
> gate for each slice before moving on. Do not push to GitHub or Bitbucket, do
> not consume an RSA code, and do not run real Edge commands unless the operator
> explicitly asks for that action.

## Objective

Move Dispatch onto one repeatable Edge deployment workflow:

1. validate a reviewed local commit,
2. publish exactly one traceable Bitbucket deployment snapshot,
3. update each Edge node to an explicit commit,
4. make the install/reinstall decision explicit,
5. verify drift, smoke, permissions, and rollback with the same report shape,
6. preserve `_seam_deploy` only as the fast authenticated-session iteration
   path.

The outcome should let an operator answer, for each node: which reviewed commit
is deployed, which deployment snapshot delivered it, whether the shared tree is
byte-aligned with the expected runtime files, whether the per-user install is
current, whether permissions are usable by analysts, and which smoke level
passed.

## Current State

Active operational docs and tools already exist:

- `docs/development-workflow.md` is the canonical contributor workflow. It
  already documents `origin` as GitHub, `bitbucket` as the corporate deployment
  remote, the manual deployment snapshot flow, `update.sh`, `_seam_deploy`, and
  the local gate.
- `docs/production_testing.md` is the canonical real Edge validation process. It
  already defines TCP 2222 preflight, the local tmux/psmux + SSH model,
  authentication rules, deployment path choices, and Level 1-4+ smoke
  semantics.
- `docs/edge-node-first-time-setup.md` owns first-time ZIP/Git setup and
  installer guidance.
- `tools/dev/local_check.ps1` is the standard local gate. It runs:
  `py -m compileall dispatch scr`, `py -m pytest tests tools/prod_tui/tests -q`,
  and `py -m dispatch --help`.
- `tools/dev/git_sync_status.ps1` checks the Bitbucket remote URL, dirty state,
  and ahead/behind counts, then points the operator to the snapshot flow.
- `tools/dev/edge_sync.ps1` wraps `_seam_deploy` for authenticated-session
  verify/sync on node 03, node 04, or both.
- `update.sh` already fetches `bitbucket/main`, resets the shared tree, and
  reapplies readable/traversable permissions with `chmod 755` and
  `chmod -R a+rX`.
- `tools/prod_tui/__main__.py` exposes public harness commands:
  `preflight`, `tmux`, `smoke`, `job`, and `level`.
- `tools/prod_tui/_seam_deploy.py` exists, but is intentionally a lower-level
  fast-iteration helper rather than the committed deployment path.

Canonical product-truth docs:

- `docs/dispatch_user_story_tracker.csv` has 64 implemented feature rows.
- `docs/dispatch_user_story_completion_audit.md` says the remaining gap is 27
  real-environment retest gates blocked by Edge SSH/TCP 2222 reachability, not
  local implementation.

## Gaps To Close

The current workflow is close, but still asks the operator to assemble too much
deployment state manually:

- The Bitbucket snapshot publish path is documented but not encoded in a helper
  that records reviewed commit, deployment snapshot commit, source branch, and
  push target.
- The Edge update path exists in `update.sh`, but there is no public harness
  command that drives the same update/install/report routine per configured
  node through the already-authenticated tmux pane.
- `update.sh` does not yet give a first-class repair path for stale or broken
  remote-tracking refs.
- Drift verification exists as `_seam_deploy verify`, but the public workflow
  needs a stable `tools.prod_tui` command and JSON report that compares only
  runtime-critical files.
- Deployment, drift, smoke, permission, and rollback reports do not yet share a
  single minimum schema.
- Permission verification is mostly procedural knowledge even though permission
  restoration is already part of `update.sh`.
- Rollback is documented as "same shape" but lacks a reportable command path
  with previous SHA, target SHA, reinstall decision, smoke result, and node.

## Non-Negotiable Constraints

- Git remains the deployable source of truth for committed production
  deployments.
- Bitbucket remains a deployment transport, not the review archive.
- Node 03 and node 04 have independent filesystems; every claim must be
  node-specific.
- `scr/` orchestrators are production-sensitive. Do not change `scr/` unless a
  plan explicitly requires it and ADR-0005 allows it.
- `_seam_deploy sync` is for fast iteration after a human-authenticated session
  exists. It must not become the canonical committed deployment path.
- Generated reports, screens, logs, caches, and deployment ZIPs must not be
  committed.
- A failed TCP 2222 preflight is a valid blocker artifact. Do not request an RSA
  code until preflight passes for the selected node.

## Target Command Surface

The implementation should converge on these supported commands:

```powershell
# local gate
.\tools\dev\local_check.ps1

# inspect local readiness for deployment
.\tools\dev\git_sync_status.ps1

# publish a reviewed commit as the deployment snapshot on bitbucket/main
.\tools\dev\publish_dispatch_snapshot.ps1 -ReviewedCommit <sha>

# preflight each node before auth
py -m tools.prod_tui preflight --config tools/prod_tui/config.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node03.json
py -m tools.prod_tui preflight --config tools/prod_tui/config-node04.yaml --timeout 5 --json-report tools/prod_tui/reports/preflight-node04.json

# after a human-authenticated tmux session exists for the node
py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto --json-report tools/prod_tui/reports/deploy-node03.json
py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha> --json-report tools/prod_tui/reports/drift-node03.json
py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens --json-report tools/prod_tui/reports/smoke-node03.json
```

Node 04 must use `tools/prod_tui/config-node04.yaml` for the same command
shapes. A wrapper may fan out over both nodes, but the underlying report files
must remain node-specific.

## Report Contract

Every new deployment-related JSON report should include at least:

- `timestamp`
- `node`
- `host`
- `repo_path`
- `operation` (`publish`, `deploy`, `drift`, `smoke`, `permission`, `rollback`)
- `reviewed_commit` when known
- `deployment_commit`
- `previous_remote_commit` when the operation changes a node
- `install_decision` (`run`, `skip`, `auto`, or `not_applicable`)
- `status` (`passed`, `failed`, or `blocked`)
- `checks[]` with `name`, `passed`, `message`, and optional evidence fields

Keep secrets out of reports. RSA passcodes, Kerberos passwords, and personal
environment values must never be printed or persisted.

## Phase 1: Encode The Bitbucket Snapshot Publish Path

Files in scope:

- `tools/dev/publish_dispatch_snapshot.ps1` (new)
- `tools/dev/git_sync_status.ps1`
- `docs/development-workflow.md`
- `tools/prod_tui/tests/test_cli.py` or a new focused test if the existing docs
  guard is the right fit

Implementation:

1. Add `tools/dev/publish_dispatch_snapshot.ps1`.
2. Inputs: `-ReviewedCommit <sha>`, optional `-Remote bitbucket`, optional
   `-Branch main`, optional `-DryRun`.
3. Validate that the remote URL matches the Dispatch Bitbucket remote before
   doing anything.
4. Validate that `<sha>` resolves locally and that `tools/dev/local_check.ps1`
   has been run by requiring either a clean explicit `-LocalCheckPassed`
   confirmation or a `-RunLocalCheck` switch. Prefer `-RunLocalCheck` for the
   normal path.
5. Fetch `bitbucket/main`, create or reset a temporary deployment work branch,
   soft-reset it to the reviewed commit, create an operator-authored snapshot
   commit, and push `HEAD:main`.
6. Print and optionally write a small JSON summary containing reviewed commit,
   previous Bitbucket commit, snapshot commit, remote, branch, and timestamp.
7. Update `git_sync_status.ps1` to point to the helper instead of manual command
   assembly.
8. Update `docs/development-workflow.md` so the manual commands become the
   fallback/troubleshooting path, not the main path.

Acceptance criteria:

- An operator can publish a reviewed commit with one supported command.
- The output identifies both the reviewed local commit and the resulting
  Bitbucket deployment snapshot commit.
- Dry-run mode prints the commands and intended commits without pushing.

Verification:

```powershell
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- The helper cannot prove the target remote URL is the Dispatch Bitbucket repo.
- The reviewed commit does not resolve locally.
- The command would push anything other than `HEAD:main` to the configured
  Bitbucket remote.

## Phase 2: Add A Public Edge Deploy Command

Files in scope:

- `tools/prod_tui/__main__.py`
- `tools/prod_tui/robocop_tmux.py`
- `tools/prod_tui/deploy.py` (new)
- `tools/prod_tui/tests/`
- `docs/development-workflow.md`
- `docs/production_testing.md`
- `tools/prod_tui/README.md`

Implementation:

1. Add `py -m tools.prod_tui deploy`.
2. Require `--config` and `--commit`. Optional flags:
   `--install auto|always|never`, `--json-report`, and `--reuse-session`.
3. Reuse the existing `TmuxDriver` authenticated-pane model. Do not open a
   second SSH connection for remote commands.
4. Remote command shape:

   ```bash
   cd <repo_path> &&
   DISPATCH_UPDATE_REMOTE=bitbucket DISPATCH_UPDATE_BRANCH=main ./update.sh <commit-sha>
   ```

5. Decide install behavior:
   - `always`: run `DISPATCH_EMAIL=<operator_email> DISPATCH_PYTHON_BIN=$(command -v python3.11 || command -v python3.10) ./install.sh`
   - `never`: skip install and record why.
   - `auto`: run install when dependency, packaging, installer, version, or
     entrypoint files changed between previous deployed commit and target
     commit; otherwise skip.
6. Record previous node commit before update and target commit after update.
7. Emit a deploy report using the report contract.
8. Update docs to make this command the normal post-publish node promotion path.

Acceptance criteria:

- Node 03 and node 04 use the same command shape with different config files.
- A deploy report captures previous commit, target commit, install decision,
  update result, and final node commit.
- The command refuses to run if no authenticated session exists and
  `--reuse-session` was requested.

Verification:

```powershell
py -m tools.prod_tui --help
py -m tools.prod_tui deploy --help
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- Implementing the deploy command appears to require storing RSA or Kerberos
  secrets.
- The command cannot reuse the existing authenticated tmux pane.
- The install decision cannot be explained in the report.

## Phase 3: Harden `update.sh` Ref Repair And Permission Evidence

Files in scope:

- `update.sh`
- `tools/prod_tui/deploy.py`
- `tools/prod_tui/tests/`
- `docs/development-workflow.md`
- `docs/edge-node-first-time-setup.md`

Implementation:

1. Teach `update.sh` to detect the known stale
   `refs/remotes/bitbucket/main` failure case.
2. On that failure, remove only the stale remote-tracking ref and retry:

   ```bash
   git update-ref -d refs/remotes/<remote>/<branch>
   git fetch --prune <remote> <branch>:refs/remotes/<remote>/<branch>
   ```

3. Keep the current permission restoration:
   `chmod 755 "$ROOT_DIR"` and `chmod -R a+rX "$ROOT_DIR"`.
4. Add a permission verification step after reset:
   - repo root is traversable,
   - `update.sh` and `install.sh` are executable,
   - tracked runtime files are readable,
   - generated report/cache directories are not treated as deploy drift.
5. Have the deploy command include permission evidence in its JSON report.
6. Document the exact stale-ref failure signature and recovery path.

Acceptance criteria:

- A stale remote-tracking ref is handled by the scripted path, not by operator
  improvisation.
- Permission evidence is available for every deploy report.
- Analysts other than the deploying user can read and traverse the shared tree.

Verification:

```powershell
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

If a POSIX shell is available locally, also run:

```powershell
sh -n update.sh
```

STOP conditions:

- The repair would delete anything outside `refs/remotes/<remote>/<branch>`.
- The update path would remove untracked runtime/vendor files that the existing
  workflow intentionally preserves.

## Phase 4: Promote Drift Verification To A Public Command

Files in scope:

- `tools/prod_tui/__main__.py`
- `tools/prod_tui/drift.py` (new)
- `tools/prod_tui/_seam_deploy.py`
- `tools/dev/edge_sync.ps1`
- `tools/prod_tui/tests/`
- `docs/development-workflow.md`
- `tools/prod_tui/README.md`

Implementation:

1. Add `py -m tools.prod_tui drift`.
2. Reuse `_seam_deploy verify` internals where practical, but expose a stable
   public command and report schema.
3. Compare runtime-critical tracked files only:
   - `dispatch/**/*.py`
   - `dispatch/**/*.tcss`
   - `scr/**/*.py`
   - `install.sh`
   - `update.sh`
   - `pyproject.toml`
   - `requirements.txt`
   - `VERSION`
4. Ignore generated reports, screens, logs, caches, `.pyc`, deployment ZIPs,
   and local config secrets.
5. Report `MATCH`, `DRIFT`, `MISSING`, and `EXTRA_RUNTIME` counts.
6. Keep `tools/dev/edge_sync.ps1` as the legacy/fast-session wrapper, but point
   docs at `py -m tools.prod_tui drift` for release evidence.

Acceptance criteria:

- The operator can answer "does node03 match the expected commit?" with one
  command.
- Running the command for node03 and node04 against the same local tree gives
  comparable report files.
- Drift reports do not fail because of generated harness artifacts.

Verification:

```powershell
py -m tools.prod_tui drift --help
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- The command would upload or modify remote files. Drift is read-only.
- The report includes secret values or personal config contents.

## Phase 5: Normalize Production Validation Levels And Reports

Files in scope:

- `tools/prod_tui/smoke_test.py`
- `tools/prod_tui/controlled_job.py`
- `tools/prod_tui/levels.py`
- `tools/prod_tui/reporting.py` (new, if useful)
- `tools/prod_tui/tests/`
- `docs/production_testing.md`
- `docs/edge-node-smoke-test.md`
- `tools/prod_tui/README.md`

Implementation:

1. Introduce a small shared reporting helper if it reduces duplication across
   preflight, deploy, drift, smoke, job, and level commands.
2. Preserve existing report fields for backward compatibility, but add the
   minimum report contract fields where missing.
3. Keep validation levels explicit:
   - Level 1: shell/TUI smoke, no job launch.
   - Level 2: install/runtime environment checks, no destructive action.
   - Level 3: controlled `SELECT 1 AS smoke_test_value` table job.
   - Level 3a: manual CSV smoke counterpart.
   - Level 4: executable Source x Destination breadth.
   - Level 5: supervision and safety semantics.
   - Level 6: opt-in production fidelity.
4. Ensure every command documents when it is safe, controlled, or blocked.
5. Make the report path explicit in examples so production claims can attach the
   exact JSON artifact.

Acceptance criteria:

- Every deployment report identifies node, host, repo path, commit, validation
  level or operation, and pass/fail/blocked status.
- Docs no longer require the operator to infer which smoke level to run for a
  deployment change.

Verification:

```powershell
py -m tools.prod_tui smoke --help
py -m tools.prod_tui job --help
py -m tools.prod_tui level --help
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- Normalizing reports would break existing tests without a compatibility path.
- A production level would launch arbitrary user SQL or touch non-smoke tables.

## Phase 6: Make Rollback A First-Class Operation

Files in scope:

- `tools/prod_tui/deploy.py`
- `docs/development-workflow.md`
- `docs/production_testing.md`
- `tools/prod_tui/README.md`
- `tools/prod_tui/tests/`

Implementation:

1. Add `--rollback-from <sha>` or a dedicated `rollback` mode to the deploy
   command. Keep the underlying remote action the same exact-commit
   `update.sh <previous-good-sha>` path.
2. Require the operator to provide both:
   - the current bad commit, and
   - the previous known-good target commit.
3. Use the same install decision logic as deploy.
4. Require a post-rollback smoke command in docs and include the smoke report
   path in the rollback report.
5. Document rollback as an exact SHA operation, not "go back to main".

Acceptance criteria:

- Rollback produces a node-specific report with previous SHA, target SHA,
  install decision, update result, permission result, and smoke result.
- Rollback instructions are command-shaped and do not depend on verbal
  convention.

Verification:

```powershell
py -m tools.prod_tui deploy --help
py -m pytest tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- The rollback path cannot identify the current node commit before changing it.
- The operator cannot name the previous known-good SHA.

## Phase 7: Add End-To-End Operator Runbook Checks

Files in scope:

- `docs/development-workflow.md`
- `docs/production_testing.md`
- `docs/edge-node-first-time-setup.md`
- `tools/prod_tui/tests/test_cli.py`
- `tests/` if the existing active-docs guard belongs there

Implementation:

1. Add doc guard tests that reject stale direct calls to old script entrypoints
   when a public `py -m tools.prod_tui ...` command exists.
2. Add doc guard tests that ensure the active docs mention:
   - preflight before RSA,
   - node-specific configs,
   - publish helper,
   - deploy command,
   - drift command,
   - exact-SHA rollback,
   - generated artifact hygiene.
3. Keep `docs/archive/` historical; do not move this plan there until the work
   is superseded or complete.

Acceptance criteria:

- The active docs tell one coherent story from local commit through rollback.
- Future edits cannot easily reintroduce stale command shapes.

Verification:

```powershell
py -m pytest tests tools/prod_tui/tests -q
.\tools\dev\local_check.ps1
```

STOP conditions:

- A docs guard would forbid a command that is still intentionally supported.
- The plan starts duplicating canonical tracker/audit state instead of linking
  to `docs/dispatch_user_story_tracker.csv` and
  `docs/dispatch_user_story_completion_audit.md`.

## Recommended Delivery Order

1. Phase 1: publish helper and docs.
2. Phase 2: public deploy command.
3. Phase 3: ref repair and permission evidence.
4. Phase 4: public drift command.
5. Phase 5: shared report contract and validation-level cleanup.
6. Phase 6: rollback mode.
7. Phase 7: runbook/docs guards.

This order keeps the operator path usable after each slice: first publish, then
update, then repair/permissions, then drift, then richer reports, then rollback,
then regression guards.

## Definition Of Done

All of the following must be true:

- `.\tools\dev\local_check.ps1` passes.
- `py -m tools.prod_tui --help` lists `preflight`, `tmux`, `smoke`, `job`,
  `level`, `deploy`, and `drift`.
- A reviewed commit can be published to Bitbucket with the snapshot helper and
  produces a traceable summary.
- Each node can be updated to an explicit commit with the public deploy command
  after a human-authenticated tmux session exists.
- Drift, smoke, permission, deploy, and rollback reports use the shared minimum
  schema.
- The docs explain when to run `install.sh`, when to skip it, when to use
  `_seam_deploy`, and when a failed TCP 2222 preflight is the correct blocker.
- Rollback is documented and executable as an exact-SHA update plus reinstall
  decision plus smoke.
- Generated reports/screens/logs/ZIPs remain uncommitted.
- Remaining unclosed user-story gates are only real Edge/Kerberos/Impala/SSH
  validation gates recorded in the canonical tracker/audit.

## Human-Gated Acceptance

These checks cannot be completed by local mocks alone:

- TCP 2222 preflight passes for node 03 and node 04 from the operator's network
  path.
- A human enters RSA and Kerberos credentials in the live session.
- `py -m tools.prod_tui deploy` runs against both nodes.
- `py -m tools.prod_tui drift` reports no unexpected drift for both nodes.
- Level 1/2 smoke passes on both nodes.
- Level 3+ controlled job checks pass where the change requires them.
- Analysts other than the deploying user can traverse and execute the shared
  tree after deployment.

If these are blocked by network or credentials, keep the latest preflight or
session report as the blocker artifact and do not mark the production workflow
complete.
