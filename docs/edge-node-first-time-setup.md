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
- installing Dispatch for one user on the Edge Node
- validating that the TUI starts correctly

## 1. Prepare the deployable tree locally

Confirm the vendored wheels exist:

```bash
ls vendor/*.whl
```

To rebuild `vendor/` for the Linux edge node from a non-Linux development
host, use the platform-targeted recipe also used by
[`deploy_and_install.ps1`](../deploy_and_install.ps1):

```bash
pip download -r requirements.txt -d vendor \
  --platform manylinux2014_x86_64 --python-version 3.10 --abi cp310 --only-binary=:all:
```

A bare `pip download -r requirements.txt -d vendor` on a non-Linux host
downloads wheels for the host platform, which the Linux edge node cannot use.

### Recommendation: Zip for Upload
For Windows-to-Linux transfers or unstable connections, upload a single ZIP archive to avoid `scp`/`rsync` overhead and potential file corruption.

```powershell
Compress-Archive -Path dispatch, scr, vendor, install.sh, update.sh, pyproject.toml, requirements.txt, VERSION, README.md, docs -DestinationPath dispatch_deploy.zip
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
tree to the previous known-good commit, then run `install.sh` again. For the
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

# Ensure writable storage
mkdir -p /ads_storage/$USER/.dispatch
touch /ads_storage/$USER/.dispatch/.smoke_test
```

## 4. Run the installer

From the deployed tree:

```bash
cd /ads_storage/dispatch
chmod +x update.sh install.sh
DISPATCH_EMAIL=you@example.com DISPATCH_PYTHON_BIN=$(command -v python3.11) ./install.sh
```

For the normal release workflow and recovery-only exact-SHA rollback details, see
[release-workflow.md](release-workflow.md).



## 5. Post-install validation

Launch the TUI:
```bash
dispatch
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
| Permission Denied in `/ads_storage` | Sticky bits or ownership | Use `/ads_storage/$USER/` for personal data (venv, logs, jobs). |

## 6. Production validation harness

For repeatable real-environment validation over SSH and tmux, use the production harness:

- [tools/prod_tui/README.md](../tools/prod_tui/README.md)
- [docs/edge-node-smoke-test.md](./edge-node-smoke-test.md)
