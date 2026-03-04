"""Generate 24 musically coherent stems across 3 genre varieties.

Each variety has 8 stems covering 4 BPM zones (walk, jog, run, sprint).
All synthesis uses soundscape.dsp — pure numpy, no external synth libraries.

Varieties:
  A: "Neon Drive" (Synthwave) — A minor
  B: "Forest Trail" (Organic Ambient) — D major pentatonic
  C: "Midnight Pulse" (Dark Minimal Techno) — E minor Phrygian

Run: python generate_stems.py
"""

import json
import os

import numpy as np
import soundfile as sf

from soundscape.dsp import (
    SR, sine, saw, square, noise_white, noise_brown,
    fm_synth, fm_bell, fm_bass,
    adsr, exponential_decay, tremolo,
    lowpass, highpass, bandpass, resonant_lowpass,
    reverb_schroeder, chorus, detune,
    beat_duration, place_hits, render_pattern,
    crossfade_loop, normalize,
    note_freq, chord_freqs, scale_freqs,
)

BASE_BPM = 150
LOOP_BARS = 4
LOOP_BEATS = LOOP_BARS * 4  # 16 beats


def _loop_samples(bpm: float = BASE_BPM, beats: int = LOOP_BEATS) -> int:
    return beat_duration(bpm) * beats


# ==========================================================================
# A: "Neon Drive" (Synthwave) — A minor
# ==========================================================================

def neon_pad_low() -> np.ndarray:
    """Am chord, saw pad, chorus, lowpass. Warm low-end pad."""
    dur_s = _loop_samples() / SR
    freqs = chord_freqs('A2', 'minor')  # A2, C3, E3
    t = np.arange(int(SR * dur_s)) / SR
    out = np.zeros_like(t)
    for f in freqs:
        out += saw(f, dur_s) * 0.3
        out += saw(f * 1.003, dur_s) * 0.15  # detuned layer
    env = adsr(len(out), 1.5, 0.5, 0.8, 1.5)
    out = out * env
    out = lowpass(out, 600)
    out = chorus(out, rate=0.8, depth=0.004, mix=0.4)
    return crossfade_loop(normalize(out))


