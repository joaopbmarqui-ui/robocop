# Onboarding video — New Job (pt-BR, silencioso)

Silent walkthrough of the **New Job** tab for first-time analysts.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Silent visual walkthrough |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized PT-BR captions |
| `dispatch_robocop_new_job_storyboard.md` | Scene map + spotlight + timing |
| `footer_timing_report.md` | Automated 10–12s timing PASS/FAIL |
| `dispatch_robocop_new_job_video_download.zip` | ZIP with the MP4 only |

No narration audio. No “Antes de começar” section.

## Pacing rule

Each instructional scene lasts **exactly 10 seconds** (or **up to 12 seconds** only for longer messages). That total includes:

1. Fast character-by-character footer reveal (~1.5–2s, ≤25% of the scene)
2. Static reading time with the complete message
3. Stable spotlight on the explained interface element

No click, cursor move, or UI change during the instructional period.

## Visual focus

The rest of the UI is dimmed while the current field/option stays bright in a spotlight cutout. The cursor remains visible but is not the only indicator.

## MonthlyJob SQL rule (verified)

The `.sql` file must contain both placeholders `{date_inicio}` and `{date_fim}`.

Evidence: `dispatch/sql.py`, `dispatch/screens/new_job.py`, `scr/monthly_query_processor.py`, `CONTEXT.md`, tests.

## Regenerate

```bash
source mocks/dev-env.sh
.venv/bin/pip install -r requirements.txt cairosvg pillow
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```
