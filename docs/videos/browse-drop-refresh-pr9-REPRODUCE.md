# Browse DROP auto-refresh demo (PR #9)

Demonstrates that the Browse tab removes dropped tables from the visible list
immediately after a successful DROP, without pressing **Load Tables [S]**.

## Generated assets

| File | Purpose |
|------|---------|
| `docs/videos/browse-drop-refresh-pr9.mp4` | Primary demo video (~12s) |
| `docs/videos/browse-drop-refresh-pr9.gif` | Animated GIF for PR embed |
| `docs/videos/browse-drop-refresh-pr9/*.svg` | Individual frame captures |

## Regenerate the video

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/python tools/demo_browser_drop_refresh.py
```

Requires `ffmpeg` on `PATH` (used to convert SVG frames to MP4/GIF).

## What the demo shows

1. **Before** — Browse auto-loads two mock tables (`dispatch_result`, `dispatch_monthly_fulljoin`); footer shows `2 tables`.
2. **Confirm** — User presses Drop and types `aa_enc.dispatch_result` in the danger modal.
3. **After** — List refreshes automatically: only `dispatch_monthly_fulljoin` remains, footer shows `1 tables`, detail pane shows `Table dropped`. No manual reload.

## Manual capture (interactive TUI)

If you prefer a live terminal recording instead of the scripted capture:

```bash
source mocks/dev-env.sh
DISPATCH_MOCK_SCENARIO=happy_path /workspace/.venv/bin/python -m dispatch
```

1. Sidebar → **Browse metadata**
2. Confirm two tables are listed and count reads `2 tables`
3. Select `dispatch_result`, press **D** (Drop)
4. Type `aa_enc.dispatch_result` and confirm
5. Observe the list updates to one table without pressing **S** (Load Tables)

Expected after step 5:

- `dispatch_result` is gone from the table list
- Count reads `1 tables`
- Detail pane shows the drop success message

## PR embed snippet

```markdown
<video src="docs/videos/browse-drop-refresh-pr9.mp4" controls width="900"></video>
```

Or for the GIF:

```markdown
![Browse DROP auto-refresh demo](docs/videos/browse-drop-refresh-pr9.gif)
```
