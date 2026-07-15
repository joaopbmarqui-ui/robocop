# PR #8 demo — Browse bulk table deletion

Automated capture of the bulk-drop improvement for [PR #8](https://github.com/joaopbmarqui-ui/robocop/pull/8).

## Attach to the PR

Embed either asset in the PR description:

```markdown
https://github.com/joaopbmarqui-ui/robocop/blob/cursor/bulk-table-deletion-browse-74c3/docs/videos/pr8-bulk-table-deletion/bulk-table-deletion-demo.mp4
```

Or the GIF (smaller, autoplays in GitHub):

```markdown
![Bulk table deletion demo](docs/videos/pr8-bulk-table-deletion/bulk-table-deletion-demo.gif)
```

## Generated files

| File | Purpose |
|------|---------|
| `bulk-table-deletion-demo.mp4` | ~18s screen recording (7 captioned frames) |
| `bulk-table-deletion-demo.gif` | Same flow as animated GIF |
| `frames/*.png` | Individual captioned screenshots |
| `../capture_pr8_bulk_drop_demo.py` | Regenerate script |

## Regenerate

```bash
/workspace/.venv/bin/pip install cairosvg pillow  # once, if missing
/workspace/.venv/bin/python docs/videos/capture_pr8_bulk_drop_demo.py
```

Requires `ffmpeg` on PATH.

## What the demo shows

1. **Before** — tables loaded; Drop disabled with no checked rows
2. **Space** — toggle one table; Drop enables
3. **Select All [A]** — all visible tables checked
4. **Drop [D]** — confirmation modal lists checked tables; button disabled
5. **Type `I AM SURE`** — first confirmation step
6. **Type `DROP`** — confirm button enables
7. **After** — three tables dropped; only checked rows were affected

## Manual live demo (optional)

If you prefer recording your own terminal session:

```bash
source mocks/dev-env.sh
DISPATCH_MOCK_SCENARIO=happy_path /workspace/.venv/bin/python -m dispatch
```

1. Press **B** (Browse) from the dashboard
2. Press **S** to load tables
3. Move with **j/k**, press **Space** to check rows (or **A** for Select All)
4. Press **D** — modal lists checked tables
5. Type `I AM SURE`, then `DROP`, confirm
6. Table list refreshes; dropped tables disappear

Expected: Drop stays disabled until at least one row is checked; only checked tables are dropped.
