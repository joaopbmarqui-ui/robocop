# PR #2 demo — ExistingTable schema selector

Animated walkthrough of the New Job **ExistingTable** schema selection control
(`coe_enc`, `aa_enc`, `other`).

## Quick path (automated GIF)

```bash
cd /path/to/robocop
source mocks/dev-env.sh
python3 -m pip install -e ".[dev]" cairosvg pillow
python3 docs/videos/record_pr2_existing_table_schema_demo.py
```

**Output file to attach in the PR:**

```text
docs/videos/pr2-existing-table-schema-demo.gif
```

Individual captioned frames are also written under:

```text
docs/videos/pr2-existing-table-schema-demo/frames/
```

## Manual interactive demo (SSH / local terminal)

Use this when you want a live screen recording instead of the generated GIF.

```bash
source mocks/dev-env.sh
DISPATCH_MOCK_SCENARIO=happy_path python3 -m dispatch
```

| Step | Action | What to show |
|------|--------|--------------|
| 1 | Open **New Job** (`N` or sidebar) | Default **SqlFile** source — no schema selector row |
| 2 | Select **ExistingTable** under Source | New **Schema** row appears with `coe_enc`, `aa_enc`, `other` |
| 3 | Leave **aa_enc** selected, type `dispatch_smoke_seed` in **Existing Table** | Manual Schema row stays hidden |
| 4 | Select **coe_enc** | Schema row still hidden; only table name needed |
| 5 | Select **other** | Manual **Schema** input appears — type e.g. `analytics` |
| 6 | Confirm footer shows validation state | Launch would use `analytics.events_existing` (or chosen preset) |

### Expected behavior checkpoints

- `#row-existing-schema` visible only when **ExistingTable** is selected
- `#row-schema` hidden for `coe_enc` / `aa_enc`, visible for `other`
- Validation summary reaches **Ready to launch** when Kerberos is healthy and table name is valid

## Demo script frames (automated)

The recorder captures five captioned frames:

1. **Before** — SqlFile, no ExistingTable controls
2. **ExistingTable** — schema selector visible (`aa_enc` default)
3. **coe_enc** — preset schema, manual field hidden
4. **other** — custom schema `analytics` + table `events_existing`
5. **aa_enc** — preset with `dispatch_smoke_seed`
