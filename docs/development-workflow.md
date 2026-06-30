# Dispatch Development and Release Workflow

This is the canonical workflow for Dispatch/Robocop development and production
release. The default release path is the shared release orchestrator in
`D:\Projects\edge-deploy-core`; repo-local deployment commands are retained for
bootstrap, recovery, and deep troubleshooting.

## Default Workflow

1. Start from `main` unless the user explicitly asks for another branch.

   ```powershell
   cd D:\Projects\robocop
   git status --short --branch
   git branch -vv
   ```

2. Make the change and run focused checks for the touched files.

3. Run the local gate before committing:

   ```powershell
   .\tools\dev\local_check.ps1
   ```

4. Commit the reviewed change locally:

   ```powershell
   git diff
   git add <files>
   git commit -m "Describe the change"
   ```

5. Release from `edge-deploy-core`:

   ```powershell
   cd D:\Projects\edge-deploy-core
   py -m edge_deploy release --tool robocop --smoke standard
   ```

   Use `--tool both` when Autobench and Dispatch must be released together.
   The release command publishes the deployable snapshot, drives node03 and
   node04 updates, handles the interactive RSA prompts in the visible terminal,
   runs drift/smoke validation, and writes the release evidence under
   `D:\Projects\edge-deploy-core\edge-deploy\reports\release-*`.

6. Verify the release report:

   - `release.json` has `overall_status: "passed"`.
   - Every Robocop rollout has `status: "passed"`.
   - `remote_git_preflight` is present for each node.
   - Drift and smoke checks passed for node03 and node04.
   - No secret-shaped values were written to the report.

## Remotes

Keep both remotes configured:

- `origin`: GitHub (`pedrochagasmaster/robocop`), used for issues and review.
- `bitbucket`: corporate deployment remote for Dispatch:
  `https://scm.mastercard.int/stash/scm/~e176097/dispatch.git`.

Configure Bitbucket once if needed:

```powershell
git remote add bitbucket https://scm.mastercard.int/stash/scm/~e176097/dispatch.git
git remote -v
```

If the remote already exists with the wrong URL:

```powershell
git remote set-url bitbucket https://scm.mastercard.int/stash/scm/~e176097/dispatch.git
```

Do not push to either remote from an agent session unless the user explicitly
asks. The release orchestrator owns the normal deployment push.

## Release Decision Table

| Situation | Use | Scope |
| --- | --- | --- |
| Normal development release | `py -m edge_deploy release --tool robocop --smoke standard` from `D:\Projects\edge-deploy-core` | Default path for production promotion, node updates, drift, smoke, and report evidence. |
| Coordinated Autobench + Dispatch release | `py -m edge_deploy release --tool both --smoke standard` | Default path when both tools need the same release process. |
| Exact rollback or targeted recovery | `edge_deploy release` with the selected rollback/recovery option, or the repo-local skill when the orchestrator cannot proceed | Operator-controlled exception; record the report path and target SHA. |
| First-time node bootstrap or offline dependency refresh | `deploy_and_install.ps1`, `install.sh`, and `vendor/` refresh | Bootstrap/recovery only, not the default release path. |
| Low-level node diagnosis | `tools.prod_tui`, `update.sh`, tmux/SSH inspection, `_seam_deploy` | Deep troubleshooting only, preferably after checking the release report. |

## What the Release Orchestrator Does

For Robocop/Dispatch, `edge_deploy release` is responsible for the end-to-end
release:

- confirms the local source commit,
- publishes the deployment snapshot to the corporate remote,
- updates `/ads_storage/dispatch` on node03 and node04,
- uses a safe Git fetch shape and self-heals the known corrupt
  `refs/remotes/bitbucket/main` condition,
- preserves per-user runtime state,
- records update, drift, smoke, and permission evidence,
- produces machine-readable reports under `edge-deploy/reports/release-*`.

The operator may still have to type RSA PASSCODEs in the visible terminal.
Manual tmux attachment and node-side commands are not part of the default path.

## Recovery and Bootstrap Paths

Use `.agents/skills/dispatch-edge-deploy/WORKFLOW.md` only when the normal
release command is unavailable or the release report points to a node-specific
condition that requires manual inspection.

Repo-local commands such as these are valid only in that recovery/bootstrap
context:

```powershell
.\tools\dev\publish_dispatch_snapshot.ps1 -ReviewedCommit <sha> -RunLocalCheck
.\deploy_and_install.ps1
py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <deployment-sha> --install auto --json-report tools/prod_tui/reports/deploy-node03.json
```

```bash
cd /ads_storage/dispatch
DISPATCH_UPDATE_REMOTE=bitbucket DISPATCH_UPDATE_BRANCH=main ./update.sh <commit-sha>
./install.sh
```

When using recovery paths, record the node, target SHA, command output, drift
result, smoke result, and why the default release command was not sufficient.

## Production Validation

The default validation is the release report produced by `edge_deploy release`.
Use the repo-local production harness for additional diagnosis or deeper
coverage:

```powershell
cd D:\Projects\robocop
py -m tools.prod_tui smoke --config tools/prod_tui/config-node04.yaml --level all --save-screens
py -m tools.prod_tui job --config tools/prod_tui/config-node04.yaml --reuse-session
py -m tools.prod_tui level --config tools/prod_tui/config-node04.yaml --level 4 --reuse-session
```

Use Level 4-6 only for changes that affect job launch, status, supervision,
destination behavior, or production parity.

## Change Hygiene

- Do not commit generated artifacts such as `dispatch_deploy.zip`,
  `tools/prod_tui/reports/`, `tools/prod_tui/screens/`, or captured logs.
- Do not commit RSA passcodes, Kerberos passwords, personal config, or
  downloaded ad hoc server files.
- Keep `scr/` changes narrow and follow ADR-0005.
- Prefer the orchestrated release report over ad hoc terminal notes for release
  evidence.
- If any manual server edit occurs, run drift detection before claiming parity.
