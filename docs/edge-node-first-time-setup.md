# Edge Node First-Time Setup

This is the canonical first-time bootstrap and install flow for Dispatch on a
real Hadoop Edge Node. It is not the default release workflow. After bootstrap,
use the shared orchestrator:

```powershell
python -m edge_deploy release
```

It covers:

- preparing the deployable tree locally
- uploading the repo and vendored dependency wheels
- installing the shared Dispatch runtime on the Edge Node
- onboarding analysts without personal dependency bundles
- validating that the TUI starts correctly

## 1. Prepare the deployable tree locally

Normal releases use content-addressed bundles managed by edge-deploy-core.
The commands below are bootstrap/recovery guidance only;
`dependency_bundle/` is generated and is not committed.

Use [`deploy_and_install.ps1`](../deploy_and_install.ps1) to download the
Python 3.10 Linux wheels, normalize the requirements file, and create a bundle
manifest with hashes and the same digest schema as edge-deploy-core:

```powershell
./deploy_and_install.ps1
```

The platform-targeted wheel download inside that script is equivalent to:

```bash
pip download -r requirements.txt -d dependency_bundle/wheels \
  --platform manylinux2014_x86_64 --python-version 3.10 --abi cp310 --only-binary=:all:
```

A bare `pip download -r requirements.txt` on a non-Linux host
downloads wheels for the host platform, which the Linux edge node cannot use.
Do not omit the generated `manifest.json`; `install.sh` rejects unverified
wheel directories.

### Recommendation: Zip for Upload
For Windows-to-Linux transfers or unstable connections, upload a single ZIP archive to avoid `scp`/`rsync` overhead and potential file corruption.

```powershell
Compress-Archive -Path dispatch, scr, bin, dependency_bundle, install.sh, onboard.sh, shared_runtime.py, update.sh, pyproject.toml, requirements.txt, VERSION, README.md, docs -DestinationPath dispatch_deploy.zip
```

## 2. Upload the repo to the Edge Node

Recommended target: `/ads_storage/dispatch`

```powershell
scp -P 2222 dispatch_deploy.zip <user>@<edge-node>:/ads_storage/dispatch/
```

On the server, unzip and clean up:
```bash
cd /ads_storage/dispatch
unzip dispatch_deploy.zip
rm dispatch_deploy.zip
```

### Alternative: Bitbucket-backed working tree

When the Edge Node can reach the corporate Bitbucket server, prefer a Git
working tree so the shared release orchestrator can manage ongoing updates. It
keeps the deployed code tied to a commit and makes rollback straightforward.

One-time setup:

```bash
cd /ads_storage
git clone -o bitbucket https://scm.mastercard.int/stash/scm/~e176097/dispatch.git dispatch
cd /ads_storage/dispatch
git remote -v
```

Recovery update, when the shared release orchestrator cannot complete:

```bash
cd /ads_storage/dispatch
GIT_REMOTE=bitbucket GIT_BRANCH=main ./update.sh
```

Exact-commit recovery update:

```bash
cd /ads_storage/dispatch
GIT_REMOTE=bitbucket GIT_BRANCH=main ./update.sh <commit-sha>
```

Rollback uses the same exact-SHA shape as a recovery operation: move the shared
tree to the previous known-good commit, then run `install.sh` to reactivate its
retained digest-specific runtime. For the
repo-local harness recovery command, see
`py -m tools.prod_tui deploy --config tools/prod_tui/config.yaml --commit <previous-good-sha> --rollback-from <current-bad-sha>`.

## 3. Verify Edge Node prerequisites

SSH to the Edge Node (port `2222`; enter the RSA SecurID PASSCODE at the
`Enter PASSCODE:` prompt, then run `kinit` to obtain a Kerberos ticket):

```bash
ssh -p 2222 <user>@<edge-node>
kinit            # enter Kerberos password, then confirm with: klist
```

Then verify the prerequisites:

```bash
# Check Python versions (3.10 or 3.11 are supported)
python3.11 --version || python3.10 --version

which impala-shell
which klist

# Release Operator must own the shared runtime location
test -w /ads_storage/dispatch
```

## 4. Run the installer

From the deployed tree:

```bash
cd /ads_storage/dispatch
chmod +x update.sh install.sh onboard.sh bin/dispatch
DISPATCH_PYTHON_BIN=$(command -v python3.11) ./install.sh
/ads_storage/dispatch/bin/dispatch --help
```

For the normal release workflow and recovery-only exact-SHA rollback details, see
[release-workflow.md](release-workflow.md).



## 5. Post-install validation

Onboard the Release Operator account only if it will also use the TUI:
```bash
/ads_storage/dispatch/onboard.sh
cd /path/to/sql/files && dispatch
```

Confirm:
- Dashboard renders correctly.
- Kerberos indicator is visible.
- Navigation (`N`, `H`, `B`) works.

After the shared tree is deployed, give end users the short setup flow in
[onboarding.md](../onboarding.md). They should not need this operator runbook.

## Gotchas & Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `IndentationError` in dispatch script | Heredoc with spaces | Use `cat <<'EOF'` to avoid variable expansion and ensure exact spacing. |
| SSH Disconnections | Idle timeout | Connect with `ssh -o ServerAliveInterval=30`. |
| Shared runtime permission denied | Wrong owner on `/ads_storage/dispatch/.venv` | Have the Release Operator repair ownership; analysts must not run pip. |
| Private state permission denied | Wrong owner on `/ads_storage/$USER/.dispatch` | Rerun `onboard.sh` as that analyst. |

## 6. Production validation harness

For repeatable real-environment validation over SSH and tmux, use the production harness:

- [tools/prod_tui/README.md](../tools/prod_tui/README.md)
- [docs/edge-node-smoke-test.md](./edge-node-smoke-test.md)
