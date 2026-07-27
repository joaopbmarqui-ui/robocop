# Onboarding video — New Job (pt-BR, silencioso, 1920×1080)

Silent walkthrough of the **New Job** tab for first-time analysts.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Silent visual walkthrough (1920×1080) |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized PT-BR captions |
| `dispatch_robocop_new_job_storyboard.md` | Scene map + spotlight geometry |
| `footer_timing_report.md` | Exactly-8s timing PASS/FAIL |
| `spotlight_report.md` / `spotlight_report.json` | Element spotlight review |
| `spotlight_contact_sheet.png` | Manual review contact sheet |
| `dispatch_robocop_new_job_video_download.zip` | ZIP with the MP4 only |

## Font

**Calibri is not available** in this Linux environment. The video uses **Carlito** (`fonts/Carlito-Regular.ttf`, `fonts/Carlito-Bold.ttf` from `fonts-crosextra-carlito`), the OFL metric-compatible Calibri substitute. Body text **38 px**, title **42 px** bold.

## Visual design

- Resolution **1920×1080**, H.264, yuv420p
- White lower-quarter dialogue box, thin black border, rounded corners
- Character-by-character typing (~1.0–1.5s) inside each **exact 8.0s** scene
- Red downward arrow after typing completes
- Real spotlight: dark overlay + tight cutouts from Textual widget bounding boxes

## MonthlyJob SQL rule (verified)

The `.sql` file must contain both placeholders `{date_inicio}` and `{date_fim}`.

## Regenerate

```bash
source mocks/dev-env.sh
sudo apt-get install -y fonts-crosextra-carlito   # if needed
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```
