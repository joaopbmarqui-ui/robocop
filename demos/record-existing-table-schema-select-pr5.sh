#!/usr/bin/env bash
# Reproduce the PR #5 demo: ExistingTable schema selection (before vs after).
#
# Outputs:
#   demos/existing-table-schema-select-pr5-demo.mp4   (if you record with a screen recorder)
#   demos/screenshots/pr5-before-existing-table.png
#   demos/screenshots/pr5-after-schema-radios.png
#
# Requirements: repo checkout on the feature branch, /workspace/.venv, mocks/dev-env.sh.
set -euo pipefail

REPO=/workspace
MAIN_WORKTREE=/tmp/dispatch-main-demo
VENV="$REPO/.venv/bin/python"
DEMO_DIR="$REPO/demos"

echo "=== PR #5 demo: ExistingTable schema selection ==="
echo

if [[ ! -x "$VENV" ]]; then
  echo "Missing venv at $VENV — run: python -m pip install -e \".[dev]\""
  exit 1
fi

if [[ ! -d "$MAIN_WORKTREE/mocks" ]]; then
  echo "Creating main-branch worktree for BEFORE state at $MAIN_WORKTREE"
  git -C "$REPO" worktree add "$MAIN_WORKTREE" main
fi

cat <<'SCRIPT'

Record your screen, then follow these steps in order.

----------------------------------------------------------------------
PART 1 — BEFORE (main branch, single combined field)
----------------------------------------------------------------------
Terminal commands:

  cd /tmp/dispatch-main-demo
  source mocks/dev-env.sh
  DISPATCH_EMAIL=demo@example.com /workspace/.venv/bin/python -m dispatch

In the TUI:
  1. Open "New Job" from the sidebar.
  2. Select Source → ExistingTable.
  3. Pause ~3s on the form.

Expected BEFORE UI:
  - One row labeled "Existing Table"
  - Placeholder: e.g. analytics.events_existing
  - User must type schema.table in that single field
  - No Schema radio buttons, no Custom Schema row

Quit dispatch (Back, then q).

----------------------------------------------------------------------
PART 2 — AFTER (feature branch, schema selector)
----------------------------------------------------------------------
Terminal commands:

  cd /workspace
  source mocks/dev-env.sh
  DISPATCH_EMAIL=demo@example.com /workspace/.venv/bin/python -m dispatch

In the TUI:
  1. Open "New Job".
  2. Select Source → ExistingTable (Destination auto-selects Csv).
  3. Pause ~3s — note new rows:
       Schema: [coe_enc] [aa_enc] [other]   (default aa_enc)
       Existing Table: table name only
  4. Select coe_enc → Custom Schema row stays hidden.
  5. Select other → Custom Schema row appears.
  6. Fill Custom Schema: analytics
  7. Fill Existing Table: events_existing
  8. Pause ~3s — validation should show "Ready to launch".

Quit dispatch.

----------------------------------------------------------------------
OPTIONAL — prefilled shortcut for AFTER deep-dive
----------------------------------------------------------------------
  cd /workspace
  source mocks/dev-env.sh
  DISPATCH_EMAIL=demo@example.com \
    DISPATCH_TEST_PREFILL=/workspace/demos/prefill-existing-table-other.json \
    /workspace/.venv/bin/python -m dispatch

Opens with other + analytics + events_existing already set. Toggle
coe_enc / aa_enc / other to show custom schema hide/show behavior.

----------------------------------------------------------------------
Save recording as:
  demos/existing-table-schema-select-pr5-demo.mp4
----------------------------------------------------------------------

SCRIPT

# Extract reference stills from the committed demo video when present.
if command -v ffmpeg >/dev/null && [[ -f "$DEMO_DIR/existing-table-schema-select-pr5-demo.mp4" ]]; then
  mkdir -p "$DEMO_DIR/screenshots"
  ffmpeg -y -loglevel error -ss 40 -i "$DEMO_DIR/existing-table-schema-select-pr5-demo.mp4" \
    -frames:v 1 "$DEMO_DIR/screenshots/pr5-before-existing-table.png"
  ffmpeg -y -loglevel error -ss 85 -i "$DEMO_DIR/existing-table-schema-select-pr5-demo.mp4" \
    -frames:v 1 "$DEMO_DIR/screenshots/pr5-after-schema-radios.png"
  echo "Reference screenshots refreshed under demos/screenshots/"
fi

echo
echo "Canonical demo video (already recorded): $DEMO_DIR/existing-table-schema-select-pr5-demo.mp4"
echo "Prefill fixture: $DEMO_DIR/prefill-existing-table-other.json"
