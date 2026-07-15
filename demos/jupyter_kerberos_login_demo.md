# Jupyter Kerberos login demo (PR #10)

Reproducible steps to capture the same end-to-end demo shown in
`docs/videos/pr-10-jupyter-kerberos-login-demo.mp4`.

## Automated (recommended)

From the repo root, on branch `cursor/jupyter-kerberos-login-3d04` or later:

```bash
/workspace/.venv/bin/pip install cairosvg pillow
/workspace/.venv/bin/python demos/generate_jupyter_kerberos_login_demo.py
```

Output: `docs/videos/pr-10-jupyter-kerberos-login-demo.mp4`

## Manual terminal walkthrough

### 1. Before — non-Jupyter, no Kerberos ticket

```bash
cd /path/to/robocop
source mocks/dev-env.sh
export DISPATCH_JUPYTER_MODE=0
export DISPATCH_MOCK_KLIST_TTL=0
rm -f "$DISPATCH_MOCK_STATE_DIR/klist_ttl"
mkdir -p "$DISPATCH_DATA_ROOT/.dispatch"
echo '{"to_email":"demo@example.com"}' > "$DISPATCH_DATA_ROOT/.dispatch/config.json"
echo '1.1.0' > "$DISPATCH_DATA_ROOT/.dispatch/installed_version"
/workspace/.venv/bin/python -m dispatch
```

**Expected:** Dashboard opens immediately. Kerberos status shows **missing** (no login modal).

Press `q` to quit.

### 2. After — Jupyter mode, no ticket → login modal

```bash
source mocks/dev-env.sh
export DISPATCH_JUPYTER_MODE=1
export DISPATCH_MOCK_KLIST_TTL=0
rm -f "$DISPATCH_MOCK_STATE_DIR/klist_ttl"
/workspace/.venv/bin/python -m dispatch
```

**Expected:** Kerberos **sign-in modal** appears first with:

- Login field placeholder: `EID`
- Password field placeholder: `Windows password`

### 3. Failed authentication (optional)

```bash
export DISPATCH_MOCK_SCENARIO=auth_error
```

Enter any EID/password and click **Sign in**.

**Expected:** Red error containing `Password incorrect`. Modal stays open for retry.

### 4. Successful authentication

```bash
export DISPATCH_MOCK_SCENARIO=happy_path
```

Enter EID `jdoe` and any non-empty password, then **Sign in**.

**Expected:** Modal closes, dashboard loads, Kerberos TTL shows a healthy value (e.g. `8h 00m`).

## What the video shows

| Segment | Mode | Behavior |
|---------|------|----------|
| Before | `DISPATCH_JUPYTER_MODE=0` | Dashboard without login gate |
| After | `DISPATCH_JUPYTER_MODE=1` | Login modal → credentials → dashboard |

`DISPATCH_JUPYTER_MODE=1` simulates Jupyter Notebook without needing a live kernel.
