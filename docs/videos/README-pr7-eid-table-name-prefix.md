# PR #7 demo: EID-prefixed table names in New Job

This folder contains a short end-to-end demo of the EID table name prefix feature.

## Video asset

| File | Description |
|---|---|
| [`pr7-eid-table-name-prefix-demo.mp4`](./pr7-eid-table-name-prefix-demo.mp4) | ~15s walkthrough: before slide → Csv-only contrast → Table flow with fixed `EID_` prefix, suffix edit, paste normalization, ready state |

Embed in the PR description:

```markdown
https://github.com/joaopbmarqui-ui/robocop/assets/...  <!-- upload via GitHub UI -->
```

Or reference the committed file path after merge:

```markdown
[Demo video](docs/videos/pr7-eid-table-name-prefix-demo.mp4)
```

## Regenerate the video

```bash
/workspace/.venv/bin/python -m pip install cairosvg pillow
/workspace/.venv/bin/python docs/videos/record_eid_table_name_prefix_demo.py
```

Outputs:

- `docs/videos/pr7-eid-table-name-prefix-demo.mp4`
- `docs/videos/frames-pr7-eid-table-name-prefix/*.png` (intermediate frames)

## Manual reproduction (live TUI)

Run these commands from the repo root to capture the same behavior interactively:

```bash
source mocks/dev-env.sh
export DISPATCH_EMAIL=demo@example.com
export DISPATCH_MOCK_SCENARIO=happy_path
mkdir -p /tmp/dispatch-demo && cd /tmp/dispatch-demo
printf '%s\n' 'SELECT 1;' > query.sql
DISPATCH_MOCK_SCENARIO=happy_path /workspace/.venv/bin/python -m dispatch
```

In the TUI:

1. Open **New Job** from the sidebar.
2. Leave **Source = SqlFile** and set **Destination = Csv**.
   - **Expected:** the **Table Name** row is hidden (Csv-only is not table creation).
3. Set **Destination = Table**.
   - **Expected:** **Table Name** shows a fixed `$(whoami)_` prefix label and an editable suffix field (default `dispatch_result`).
   - **Expected full name:** `$(whoami)_dispatch_result` (e.g. `ubuntu_dispatch_result`).
4. Tab to the suffix field and change it to `monthly_export`.
   - **Expected:** launch/validation use `$(whoami)_monthly_export`.
5. Paste `$(whoami)_cloned_job` into the suffix field.
   - **Expected:** the field normalizes to `cloned_job`; full name remains `$(whoami)_cloned_job`.
6. Confirm the footer validation line shows **Ready to launch** when other fields are valid.

### Quick automated check (no video)

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/python -m pytest tests/test_eid_table_name.py -q
```

## What the demo shows

| Step | What you should see |
|---|---|
| Before slide | Single editable table name with no EID enforcement |
| Csv-only | Table Name row hidden |
| Table destination | Fixed `EID_` prefix + suffix input |
| Suffix edit | Only the suffix changes; prefix stays fixed |
| Paste full name | Prefix stripped from editable field |
| Ready state | Validation summary passes with enforced `EID_suffix` |
