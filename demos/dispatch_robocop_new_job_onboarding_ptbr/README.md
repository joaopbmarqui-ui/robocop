# Onboarding video — New Job (pt-BR, silencioso)

Silent walkthrough of the **New Job** tab for first-time analysts.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Silent visual walkthrough |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized PT-BR captions |
| `dispatch_robocop_new_job_storyboard.md` | Scene map + spotlight + timing |
| `footer_timing_report.md` | Automated exactly-8s timing PASS/FAIL |
| `dispatch_robocop_new_job_video_download.zip` | ZIP with the MP4 only |

No narration audio. No “Antes de começar” section.

## Pacing

Every instructional scene lasts **exactly 8.0 seconds**, including the typewriter animation (~1.0–1.5s) and static reading time.

## Visual design

- **Dialogue box:** white retro box in the lower quarter, thin black border, rounded corners, black pixel-style font, red downward arrow after typing completes.
- **Spotlight:** semi-transparent dark overlay (~66%) with a bright cutout on the explained element.

## MonthlyJob SQL rule (verified)

The `.sql` file must contain both placeholders `{date_inicio}` and `{date_fim}`.

## Regenerate

```bash
source mocks/dev-env.sh
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```