def neon_bass_walk() -> np.ndarray:
    """Half-note A2 bass, gentle FM pulse."""
    n = _loop_samples()
    half_note = beat_duration(BASE_BPM) * 2
    out = np.zeros(n)
    root = note_freq('A2')
    for i in range(LOOP_BEATS // 2):
        seg = fm_bass(root, half_note / SR)
        env = adsr(len(seg), 0.01, 0.1, 0.6, 0.3)
        seg = seg * env
        start = i * half_note
        end = min(start + len(seg), n)
        out[start:end] += seg[:end - start]
    out = lowpass(out, 400)
    return crossfade_loop(normalize(out))


def neon_pad_mid() -> np.ndarray:
    """Am7 voicing, bright pad with bandpass sweep."""
    dur_s = _loop_samples() / SR
    freqs = chord_freqs('A3', 'min7')  # A3, C4, E4, G4
    t = np.arange(int(SR * dur_s)) / SR
    out = np.zeros_like(t)
    for f in freqs:
        out += saw(f, dur_s) * 0.2
    env = adsr(len(out), 2.0, 0.5, 0.7, 2.0)
    out = out * env
    # Bandpass sweep via LFO-modulated filter
    sweep_freq = 800 + 400 * np.sin(2 * np.pi * 0.25 * t)
    # Apply bandpass at the average frequency
    out = bandpass(out, 900, q=1.5)
    out = chorus(out, rate=1.2, depth=0.003, mix=0.3)
    return crossfade_loop(normalize(out))


def neon_arp() -> np.ndarray:
    """16th-note arpeggio Am-C-Em-G, FM bell timbre."""
    n = _loop_samples()
    sixteenth = beat_duration(BASE_BPM) // 4
    # Am pentatonic arp: A3, C4, E4, G4 cycling
    arp_notes = [note_freq('A3'), note_freq('C4'),
                 note_freq('E4'), note_freq('G4')]
    out = np.zeros(n)
    total_steps = n // sixteenth
    for i in range(total_steps):
        freq = arp_notes[i % len(arp_notes)]
        seg = fm_bell(freq, sixteenth / SR)
        start = i * sixteenth
        end = min(start + len(seg), n)
        out[start:end] += seg[:end - start] * 0.6
    out = lowpass(out, 6000)
    return crossfade_loop(normalize(out))


def neon_kick() -> np.ndarray:
    """Four-on-the-floor kick with pitch sweep."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    # Synthesize one kick hit
    kick_len = min(bd, int(SR * 0.25))
    t = np.arange(kick_len) / SR
    env = np.exp(-t * 30)
    # Pitch sweep from 150 Hz down to 50 Hz
    freq_sweep = 50 + 100 * np.exp(-t * 40)
    phase = np.cumsum(2 * np.pi * freq_sweep / SR)
    hit = np.sin(phase) * env
    # Place four-on-the-floor
    hits = place_hits(LOOP_BEATS, subdivisions=1, bpm=BASE_BPM)
    out = render_pattern(hits, hit, n)
    return crossfade_loop(normalize(out))


def neon_hihat() -> np.ndarray:
    """16th-note hi-hat with accents and swing."""
    n = _loop_samples()
    sixteenth_samp = beat_duration(BASE_BPM) // 4
    # Synthesize one hat hit
    hat_len = min(sixteenth_samp, int(SR * 0.04))
    t = np.arange(hat_len) / SR
    noise = np.random.randn(hat_len)
    noise = highpass(noise, 6000)
    env = np.exp(-t * 100)
    hit = noise * env

    # Pattern with accents: downbeat=1.0, offbeat=0.5
    pattern = [True] * 16
    hits = place_hits(LOOP_BEATS, subdivisions=4, pattern=pattern,
                      swing=0.1, bpm=BASE_BPM)
    # Apply accent pattern
    accented_hits = []
    for i, (pos, vel) in enumerate(hits):
        accent = 1.0 if i % 4 == 0 else (0.7 if i % 2 == 0 else 0.4)
        accented_hits.append((pos, accent))
    out = render_pattern(accented_hits, hit, n)
    return crossfade_loop(normalize(out))


def neon_bass_drive() -> np.ndarray:
    """8th-note driving bass, resonant LP, A2-E2-G2 pattern."""
    n = _loop_samples()
    eighth = beat_duration(BASE_BPM) // 2
    notes = [note_freq('A2'), note_freq('A2'),
             note_freq('E2'), note_freq('E2'),
             note_freq('G2'), note_freq('G2'),
             note_freq('A2'), note_freq('A2')]
    out = np.zeros(n)
    total_eighths = n // eighth
    for i in range(total_eighths):
        freq = notes[i % len(notes)]
        seg_len = min(eighth, int(SR * 0.3))
        seg = saw(freq, seg_len / SR)
        env = adsr(len(seg), 0.005, 0.05, 0.7, 0.05)
        seg = seg * env
        start = i * eighth
        end = min(start + len(seg), n)
        out[start:end] += seg[:end - start]
    out = resonant_lowpass(out, 800, q=3.0)
    return crossfade_loop(normalize(out))


def neon_lead() -> np.ndarray:
    """Chord stabs on beats 2+4, Am-Em-F-G progression."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    chords = [
        chord_freqs('A3', 'minor'),  # bar 1
        chord_freqs('E3', 'minor'),  # bar 2
        chord_freqs('F3', 'major'),  # bar 3
        chord_freqs('G3', 'major'),  # bar 4
    ]
    out = np.zeros(n)
    for bar in range(4):
        for beat_offset in [1, 3]:  # beats 2 and 4 (0-indexed: 1, 3)
            stab_len = min(bd, int(SR * 0.2))
            t_stab = np.arange(stab_len) / SR
            stab = np.zeros(stab_len)
            for freq in chords[bar]:
                stab += saw(freq, stab_len / SR) * 0.25
            env = np.exp(-t_stab * 10)
            stab = stab * env
            pos = (bar * 4 + beat_offset) * bd
            end = min(pos + stab_len, n)
            out[pos:end] += stab[:end - pos]
    out = lowpass(out, 4000)
    out = reverb_schroeder(out, mix=0.2)
    return crossfade_loop(normalize(out))


