# Manual demo: New Job email placeholder (PR #6)

Reproduce the before/after email placeholder change in a live terminal session.

## Prerequisites

```bash
cd /workspace
source mocks/dev-env.sh
unset DISPATCH_EMAIL
/workspace/.venv/bin/python -c "from dispatch import config; config.save_form_defaults({})"
```

Clearing `DISPATCH_EMAIL` and saved form defaults ensures the **placeholder** is visible (not a pre-filled value).

## Before state (reference)

On `main` before this PR, the placeholder was:

```text
user@example.com
```

## After state (this branch)

```text
name.surname@mastercard.com,name2.surname2@mastercard.com
```

## Steps

1. Launch Dispatch:

   ```bash
   DISPATCH_MOCK_SCENARIO=happy_path /workspace/.venv/bin/python -m dispatch
   ```

2. Open **New Job** from the sidebar (or press the bound navigation key).

3. Scroll to **Email (notifications)** when the field is empty.

4. Confirm the dim placeholder text shows the comma-separated Mastercard examples.

5. Switch **Source** options and verify the email placeholder stays the same:

   - `SqlFile` → any legal destination
   - `SqlTemplate` → `Table`
   - `ExistingTable` → `Csv`

6. Optional: tab into the email field, type a valid address, and confirm existing validation still works (green ✓ in the inline status row).

## Automated video generation

From the repo root:

```bash
/workspace/.venv/bin/pip install cairosvg pillow
/workspace/.venv/bin/python demos/record_email_placeholder_demo.py
```

Output: `demos/email-placeholder-new-job-demo.mp4`
