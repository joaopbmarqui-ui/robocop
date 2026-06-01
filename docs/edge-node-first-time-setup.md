# Edge Node First-Time Setup

This is the canonical first-time deployment and install flow for Dispatch on a real Hadoop Edge Node.

It covers:

- preparing the deployable tree locally
- uploading the repo and vendored dependency wheels
- installing Dispatch for one user on the Edge Node
- validating that the TUI starts correctly

## What gets deployed

Dispatch is deployed as a repo checkout under `/ads_storage/dispatch`.

Important detail: `install.sh` does **not** install a prebuilt Dispatch application wheel. It does two separate things:

1. installs pinned dependency wheels from `vendor/`
2. installs the repo itself from the deployed checkout with `pip install --no-deps -e "$ROOT_DIR"`

That means the remote server needs:

- `dispatch/`
- `scr/`
- `vendor/`
- `install.sh`
- `pyproject.toml`
- `requirements.txt`
- `VERSION`

## 1. Prepare the deployable tree locally

From your local checkout, confirm the vendored wheels exist:

```bash
ls vendor/*.whl
```

If `vendor/` needs to be refreshed, rebuild it locally:

```bash
python -m pip download -r requirements.txt -d vendor
```

For this repo, that downloads the pinned Textual dependency set used by the TUI. The current app code itself still comes from the uploaded repo tree, not from a built wheel.

## 2. Upload the repo to the Edge Node

Recommended target:

```bash
/ads_storage/dispatch
```

Example using `rsync`:

```bash
rsync -av --delete \
  dispatch scr vendor install.sh pyproject.toml requirements.txt VERSION README.md docs \
  <user>@<edge-node>:/ads_storage/dispatch/
```

Example using `scp`:

```bash
scp -r \
  dispatch scr vendor install.sh pyproject.toml requirements.txt VERSION README.md docs \
  <user>@<edge-node>:/ads_storage/dispatch/
```

If you use another deploy mechanism, preserve the same directory layout on the server.

## 3. Verify Edge Node prerequisites

SSH to the Edge Node:

```bash
ssh <user>@<edge-node>
```

Then verify the required runtime environment:

```bash
python3.10 --version
which impala-shell
which klist
mkdir -p /ads_storage/$USER/.dispatch
touch /ads_storage/$USER/.dispatch/.smoke_test
```

Dispatch expects:

- Python 3.10
- `impala-shell` on `PATH`
- `klist` on `PATH`
- writable `/ads_storage/$USER/`

## 4. Run the installer

From the deployed tree:

```bash
cd /ads_storage/dispatch
DISPATCH_EMAIL=you@example.com DISPATCH_PYTHON_BIN=$(command -v python3.10) ./install.sh
```

What `install.sh` does:

- creates `/ads_storage/$USER/.dispatch/jobs`
- creates or refreshes `/ads_storage/$USER/.dispatch/venv`
- installs dependencies from `/ads_storage/dispatch/vendor`
- installs the Dispatch repo into that venv
- creates `~/.local/bin/dispatch` as a shortcut to the venv entrypoint
- writes `/ads_storage/$USER/.dispatch/config.json` on first run
- writes `/ads_storage/$USER/.dispatch/installed_version`

The installer is idempotent. Re-running it preserves `config.json` and `jobs/`.

## 5. Start the TUI

Open a new shell after install, or reload your shell startup file if needed, then launch from the directory containing your SQL files:

```bash
cd /path/to/sql/files
dispatch
```

Dispatch captures the launch-time current working directory once. CSV outputs are resolved relative to that launch directory for the whole session.

## 6. Post-install validation

From `/ads_storage/dispatch`:

```bash
python3.10 -m compileall dispatch scr
python3.10 -m dispatch --help
```

Then verify the installed shortcut and version marker:

```bash
which dispatch
cat /ads_storage/$USER/.dispatch/installed_version
cat /ads_storage/dispatch/VERSION
```

Then launch the TUI:

```bash
cd /path/to/sql/files
dispatch
```

At minimum, confirm:

- the dashboard renders
- the Kerberos indicator is visible
- `N` opens the New Job screen
- `H` opens History
- `B` opens Browser
- `Q` exits cleanly

## 7. Production validation harness

For repeatable real-environment validation over SSH and tmux, use the production harness:

- [tools/prod_tui/README.md](../tools/prod_tui/README.md)
- [docs/edge-node-smoke-test.md](./edge-node-smoke-test.md)

The harness is the right path when you want controlled remote validation rather than a one-off manual launch.

## Common mistakes

- Uploading only source code and forgetting `vendor/`. Offline dependency install will fail.
- Building a Dispatch app wheel unnecessarily. The current installer uses the uploaded repo checkout for the app itself.
- Running `dispatch` from the wrong directory. CSV outputs are tied to the launch-time working directory.
- Verifying `installed_version` under `~/.dispatch`. In this repo, the default install root is `/ads_storage/$USER/.dispatch`.