# ==========================================================================
# B: "Forest Trail" (Organic Ambient) — D major pentatonic
# ==========================================================================

def forest_texture() -> np.ndarray:
    """Nature bed: shaped noise + random droplet pings."""
    n = _loop_samples()
    t = np.arange(n) / SR
    # Base rain-like noise
    rain = noise_brown(n / SR) * 0.4
    rain = lowpass(rain, 2000)
    # Random droplet pings
    np.random.seed(12)
    for _ in range(30):
        pos = np.random.randint(0, n - SR // 10)
        length = min(SR // 15, n - pos)
        dt = np.arange(length) / SR
        freq = np.random.uniform(2000, 6000)
        ping = np.sin(2 * np.pi * freq * dt) * np.exp(-dt * 60) * 0.3
        rain[pos:pos + length] += ping
    return crossfade_loop(normalize(rain))


def forest_drone() -> np.ndarray:
    """Sub drone on D2, slow vibrato."""
    n = _loop_samples()
    t = np.arange(n) / SR
    freq = note_freq('D2')
    vibrato = 1 + 0.005 * np.sin(2 * np.pi * 0.3 * t)
    out = sine(1.0, n / SR)  # placeholder
    phase = np.cumsum(2 * np.pi * freq * vibrato / SR)
    out = np.sin(phase)
    env = adsr(n, 2.0, 1.0, 0.8, 2.0)
    out = out * env * 0.7
    out = lowpass(out, 200)
    return crossfade_loop(normalize(out))


def forest_pad() -> np.ndarray:
    """Breathy pad, Dmaj7, bandpass LFO."""
    dur_s = _loop_samples() / SR
    freqs = chord_freqs('D3', 'maj7')  # D3, F#3, A3, C#4
    t = np.arange(int(SR * dur_s)) / SR
    out = np.zeros_like(t)
    for f in freqs:
        # Breathy: noise-modulated sine
        mod = noise_white(dur_s) * 0.1
        mod = lowpass(mod, 10)
        out += np.sin(2 * np.pi * f * t + mod) * 0.25
    env = adsr(len(out), 2.0, 0.5, 0.7, 2.0)
    out = out * env
    out = bandpass(out, 600, q=0.8)
    return crossfade_loop(normalize(out))


def forest_marimba() -> np.ndarray:
    """Pentatonic melody, FM wood timbre."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    scale = scale_freqs('D3', 'pentatonic_major', octaves=2)
    np.random.seed(7)
    out = np.zeros(n)
    # Place notes on beats with some variation
    for beat in range(LOOP_BEATS):
        if np.random.random() < 0.5:
            continue
        freq = np.random.choice(scale)
        note_len = min(bd, int(SR * 0.3))
        # FM wood: high ratio, quick decay
        t_note = np.arange(note_len) / SR
        mod_idx = 4.0 * np.exp(-t_note * 15)
        mod = mod_idx * np.sin(2 * np.pi * freq * 3.2 * t_note)
        carrier = np.sin(2 * np.pi * freq * t_note + mod)
        env = np.exp(-t_note * 8)
        note_sig = carrier * env * 0.6
        pos = beat * bd
        end = min(pos + note_len, n)
        out[pos:end] += note_sig[:end - pos]
    return crossfade_loop(normalize(out))


def forest_clicks() -> np.ndarray:
    """Woodblock percussion on beats 1+3 with swing."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    # Woodblock: short resonant tone
    click_len = int(SR * 0.02)
    t = np.arange(click_len) / SR
    click = np.sin(2 * np.pi * 800 * t) * np.exp(-t * 200)
    # Place on beats 1 and 3
    pattern = [True, False, True, False]
    hits = place_hits(LOOP_BEATS, subdivisions=1,
                      pattern=pattern, swing=0.05, bpm=BASE_BPM)
    out = render_pattern(hits, click, n)
    return crossfade_loop(normalize(out))


def forest_bass() -> np.ndarray:
    """Warm walking bass: D2-A2-B2-F#2 pattern."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    notes = [note_freq('D2'), note_freq('A2'),
             note_freq('B2'), note_freq('F#2')]
    out = np.zeros(n)
    for beat in range(LOOP_BEATS):
        freq = notes[beat % len(notes)]
        note_len = min(bd, int(SR * 0.4))
        seg = sine(freq, note_len / SR)
        # Add warmth with a bit of harmonics
        seg += sine(freq * 2, note_len / SR) * 0.2
        env = adsr(len(seg), 0.01, 0.1, 0.6, 0.1)
        seg = seg * env
        pos = beat * bd
        end = min(pos + len(seg), n)
        out[pos:end] += seg[:end - pos]
    out = lowpass(out, 500)
    return crossfade_loop(normalize(out))


def forest_shaker() -> np.ndarray:
    """16th-note shaker, highpass noise."""
    n = _loop_samples()
    sixteenth = beat_duration(BASE_BPM) // 4
    # Shaker hit
    shaker_len = min(sixteenth, int(SR * 0.03))
    noise = np.random.randn(shaker_len)
    noise = highpass(noise, 8000)
    env = exponential_decay(shaker_len, 80)
    hit = noise * env

    hits = place_hits(LOOP_BEATS, subdivisions=4, swing=0.08, bpm=BASE_BPM)
    # Accent pattern
    accented = []
    for i, (pos, vel) in enumerate(hits):
        accent = 1.0 if i % 4 == 0 else 0.5
        accented.append((pos, accent))
    out = render_pattern(accented, hit, n)
    return crossfade_loop(normalize(out))


def forest_bells() -> np.ndarray:
    """Sparse pentatonic FM bells."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    scale = scale_freqs('D4', 'pentatonic_major', octaves=2)
    np.random.seed(21)
    out = np.zeros(n)
    # Sparse: only ~6 notes across the loop
    positions = sorted(np.random.choice(LOOP_BEATS, size=6, replace=False))
    for beat in positions:
        freq = np.random.choice(scale)
        bell = fm_bell(freq, min(bd * 2 / SR, 1.0))
        pos = beat * bd
        end = min(pos + len(bell), n)
        out[pos:end] += bell[:end - pos] * 0.5
    return crossfade_loop(normalize(out))


# ==========================================================================
# C: "Midnight Pulse" (Dark Minimal Techno) — E minor Phrygian
# ==========================================================================

def midnight_drone() -> np.ndarray:
    """Dark drone: E2 sine + detuned saw, LFO tremolo."""
    n = _loop_samples()
    t = np.arange(n) / SR
    freq = note_freq('E2')
    out = sine(freq, n / SR) * 0.5
    out += saw(freq * 1.005, n / SR) * 0.3  # detuned
    env = adsr(n, 2.0, 1.0, 0.8, 2.0)
    trem = tremolo(n, 0.2, depth=0.3)
    out = out * env * trem
    out = lowpass(out, 300)
    return crossfade_loop(normalize(out))


def midnight_texture() -> np.ndarray:
    """Industrial texture: bandpass-swept noise, metallic."""
    n = _loop_samples()
    t = np.arange(n) / SR
    noise = noise_white(n / SR)
    # Bandpass sweep
    sweep_center = 2000 + 1500 * np.sin(2 * np.pi * 0.15 * t)
    # Apply multiple bandpass passes at slightly different frequencies
    out = bandpass(noise, 2000, q=3.0) * 0.5
    out += bandpass(noise, 3500, q=2.0) * 0.3
    env = adsr(n, 1.0, 0.5, 0.6, 1.0)
    out = out * env
    return crossfade_loop(normalize(out))


def midnight_sub() -> np.ndarray:
    """Sub bass: half-note E2, FM grit."""
    n = _loop_samples()
    half_note = beat_duration(BASE_BPM) * 2
    freq = note_freq('E2')
    out = np.zeros(n)
    for i in range(LOOP_BEATS // 2):
        seg = fm_bass(freq, half_note / SR)
        env = adsr(len(seg), 0.01, 0.15, 0.7, 0.2)
        seg = seg * env
        start = i * half_note
        end = min(start + len(seg), n)
        out[start:end] += seg[:end - start]
    out = lowpass(out, 250)
    return crossfade_loop(normalize(out))


def midnight_kick() -> np.ndarray:
    """Deep kick: 4-on-floor, long pitch sweep."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    # Deep kick with long sweep
    kick_len = min(bd, int(SR * 0.35))
    t = np.arange(kick_len) / SR
    env = np.exp(-t * 20)
    freq_sweep = 45 + 120 * np.exp(-t * 25)
    phase = np.cumsum(2 * np.pi * freq_sweep / SR)
    hit = np.sin(phase) * env
    # Add sub thump
    hit += sine(45, kick_len / SR) * np.exp(-t * 15) * 0.5
    hits = place_hits(LOOP_BEATS, subdivisions=1, bpm=BASE_BPM)
    out = render_pattern(hits, hit, n)
    return crossfade_loop(normalize(out))


def midnight_hat() -> np.ndarray:
    """Metallic hat: ring-mod noise with swing."""
    n = _loop_samples()
    sixteenth = beat_duration(BASE_BPM) // 4
    hat_len = min(sixteenth, int(SR * 0.03))
    t = np.arange(hat_len) / SR
    noise = np.random.randn(hat_len)
    # Ring modulation for metallic quality
    ring = np.sin(2 * np.pi * 7500 * t)
    hat = noise * ring * np.exp(-t * 120)
    hat = highpass(hat, 5000)

    hits = place_hits(LOOP_BEATS, subdivisions=4, swing=0.15, bpm=BASE_BPM)
    accented = []
    for i, (pos, vel) in enumerate(hits):
        accent = 1.0 if i % 4 == 0 else (0.6 if i % 2 == 0 else 0.3)
        accented.append((pos, accent))
    out = render_pattern(accented, hat, n)
    return crossfade_loop(normalize(out))


def midnight_acid() -> np.ndarray:
    """Acid bass: saw + resonant LP sweep, E-F-G-B pattern."""
    n = _loop_samples()
    eighth = beat_duration(BASE_BPM) // 2
    notes = [note_freq('E2'), note_freq('F2'),
             note_freq('G2'), note_freq('B2')]
    out = np.zeros(n)
    total_eighths = n // eighth
    for i in range(total_eighths):
        freq = notes[i % len(notes)]
        seg_len = min(eighth, int(SR * 0.25))
        seg = saw(freq, seg_len / SR)
        env = adsr(len(seg), 0.005, 0.05, 0.5, 0.05)
        seg = seg * env
        start = i * eighth
        end = min(start + len(seg), n)
        out[start:end] += seg[:end - start]
    # Acid resonant filter sweep
    out = resonant_lowpass(out, 1200, q=6.0)
    return crossfade_loop(normalize(out))


def midnight_stab() -> np.ndarray:
    """Chord stabs: Em/F triads, syncopated."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    chords = [
        chord_freqs('E3', 'minor'),
        chord_freqs('F3', 'major'),
        chord_freqs('E3', 'minor'),
        chord_freqs('F3', 'major'),
    ]
    out = np.zeros(n)
    # Syncopated: hit on beat 1, the "and" of 2, beat 4
    stab_beats = [0, 1.5, 3]
    for bar in range(4):
        for sb in stab_beats:
            stab_len = min(bd // 2, int(SR * 0.15))
            stab = np.zeros(stab_len)
            for freq in chords[bar]:
                stab += saw(freq, stab_len / SR) * 0.2
            t_stab = np.arange(stab_len) / SR
            env = np.exp(-t_stab * 15)
            stab = stab * env
            pos = int((bar * 4 + sb) * bd)
            end = min(pos + stab_len, n)
            if pos < n:
                out[pos:end] += stab[:end - pos]
    out = lowpass(out, 3000)
    out = reverb_schroeder(out, mix=0.15)
    return crossfade_loop(normalize(out))


def midnight_clap() -> np.ndarray:
    """Clap on beats 2+4: bandpass noise."""
    n = _loop_samples()
    bd = beat_duration(BASE_BPM)
    # Clap: layered noise bursts
    clap_len = int(SR * 0.06)
    t = np.arange(clap_len) / SR
    clap = np.zeros(clap_len)
    for offset in [0, 0.003, 0.007, 0.012]:
        start = int(offset * SR)
        end = min(start + int(SR * 0.02), clap_len)
        seg_len = end - start
        noise = np.random.randn(seg_len)
        env = np.exp(-np.arange(seg_len) / SR * 100)
        clap[start:end] += noise * env * 0.5
    clap = bandpass(clap, 1500, q=1.0)

    # Beats 2 and 4
    pattern = [False, True, False, True]
    hits = place_hits(LOOP_BEATS, subdivisions=1,
                      pattern=pattern, bpm=BASE_BPM)
    out = render_pattern(hits, clap, n)
    return crossfade_loop(normalize(out))


# ==========================================================================
# Registry and output
# ==========================================================================

STEMS = {
    'neon': [
        ('neon_pad_low', neon_pad_low, 95, 145, 10, 10, 0.50),
        ('neon_bass_walk', neon_bass_walk, 100, 140, 8, 8, 0.55),
        ('neon_pad_mid', neon_pad_mid, 125, 170, 10, 10, 0.45),
        ('neon_arp', neon_arp, 130, 180, 8, 8, 0.40),
        ('neon_kick', neon_kick, 140, 200, 8, 5, 0.60),
        ('neon_hihat', neon_hihat, 145, 200, 8, 5, 0.30),
        ('neon_bass_drive', neon_bass_drive, 150, 200, 10, 5, 0.50),
        ('neon_lead', neon_lead, 160, 200, 10, 5, 0.35),
    ],
    'forest': [
        ('forest_texture', forest_texture, 95, 160, 10, 15, 0.30),
        ('forest_drone', forest_drone, 95, 150, 10, 10, 0.40),
        ('forest_pad', forest_pad, 120, 170, 10, 10, 0.45),
        ('forest_marimba', forest_marimba, 125, 175, 8, 8, 0.40),
        ('forest_clicks', forest_clicks, 135, 185, 8, 8, 0.25),
        ('forest_bass', forest_bass, 140, 195, 10, 8, 0.50),
        ('forest_shaker', forest_shaker, 150, 200, 8, 5, 0.25),
        ('forest_bells', forest_bells, 155, 200, 10, 5, 0.35),
    ],
    'midnight': [
        ('midnight_drone', midnight_drone, 95, 145, 12, 10, 0.40),
        ('midnight_texture', midnight_texture, 100, 155, 10, 10, 0.30),
        ('midnight_sub', midnight_sub, 120, 170, 8, 8, 0.55),
        ('midnight_kick', midnight_kick, 130, 200, 10, 5, 0.65),
        ('midnight_hat', midnight_hat, 135, 200, 8, 5, 0.28),
        ('midnight_acid', midnight_acid, 145, 200, 10, 5, 0.45),
        ('midnight_stab', midnight_stab, 155, 200, 10, 5, 0.35),
        ('midnight_clap', midnight_clap, 160, 200, 10, 5, 0.30),
    ],
}

# Map stem names to generator functions for test access
GENERATORS = {}
for variety_stems in STEMS.values():
    for name, func, *_ in variety_stems:
        GENERATORS[name] = func


def generate_all() -> dict:
    """Generate all 24 stems, return {name: np.ndarray}."""
    results = {}
    for variety_stems in STEMS.values():
        for name, func, *_ in variety_stems:
            results[name] = func()
    return results


def main():
    """Generate WAV files + JSON configs."""
    base_dir = os.path.join(os.path.dirname(__file__), 'stems')

    for variety, variety_stems in STEMS.items():
        variety_dir = os.path.join(base_dir, variety)
        os.makedirs(variety_dir, exist_ok=True)

        config = {
            'baseBPM': BASE_BPM,
            'stems': [],
        }

        for name, func, bpm_low, bpm_high, fade_in, fade_out, volume in variety_stems:
            print(f'  Generating {name}...')
            audio = func()
            wav_name = f'{name}.wav'
            wav_path = os.path.join(variety_dir, wav_name)
            sf.write(wav_path, audio.astype(np.float32), SR)
            print(f'    {wav_name}  ({len(audio)/SR:.1f}s)')

            config['stems'].append({
                'file': wav_name,
                'bpmRange': [bpm_low, bpm_high],
                'fadeIn': fade_in,
                'fadeOut': fade_out,
                'volume': volume,
            })

        json_path = os.path.join(variety_dir, f'{variety}_mix.json')
        with open(json_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f'  Config: {json_path}')

    print(f'\nDone — stems written to {base_dir}/')


if __name__ == '__main__':
    print('Generating stems...')
    main()
