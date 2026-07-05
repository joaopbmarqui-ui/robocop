# PR #4 demo — Browse table search clarity

Short before/after recording of the Browse tab query row improvement:

- **Before:** shared caption `Schema · table filter` with unlabeled inputs
- **After:** `Table name` label, inline hint `type firstword* and load`, typed `dispatch*` filter, and loaded tables

## Generate the video

```bash
source mocks/dev-env.sh
./demos/pr4-browse-table-search-clarity/run_demo.sh
```

Or:

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/python demos/pr4-browse-table-search-clarity/capture_demo.py
```

## Outputs

| File | Purpose |
|------|---------|
| `docs/videos/pr4-browse-table-search-clarity.mp4` | PR embed (primary) |
| `docs/videos/pr4-browse-table-search-clarity.gif` | Lightweight PR embed |
| `demos/pr4-browse-table-search-clarity/frames/*.png` | Individual PNG frames |

Requires `ffmpeg` on `PATH`.
