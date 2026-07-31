# Onboarding video — Overview (pt-BR, 1920×1080)

Part 2 of the Dispatch (Robocop) onboarding series. Same production standards as
the New Job video: Carlito dialogue, typing + **5.0s** complete-text hold,
element spotlights, original chiptune BGM, dialogue-open UI blip with ducking.

## Deliverables

| File | Description |
|------|-------------|
| `overview_onboarding_ptbr.mp4` | Final video (1920×1080, H.264 + AAC) |
| `overview_onboarding_ptbr_captions_ptbr.srt` | Synchronized PT-BR captions |
| `overview_onboarding_ptbr_storyboard.md` | Scene map, timing, spotlights, audio cues |
| `footer_timing_report.md` | Typing + 5.0s hold PASS/FAIL |
| `spotlight_report.md` / `.json` | Element spotlight review |
| `spotlight_contact_sheet.png` | Manual review contact sheet |
| `overview_onboarding_video_download.zip` | ZIP with the MP4 only |
| `audio/original/` | Same original BGM + dialogue cue + license |

## Font

**Calibri is not available** in this Linux environment. The video uses **Carlito**
(`fonts/Carlito-Regular.ttf`, `fonts/Carlito-Bold.ttf`), the OFL metric-compatible
Calibri substitute. Body **38 px**, title **42 px** bold. Dialogue padding ≥ 64×40 px.

## Audio (original — not Pokémon-derived)

Reuses the New Job series assets (identical mood and ducking):

| Asset | Path | Status |
|-------|------|--------|
| Background music | `audio/original/town_walk_original_chiptune.wav` | Original generated chiptune (NumPy, seed `20260727`, BPM 96). |
| Dialogue cue | `audio/original/dialogue_open_ui_blip.wav` | Original soft two-tone UI blip. |
| License note | `audio/original/AUDIO_LICENSE.json` | Generation evidence |

Mix: BGM ≈ 0.18, SFX ≈ 0.55, duck ≈ 0.06, fade down 0.12s / up 0.35s. No narration.

## Timing

- Character typing: 1.0–1.5 s (not counted in the hold)
- Complete text visible: **exactly 5.0 s**
- Red arrow only after typing completes
- Related cards keep the **same spotlight group**

## Spotlights (geometry-driven)

Every instructional spotlight is built from **captured Textual runtime geometry**,
not screen percentages:

- Widget `region` / `content_region` for controls
- `DataTable._get_column_region` / `_get_cell_region` for table columns and State cells
- Status-strip metric spans from the strip’s rendered plain text

Related cards that explain the same element reuse the **identical** spotlight
coordinates. See `spotlight_accuracy_report.md`.

## Content order (top → bottom)

1. Opening / what Overview is
2. Status strip (KERBEROS with kinit recovery, RUNNING, FINISHED 7D, FAILED 7D)
3. Jobs title (running first · last 7 days of history)
4. Empty list guidance
5. Jobs table + columns (ID, Source, Destination, State, Elapsed)
6. Status meanings (PENDING, RUNNING, SUCCEEDED, FAILED, CANCELLED)
7. Filter (`/`) and example
8. Detail pane (title + log preview)
9. Actions (events, New Job, View Logs, Cancel)
10. Closing summary (no “Next Step”)

Sidebar navigation is visible but not explained.

## Regenerate

```bash
# Optional: recreate original audio assets
.venv/bin/python demos/dispatch_robocop_overview_onboarding_ptbr/generate_original_audio.py

source mocks/dev-env.sh
.venv/bin/python demos/dispatch_robocop_overview_onboarding_ptbr/generate_onboarding_video.py
# or reuse captures:
.venv/bin/python demos/dispatch_robocop_overview_onboarding_ptbr/generate_onboarding_video.py --compose-only
```
