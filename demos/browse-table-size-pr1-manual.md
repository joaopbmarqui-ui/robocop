# Browse table size column — manual demo script (PR #1)

Reproduce the same end-to-end demo locally if you prefer to record your own
terminal session or regenerate the bundled assets.

## Prerequisites

```bash
cd /path/to/robocop
source mocks/dev-env.sh
python3 -m pip install -e .
python3 -m pip install cairosvg   # only needed for the automated recorder
```

## Automated recorder (recommended)

Generates an MP4, GIF, and PNG frames under `docs/videos/` and `demos/frames/`:

```bash
source mocks/dev-env.sh
python3 demos/browse-table-size-pr1-demo.py
```

Expected output files:

| File | Purpose |
|------|---------|
| `docs/videos/browse-table-size-pr1-demo.mp4` | PR-ready screen recording |
| `docs/videos/browse-table-size-pr1-demo.gif` | Lightweight animated preview |
| `demos/frames/browse-table-size-pr1-*.png` | Individual annotated frames |

## Manual terminal walkthrough

Use this if you want to capture a live `asciinema` or screen recording yourself.

### 1. Start Dispatch with mocks

```bash
source mocks/dev-env.sh
DISPATCH_MOCK_SCENARIO=happy_path python3 -m dispatch
```

### 2. Open Browse

| Step | Input | Expected result |
|------|-------|-----------------|
| 1 | Press `B` on Dashboard | Browse screen opens |
| 2 | Wait ~1s (auto-load) | Table list shows **Name · Type · Size** columns |
| 3 | Observe sort line | `Sorted by: name ↑` above the table |
| 4 | Observe sizes | `dispatch_result` ≈ `12.6 MB`, `dispatch_monthly_fulljoin` ≈ `370.4 MB` |

### 3. Sort by size

| Step | Input | Expected result |
|------|-------|-----------------|
| 5 | Press `O` | Sort indicator changes to `Sorted by: size ↑` |
| 6 | Observe row order | Largest table (`dispatch_monthly_fulljoin`) moves to the top |

### 4. Describe still works

| Step | Input | Expected result |
|------|-------|-----------------|
| 7 | Press `Enter` on a row | Right pane shows column schema for the selected table |

### Before vs after (what changed)

| Before (pre-PR) | After (this PR) |
|-----------------|-----------------|
| Columns: `Name`, `Type` only | Columns: `Name`, `Type`, **`Size`** |
| No size metadata | Sizes fetched via `SHOW TABLE STATS` |
| No size sorting | Press **`O`** to cycle `name → size` sort |

## Attach to the GitHub PR

Embed the MP4 directly in the PR description:

```markdown
https://github.com/<owner>/<repo>/blob/<branch>/docs/videos/browse-table-size-pr1-demo.mp4
```

Or upload `docs/videos/browse-table-size-pr1-demo.mp4` as a PR attachment and drag it into the description field.
