# Onboarding video — New Job (pt-BR, silencioso)

Silent screen-recording-style walkthrough of the **New Job** tab for first-time analysts.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Silent visual walkthrough (PT-BR on-screen text, no voice/music) |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Same explanations synchronized as captions |
| `dispatch_robocop_new_job_storyboard.md` | Step map |
| `dispatch_robocop_new_job_video_download.zip` | ZIP containing only the MP4 |

There is **no** narration audio file.

## How footage is produced

Frames come from the real Dispatch Textual UI (`DispatchApp` → Overview → `n` → `NewJobScreen`).
Overlays add cursor movement, click indicators, field highlights, and Portuguese callouts.
Audio is a silent track only (playable, no voice, no music).

## Regenerate

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/pip install -r requirements.txt cairosvg pillow
/workspace/.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```

Requires system `ffmpeg`.
