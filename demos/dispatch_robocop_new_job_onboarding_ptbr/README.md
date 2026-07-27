# Onboarding video — New Job (pt-BR, silencioso)

Silent walkthrough of the **New Job** tab for first-time analysts.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Silent visual walkthrough |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized PT-BR captions |
| `dispatch_robocop_new_job_storyboard.md` | Scene map + verification evidence |
| `footer_timing_report.md` | Automated ≥15s footer timing PASS/FAIL |
| `dispatch_robocop_new_job_video_download.zip` | ZIP with the MP4 only |

No narration audio. No “Antes de começar” section.

## Pacing rule

Every instructional footer remains fully visible and static for **at least 15 seconds** before the next click or scene change.

## MonthlyJob SQL rule (verified)

The `.sql` file must contain both placeholders `{date_inicio}` and `{date_fim}`.

Evidence: `dispatch/sql.py`, `dispatch/screens/new_job.py`, `scr/monthly_query_processor.py`, `CONTEXT.md`, tests.

## Regenerate

```bash
source mocks/dev-env.sh
.venv/bin/pip install -r requirements.txt cairosvg pillow
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```
