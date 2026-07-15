# Dispatch Release Workflow

Only a Release Operator performs this workflow. Normal development ends at the
merged GitHub pull request.

From the Dispatch checkout:

```powershell
git switch main
git pull --ff-only origin main
python -m pip install -e ".[dev,release]"
python -m pytest -n 4 --dist loadfile
python -m edge_deploy release
```

The command requires clean local `main` exactly matching GitHub `origin/main`,
successful post-merge GitHub CI for that SHA, the configured `bitbucket`
remote, available centralized audit storage, and interactive Edge
authentication. It publishes and deploys one tool only.

When `requirements.txt` changes, edge-deploy-core v1.1.0 builds, transfers,
verifies, and installs a content-addressed offline bundle before updating the
checkout. `install.sh` constructs or reuses the digest-specific shared runtime,
validates it, and atomically activates it. Repository-local `vendor/` wheels
are no longer a release input, and analysts do not run the release installer.

Standard smoke verification invokes
`/ads_storage/dispatch/bin/dispatch --help` explicitly and verifies the active
completion metadata, delivered bundle digest, prior `pip check`, `sqlglot`
import, and runtime permissions. This avoids a stale Release Operator launcher
on `PATH`.

Successful verification creates the same immutable release tag on GitHub and
Bitbucket. Redacted evidence is appended to the Bitbucket-only `release-log`
branch in `edge-deploy-core`.

Rollback is a separate tagged operation:

```powershell
python -m edge_deploy rollback --tag release-<UTC>-<short-sha>
```

Rollback reactivates a retained completed runtime when its bundle digest is
already present; it does not delete or rebuild older runtimes.

Real operator configuration lives at
`%APPDATA%\edge-deploy\config.yaml`. Bootstrap and recovery procedures remain
in [edge-node-first-time-setup.md](edge-node-first-time-setup.md); they are not
normal release paths.
