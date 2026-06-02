# Edge Node First-Time Setup

This is the canonical first-time deployment and install flow for Dispatch on a real Hadoop Edge Node.

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

If `vendor/` needs to be refreshed, rebuild it locally:

```bash
python -m pip download -r requirements.txt -d vendor
```

### Recommendation: Zip for Upload
For Windows-to-Linux transfers or unstable connections, upload a single ZIP archive to avoid `scp`/`rsync` overhead and potential file corruption.

```powershell
Compress-Archive -Path dispatch, scr, vendor, install.sh, pyproject.toml, requirements.txt, VERSION, README.md, docs -DestinationPath dispatch_deploy.zip
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

## 3. Verify Edge Node prerequisites

SSH to the Edge Node and verify:

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
chmod +x install.sh
DISPATCH_EMAIL=you@example.com DISPATCH_PYTHON_BIN=$(command -v python3.11) ./install.sh
```



## 5. Post-install validation

Launch the TUI:
```bash
dispatch
```

Confirm:
- Dashboard renders correctly.
- Kerberos indicator is visible.
- Navigation (`N`, `H`, `B`) works.

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
