# Dispatch Edge Deploy Workflow

Run normal releases from `D:\Projects\edge-deploy-core`, not from this repo.

## 1. Default Release

```powershell
cd D:\Projects\robocop
git status --short --branch
.\tools\dev\local_check.ps1
git add <files>
git commit -m "Describe the change"

cd D:\Projects\edge-deploy-core
py -m edge_deploy release --tool robocop --smoke standard
```

Use `--tool both` when Autobench and Dispatch should be released in the same
process.

The release command owns:

- deployment snapshot publication,
- node03 and node04 update,
- interactive RSA prompt handling in the visible terminal,
- safe Git preflight and bounded remote-tracking-ref repair,
- drift and smoke validation,
- JSON release reports under `edge-deploy\reports\release-*`.

## 2. Release Evidence

Accept the release only when:

- `release.json` has `overall_status: "passed"`,
- each Robocop rollout report has `status: "passed"`,
- update, drift, and smoke checks passed for node03 and node04,
- `remote_git_preflight` is present for each node,
- no secret-shaped values are present in the report.

Report the release directory, local source commit, deployment SHA, nodes
updated, and any authentication handoff.

## 3. Recovery Entry Criteria

Use the remaining sections only when:

- the release command is unavailable,
- a release report points to a node-specific condition that needs manual
  inspection,
- a first-time node bootstrap is required,
- offline dependencies must be refreshed outside the orchestrator.

Do not use these commands as the normal release workflow.

## 4. Repo-Local Snapshot Recovery

If the orchestrator cannot publish, the repo-local helper can create a
deployment snapshot:

```powershell
cd D:\Projects\robocop
.\tools\dev\publish_dispatch_snapshot.ps1 -ReviewedCommit <sha> -RunLocalCheck
git fetch bitbucket main
git log --oneline -1 bitbucket/main
```

Record why the orchestrator publish path was bypassed.

## 5. Manual Node Recovery

Prepare authenticated sessions only after inspecting current panes:

```powershell
tmux ls
tmux list-panes -a -F "#{session_name}:#{window_index}.#{pane_index} #{pane_current_command} #{pane_current_path}"
tmux capture-pane -t <session> -p -S -80
```

If SSH has logged out, restart SSH and let the human enter the RSA PASSCODE.

On the node, the recovery update shape is:

```bash
cd /ads_storage/dispatch
GIT_TERMINAL_PROMPT=0 DISPATCH_UPDATE_REMOTE=bitbucket DISPATCH_UPDATE_BRANCH=main ./update.sh <snapshot-sha>
git log --oneline -1
git status --porcelain
```

`update.sh` preserves untracked runtime paths, reasserts shared permissions,
and repairs the known corrupt `refs/remotes/bitbucket/main` signature. If the
script reports that install is needed, run:

```bash
cd /ads_storage/dispatch
DISPATCH_EMAIL=${DISPATCH_EMAIL:-e176097@mastercard.com} DISPATCH_PYTHON_BIN=$(command -v python3.11 || command -v python3.10 || command -v python3) ./install.sh
cat /ads_storage/$USER/.dispatch/installed_version
~/.local/bin/dispatch --help | head -8
```

## 6. Repo-Local Harness Recovery

`tools.prod_tui deploy` is a recovery/diagnostic interface when the shared
release command is unavailable or when a node report needs deeper evidence:

```powershell
py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto --json-report tools/prod_tui/reports/deploy-node03.json
py -m tools.prod_tui drift --config tools/prod_tui/config.yaml --commit <deployment-sha> --json-report tools/prod_tui/reports/drift-node03.json
py -m tools.prod_tui smoke --config tools/prod_tui/config.yaml --level all --save-screens --reuse-session --json-report tools/prod_tui/reports/smoke-node03.json
```

For node04, use `tools/prod_tui/config-node04.yaml` consistently.

## 7. Offline Bootstrap or Dependency Recovery

Use the bundle path only for first-time setup, vendor refreshes, offline
installs, or recovery when the server working tree is not usable:

```powershell
cd D:\Projects\robocop
.\deploy_and_install.ps1
```

The generated `dispatch_deploy.zip` is an artifact and must not be committed.

## 8. Final Recovery Report

Include:

- why the default `edge_deploy release` path was not sufficient,
- local source commit,
- deployment SHA,
- nodes touched,
- remote update/install/smoke evidence,
- drift evidence,
- shared-permission evidence,
- any authentication or remote-state issue.
