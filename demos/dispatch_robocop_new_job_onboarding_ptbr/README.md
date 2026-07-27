# Onboarding video — New Job (pt-BR)

Final package for first-time analysts learning the **New Job** tab.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Final video with PT-BR narration and burned-in captions |
| `dispatch_robocop_new_job_narration_ptbr.txt` | Full narration script with timestamps |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized Portuguese captions |
| `dispatch_robocop_new_job_storyboard.md` | Section → screen → narration → highlight map |

## How the footage is produced

Frames are screenshots of the **real** Dispatch Textual application from this
repository (`dispatch.app.DispatchApp` → Overview startup → `n` → `NewJobScreen`),
not a hand-drawn or HTML recreation. Capture uses Textual’s Pilot harness and
`save_screenshot`, the same compositor that renders the live TUI.

Kerberos / Impala / SMTP use `mocks/` so the recording stays offline and safe.
The video shows Launch confirmation and the in-app `Launched Job` message; it
does **not** treat a mock Impala `SUCCEEDED` state as production evidence.

## Environment note (textual==8.2.5)

`textual==8.2.5` is the correct pin (`requirements.txt` and `pyproject.toml`,
ADR-0002). Cloud/agent installs that run:

```bash
pip install --no-index --find-links=/workspace/vendor -r requirements.txt
```

fail when `/workspace/vendor` is missing (no wheels shipped in a clean clone).
That is an offline-bundle gap, not a wrong version. Fix for local/Cloud work:

```bash
/workspace/.venv/bin/pip install -r /workspace/requirements.txt
```

Do not change the pin unless the Release Operator updates the Edge vendor bundle.

## Regenerate

```bash
source mocks/dev-env.sh
/workspace/.venv/bin/pip install -r requirements.txt cairosvg pillow edge-tts
/workspace/.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
```

Requires system `ffmpeg` on `PATH`.
