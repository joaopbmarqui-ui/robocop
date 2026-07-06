# PR #11 demo — MonthlyJob label rename

Short end-to-end demo of renaming the **SqlTemplate** source option to **MonthlyJob**
in the New Job flow (PR #11).

## Quick run (generates MP4)

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/python demos/pr11-monthlyjob-label/generate_demo.py
```

**Output video:** `demos/pr11-monthlyjob-label/monthlyjob-label-pr11-demo.mp4`

Intermediate SVG/PNG frames land in `demos/pr11-monthlyjob-label/frames/`.

## What the video shows

| Segment | Content |
|---------|---------|
| Title | Before PR #11 |
| Matrix | Source × Destination matrix row labeled **SqlTemplate** |
| Selected | SqlTemplate radio + hint “SqlTemplate supports Table only” + picker **Detected** column |
| Preview | SQL Preview header `SqlTemplate → Table` |
| Title | After PR #11 |
| Matrix | Same matrix with **MonthlyJob** row |
| Selected | MonthlyJob radio + hint + picker |
| Preview | SQL Preview header `MonthlyJob → Table` |

Internal manifest/orchestrator type remains `SqlTemplate`; only user-facing labels change.

## Manual interactive capture (optional)

If you prefer a live terminal recording:

```bash
source mocks/dev-env.sh
cd /tmp
cat > monthly_revenue.sql <<'SQL'
SELECT region, SUM(amount) AS total
FROM sales
WHERE sale_date BETWEEN '{date_inicio}' AND '{date_fim}'
GROUP BY region
SQL
DISPATCH_MOCK_SCENARIO=happy_path /workspace/.venv/bin/python -m dispatch
```

Then in the TUI:

1. Press **N** (New Job).
2. Press **M** to expand the Source × Destination matrix — confirm **MonthlyJob** row.
3. Select **MonthlyJob** — confirm hint “MonthlyJob supports Table only”.
4. Pick `monthly_revenue.sql` in the file picker — **Detected** shows **MonthlyJob**.
5. Press **P** — preview header shows `MonthlyJob → Table`.

To compare with **main** (before), checkout `main`, repeat the same steps, and note **SqlTemplate** everywhere above.

## Requirements

- Python venv at `/workspace/.venv` (or `pip install -e ".[dev]"`)
- `ffmpeg` on `PATH` (used for PNG conversion and MP4 mux)
- `source mocks/dev-env.sh` before running (mock Kerberos / Impala)
