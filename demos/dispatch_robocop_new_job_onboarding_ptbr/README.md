# Onboarding video — New Job (pt-BR)

Final package for first-time analysts learning the **New Job** tab.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Final video with PT-BR narration and burned-in captions |
| `dispatch_robocop_new_job_narration_ptbr.txt` | Full narration script with timestamps |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized Portuguese captions |
| `dispatch_robocop_new_job_storyboard.md` | Section → screen → narration → highlight map |

## Regenerate

Requires `.venv` with `requirements.txt` plus `cairosvg`, `pillow`, `edge-tts`, and system `ffmpeg`.

```bash
/workspace/.venv/bin/pip install -r requirements.txt cairosvg pillow edge-tts
/workspace/.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```

The generator drives the real Textual New Job UI under mocks (no production data),
records SVG screenshots, synthesizes `pt-BR-FranciscaNeural` narration, and muxes the MP4.
