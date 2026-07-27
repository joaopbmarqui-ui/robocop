# Onboarding video — New Job (pt-BR, 1920×1080)

Silent visual walkthrough of the **New Job** tab with original chiptune bed and
UI dialogue cues. Top-to-bottom form order. Typing + exactly **5.0s** complete-text hold.

## Deliverables

| File | Description |
|------|-------------|
| `dispatch_robocop_new_job_onboarding_ptbr.mp4` | Final video (1920×1080, H.264 + AAC) |
| `dispatch_robocop_new_job_captions_ptbr.srt` | Synchronized PT-BR captions |
| `dispatch_robocop_new_job_storyboard.md` | Scene map, timing, spotlights, audio cues |
| `footer_timing_report.md` | Typing + 5.0s hold PASS/FAIL |
| `spotlight_report.md` / `.json` | Element spotlight review |
| `spotlight_contact_sheet.png` | Manual review contact sheet |
| `dispatch_robocop_new_job_video_download.zip` | ZIP with the MP4 only |
| `audio/original/` | Original BGM + dialogue cue + license |

## Font

**Calibri is not available** in this Linux environment. The video uses **Carlito**
(`fonts/Carlito-Regular.ttf`, `fonts/Carlito-Bold.ttf` from `fonts-crosextra-carlito`),
the OFL metric-compatible Calibri substitute. Body **38 px**, title **42 px** bold.
Dialogue padding ≥ 64×40 px. No “Opcional” badges; “Obrigatório” kept where verified.

## Audio (original — not Pokémon-derived)

| Asset | Path | Status |
|-------|------|--------|
| Background music | `audio/original/town_walk_original_chiptune.wav` | Original generated chiptune (NumPy oscillators, seed `20260727`, BPM 96, G-centered). Calm welcoming bed. **Not** Pallet Town / Pokémon. |
| Dialogue cue | `audio/original/dialogue_open_ui_blip.wav` | Original soft two-tone UI blip (~0.14s). Plays once when each dialogue card opens. |
| License note | `audio/original/AUDIO_LICENSE.json` | Generation evidence + license statement |

Mix:

- BGM level ≈ 0.18
- SFX level ≈ 0.55
- Duck via `sidechaincompress` (fade down ≈ 0.12s, fade up ≈ 0.35s)
- No narration / no voice

## Timing

- Character typing: 1.0–1.5 s (not counted in the hold)
- Complete text visible: **exactly 5.0 s**
- Red arrow only after typing completes
- Related cards (“O que é” / “O que você decide aqui” / “Efeito”) keep the **same spotlight group**

## Content order (top → bottom)

1. Opening
2. Source → Destination (first configuration elements)
3. Detected / Matrix (near-top aids)
4. Execution Queue
5. SQL File (+ Destination relationship, when reached visually)
6. Email / Subject
7. MonthlyJob (Table + SQL rule + Start/End Date in form)
8. ExistingTable (positive remaining fields only)
9. Status → Preview → Launch → Confirm → Overview

## MonthlyJob SQL rule (verified)

The `.sql` file must contain both placeholders `{date_inicio}` and `{date_fim}`.

## Regenerate

```bash
# Optional: recreate original audio assets (only if missing, or to rebuild)
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_original_audio.py

source mocks/dev-env.sh
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py
# or reuse captures:
.venv/bin/python demos/dispatch_robocop_new_job_onboarding_ptbr/generate_onboarding_video.py --compose-only
```
