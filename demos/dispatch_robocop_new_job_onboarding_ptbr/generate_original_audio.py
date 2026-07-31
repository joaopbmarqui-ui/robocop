#!/usr/bin/env python3
"""Generate original (non-Pokémon) chiptune BGM + dialogue UI blip for the onboarding video.

Evidence: NumPy square/triangle oscillators, seed 20260727, BPM 96, G-centered.
Not derived from Nintendo / Game Freak / Pokémon audio.
"""
from __future__ import annotations

import json
import math
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "audio" / "original"
BGM = OUT / "town_walk_original_chiptune.wav"
SFX = OUT / "dialogue_open_ui_blip.wav"
LICENSE = OUT / "AUDIO_LICENSE.json"

SR = 44100
SEED = 20260727
BPM = 96


def _adsr(n: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    ea, ed, er = int(a * n), int(d * n), int(r * n)
    es = max(0, n - ea - ed - er)
    env = np.concatenate([
        np.linspace(0.0, 1.0, max(1, ea), endpoint=False),
        np.linspace(1.0, s, max(1, ed), endpoint=False),
        np.full(max(1, es), s, dtype=np.float64),
        np.linspace(s, 0.0, max(1, er)),
    ])
    if len(env) < n:
        env = np.pad(env, (0, n - len(env)))
    return env[:n]


def _square(freq: float, n: int, vol: float = 0.2) -> np.ndarray:
    t = np.arange(n) / SR
    return vol * np.sign(np.sin(2 * math.pi * freq * t))


def _triangle(freq: float, n: int, vol: float = 0.12) -> np.ndarray:
    t = np.arange(n) / SR
    return vol * (2 / math.pi) * np.arcsin(np.sin(2 * math.pi * freq * t))


def _note_hz(degree: int, octave: int = 4) -> float:
    # G major-ish degrees: G A B C D E F# → MIDI-ish from G3
    semis = [0, 2, 4, 5, 7, 9, 11][degree % 7] + 12 * (degree // 7)
    base = 196.0 * (2 ** octave) / 8  # G3≈196 when octave=3 → use octave param
    # Fix: G4 = 392 Hz as root for octave=4
    g4 = 392.0
    return g4 * (2 ** ((semis + 12 * (octave - 4)) / 12.0))


def write_bgm() -> float:
    rng = np.random.default_rng(SEED)
    beat = 60.0 / BPM
    bars = 16
    beats_per_bar = 4
    total_s = bars * beats_per_bar * beat
    n = int(total_s * SR)
    mix = np.zeros(n, dtype=np.float64)

    # Soft looping melody (original phrase; not a known game theme)
    melody = [0, 2, 4, 2, 5, 4, 2, 0, 4, 5, 7, 5, 4, 2, 0, -2]
    harmony = [0, 0, 4, 4, 5, 5, 4, 2]
    bass = [0, 0, 5, 5, 3, 3, 4, 4]

    t = 0.0
    for bar in range(bars):
        for bi in range(beats_per_bar):
            start = int(t * SR)
            dur = beat * (0.85 if bi % 2 == 0 else 0.55)
            nn = max(1, int(dur * SR))
            deg = melody[(bar * beats_per_bar + bi) % len(melody)]
            lead = _square(_note_hz(deg, 4), nn, 0.11) * _adsr(nn, 0.05, 0.15, 0.55, 0.25)
            hdeg = harmony[(bar * 2 + bi // 2) % len(harmony)]
            harm = _triangle(_note_hz(hdeg, 3), nn, 0.07) * _adsr(nn, 0.08, 0.2, 0.45, 0.3)
            bdeg = bass[(bar * 2 + bi // 2) % len(bass)]
            bas = _triangle(_note_hz(bdeg, 2), nn, 0.09) * _adsr(nn, 0.02, 0.1, 0.5, 0.2)
            # light pulse on beat 1/3
            click_n = max(1, int(0.04 * SR))
            pulse = np.zeros(nn)
            if bi in (0, 2):
                pulse[:click_n] = _square(980.0, click_n, 0.03) * _adsr(click_n, 0.01, 0.3, 0.2, 0.5)
            chunk = lead + harm + bas + pulse
            end = min(n, start + len(chunk))
            mix[start:end] += chunk[: end - start]
            t += beat

    # gentle high shimmer (non-melodic noise bed)
    shimmer = 0.008 * rng.standard_normal(n)
    mix += shimmer
    peak = np.max(np.abs(mix)) or 1.0
    mix = 0.85 * mix / peak
    _write_wav(BGM, mix)
    return total_s


def write_sfx() -> float:
    # Soft two-tone UI blip (~0.14s)
    dur = 0.14
    n = int(dur * SR)
    t = np.arange(n) / SR
    f1, f2 = 660.0, 880.0
    tone = 0.35 * (
        np.sign(np.sin(2 * math.pi * f1 * t)) * (t < 0.07)
        + np.sign(np.sin(2 * math.pi * f2 * t)) * (t >= 0.07)
    )
    tone *= _adsr(n, 0.02, 0.15, 0.4, 0.45)
    _write_wav(SFX, tone)
    return dur


def _write_wav(path: Path, samples: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(samples, -1.0, 1.0)
    data = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    bgm_s = write_bgm()
    sfx_s = write_sfx()
    meta = {
        "bgm_file": "audio/original/town_walk_original_chiptune.wav",
        "sfx_file": "audio/original/dialogue_open_ui_blip.wav",
        "license": (
            "Original work created for this onboarding package. "
            "All rights granted for use in this repository. "
            "Not derived from Nintendo/Game Freak/Pokémon works."
        ),
        "generation": (
            f"Synthesized with NumPy (square/triangle oscillators + ADSR). "
            f"Seed={SEED}. BPM={BPM}. Key center=G."
        ),
        "bgm_duration_s": bgm_s,
        "sfx_duration_s": sfx_s,
        "generator": "generate_original_audio.py",
        "note": "Deliberately avoids recognizable Pallet Town / Pokémon melodic phrases.",
    }
    LICENSE.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {BGM} ({bgm_s:.2f}s)")
    print(f"Wrote {SFX} ({sfx_s:.2f}s)")
    print(f"Wrote {LICENSE}")


if __name__ == "__main__":
    main()
