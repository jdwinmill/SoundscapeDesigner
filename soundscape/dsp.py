"""Pure-numpy DSP utility module for stem synthesis.

All functions operate on numpy arrays — no external synth libraries.
"""

import numpy as np

SR = 44100  # Default sample rate


# ---------------------------------------------------------------------------
# Oscillators
# ---------------------------------------------------------------------------

def sine(freq: float, duration: float, sr: int = SR, phase: float = 0.0) -> np.ndarray:
    """Pure sine wave."""
    t = np.arange(int(sr * duration)) / sr
    return np.sin(2 * np.pi * freq * t + phase)


def saw(freq: float, duration: float, sr: int = SR) -> np.ndarray:
    """Band-limited sawtooth via additive synthesis (8 harmonics)."""
    t = np.arange(int(sr * duration)) / sr
    out = np.zeros_like(t)
    for k in range(1, 9):
        if k * freq > sr / 2:
            break
        out += ((-1) ** (k + 1)) * np.sin(2 * np.pi * k * freq * t) / k
    return out * (2 / np.pi)


def square(freq: float, duration: float, sr: int = SR) -> np.ndarray:
    """Band-limited square via additive synthesis (odd harmonics)."""
    t = np.arange(int(sr * duration)) / sr
    out = np.zeros_like(t)
    for k in range(1, 16, 2):
        if k * freq > sr / 2:
            break
        out += np.sin(2 * np.pi * k * freq * t) / k
    return out * (4 / np.pi)


def noise_white(duration: float, sr: int = SR) -> np.ndarray:
    """White noise."""
    return np.random.randn(int(sr * duration))


def noise_brown(duration: float, sr: int = SR) -> np.ndarray:
    """Brown noise (integrated white noise, detrended)."""
    n = int(sr * duration)
    white = np.random.randn(n) * 0.02
    brown = np.cumsum(white)
    brown -= np.linspace(brown[0], brown[-1], n)
    peak = np.max(np.abs(brown))
    if peak > 0:
        brown /= peak
    return brown


# ---------------------------------------------------------------------------
# FM Synthesis
# ---------------------------------------------------------------------------

def fm_synth(carrier_freq: float, mod_freq: float, mod_index: float,
             duration: float, sr: int = SR) -> np.ndarray:
    """Basic FM synthesis: carrier modulated by a single modulator."""
    t = np.arange(int(sr * duration)) / sr
    modulator = mod_index * np.sin(2 * np.pi * mod_freq * t)
    return np.sin(2 * np.pi * carrier_freq * t + modulator)


def fm_bell(freq: float, duration: float, sr: int = SR) -> np.ndarray:
    """Bell-like FM timbre: inharmonic ratio with fast decay."""
    t = np.arange(int(sr * duration)) / sr
    mod_freq = freq * 2.76
    mod_index = 5.0 * np.exp(-t * 4)
    modulator = mod_index * np.sin(2 * np.pi * mod_freq * t)
    carrier = np.sin(2 * np.pi * freq * t + modulator)
    env = np.exp(-t * 3)
    return carrier * env


def fm_bass(freq: float, duration: float, sr: int = SR) -> np.ndarray:
    """Gritty FM bass: low ratio, moderate index."""
    t = np.arange(int(sr * duration)) / sr
    mod_freq = freq * 1.0
    mod_index = 3.0 + 2.0 * np.exp(-t * 6)
    modulator = mod_index * np.sin(2 * np.pi * mod_freq * t)
    carrier = np.sin(2 * np.pi * freq * t + modulator)
    env = np.exp(-t * 2)
    return carrier * env


# ---------------------------------------------------------------------------
# Envelopes
# ---------------------------------------------------------------------------

def adsr(n_samples: int, attack: float, decay: float, sustain: float,
         release: float, sr: int = SR) -> np.ndarray:
    """ADSR envelope. Times in seconds, sustain is a level (0-1)."""
    a_samp = int(attack * sr)
    d_samp = int(decay * sr)
    r_samp = int(release * sr)
    s_samp = max(0, n_samples - a_samp - d_samp - r_samp)

    attack_seg = np.linspace(0, 1, a_samp) if a_samp > 0 else np.array([])
    decay_seg = np.linspace(1, sustain, d_samp) if d_samp > 0 else np.array([])
    sustain_seg = np.full(s_samp, sustain) if s_samp > 0 else np.array([])
    release_seg = np.linspace(sustain, 0, r_samp) if r_samp > 0 else np.array([])

    env = np.concatenate([attack_seg, decay_seg, sustain_seg, release_seg])
    # Pad or trim to exact length
    if len(env) < n_samples:
        env = np.concatenate([env, np.zeros(n_samples - len(env))])
    return env[:n_samples]


def exponential_decay(n_samples: int, rate: float, sr: int = SR) -> np.ndarray:
    """Exponential decay envelope: exp(-rate * t)."""
    t = np.arange(n_samples) / sr
    return np.exp(-rate * t)


def tremolo(n_samples: int, rate: float, depth: float = 0.5,
            sr: int = SR) -> np.ndarray:
    """Tremolo (amplitude modulation). depth=0 means no effect, depth=1 full."""
    t = np.arange(n_samples) / sr
    return 1.0 - depth * 0.5 * (1 - np.cos(2 * np.pi * rate * t))


# ---------------------------------------------------------------------------
# Biquad IIR Filters (Audio EQ Cookbook, Direct Form II Transposed)
# ---------------------------------------------------------------------------

def biquad_coeffs(filter_type: str, freq: float, sr: int = SR,
                  q: float = 0.707) -> tuple:
    """Compute biquad filter coefficients (b0,b1,b2,a0,a1,a2).

    filter_type: 'lowpass', 'highpass', 'bandpass'
    """
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * q)
    cos_w0 = np.cos(w0)

    if filter_type == 'lowpass':
        b0 = (1 - cos_w0) / 2
        b1 = 1 - cos_w0
        b2 = (1 - cos_w0) / 2
        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha
    elif filter_type == 'highpass':
        b0 = (1 + cos_w0) / 2
        b1 = -(1 + cos_w0)
        b2 = (1 + cos_w0) / 2
        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha
    elif filter_type == 'bandpass':
        b0 = alpha
        b1 = 0
        b2 = -alpha
        a0 = 1 + alpha
        a1 = -2 * cos_w0
        a2 = 1 - alpha
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")

    return (b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)


def biquad_apply(signal: np.ndarray, coeffs: tuple) -> np.ndarray:
    """Apply biquad filter using Direct Form II Transposed."""
    b0, b1, b2, a1, a2 = coeffs
    n = len(signal)
    out = np.zeros(n)
    z1 = 0.0
    z2 = 0.0

    for i in range(n):
        x = signal[i]
        y = b0 * x + z1
        z1 = b1 * x - a1 * y + z2
        z2 = b2 * x - a2 * y
        out[i] = y

    return out


def lowpass(signal: np.ndarray, freq: float, sr: int = SR,
            q: float = 0.707) -> np.ndarray:
    """Apply lowpass biquad filter."""
    coeffs = biquad_coeffs('lowpass', freq, sr, q)
    return biquad_apply(signal, coeffs)


def highpass(signal: np.ndarray, freq: float, sr: int = SR,
             q: float = 0.707) -> np.ndarray:
    """Apply highpass biquad filter."""
    coeffs = biquad_coeffs('highpass', freq, sr, q)
    return biquad_apply(signal, coeffs)


def bandpass(signal: np.ndarray, freq: float, sr: int = SR,
             q: float = 1.0) -> np.ndarray:
    """Apply bandpass biquad filter."""
    coeffs = biquad_coeffs('bandpass', freq, sr, q)
    return biquad_apply(signal, coeffs)


def resonant_lowpass(signal: np.ndarray, freq: float, sr: int = SR,
                     q: float = 5.0) -> np.ndarray:
    """Lowpass with high resonance (acid-style)."""
    return lowpass(signal, freq, sr, q)


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------

def _comb_filter(signal: np.ndarray, delay_samples: int,
                 feedback: float) -> np.ndarray:
    """Feedback comb filter for reverb."""
    out = np.zeros(len(signal))
    for i in range(len(signal)):
        if i >= delay_samples:
            out[i] = signal[i] + feedback * out[i - delay_samples]
        else:
            out[i] = signal[i]
    return out


def _allpass_filter(signal: np.ndarray, delay_samples: int,
                    gain: float) -> np.ndarray:
    """Schroeder allpass filter."""
    n = len(signal)
    buf = np.zeros(n)
    out = np.zeros(n)
    for i in range(n):
        if i >= delay_samples:
            buf[i] = signal[i] + gain * buf[i - delay_samples]
            out[i] = -gain * buf[i] + buf[i - delay_samples]
        else:
            buf[i] = signal[i]
            out[i] = -gain * buf[i]
    return out


def reverb_schroeder(signal: np.ndarray, sr: int = SR, mix: float = 0.3,
                     room_size: float = 1.0) -> np.ndarray:
    """Schroeder reverb: 4 parallel comb filters + 2 series allpass filters."""
    comb_delays = [int(d * room_size) for d in [1557, 1617, 1491, 1422]]
    comb_gains = [0.84, 0.82, 0.80, 0.78]
    allpass_delays = [int(d * room_size) for d in [225, 556]]
    allpass_gain = 0.5

    wet = np.zeros(len(signal))
    for delay, gain in zip(comb_delays, comb_gains):
        wet += _comb_filter(signal, delay, gain)
    wet /= len(comb_delays)

    for delay in allpass_delays:
        wet = _allpass_filter(wet, delay, allpass_gain)

    return signal * (1 - mix) + wet * mix


def chorus(signal: np.ndarray, sr: int = SR, rate: float = 1.5,
           depth: float = 0.003, mix: float = 0.5) -> np.ndarray:
    """Simple chorus effect using modulated delay."""
    n = len(signal)
    t = np.arange(n) / sr
    mod = depth * sr * (1 + np.sin(2 * np.pi * rate * t)) / 2
    base_delay = int(0.01 * sr)  # 10ms base delay

    out = np.zeros(n)
    for i in range(n):
        delay_idx = i - base_delay - mod[i]
        if delay_idx < 0:
            out[i] = signal[i]
        else:
            idx_int = int(delay_idx)
            frac = delay_idx - idx_int
            if idx_int + 1 < n:
                out[i] = signal[idx_int] * (1 - frac) + signal[idx_int + 1] * frac
            elif idx_int < n:
                out[i] = signal[idx_int]

    return signal * (1 - mix) + out * mix


def detune(signal: np.ndarray, cents: float = 10.0,
           sr: int = SR) -> np.ndarray:
    """Detune by resampling at a slightly different rate, then mix."""
    ratio = 2 ** (cents / 1200)
    n = len(signal)
    new_indices = np.arange(n) * ratio
    valid = new_indices < n - 1
    out = np.zeros(n)
    idx_int = new_indices[valid].astype(int)
    frac = new_indices[valid] - idx_int
    out[valid] = signal[idx_int] * (1 - frac) + signal[idx_int + 1] * frac
    return (signal + out) * 0.5


# ---------------------------------------------------------------------------
# Rhythm
# ---------------------------------------------------------------------------

def beat_duration(bpm: float, sr: int = SR) -> int:
    """Samples per beat at given BPM."""
    return int(sr * 60 / bpm)


def place_hits(n_beats: int, subdivisions: int = 1, pattern: list = None,
               swing: float = 0.0, bpm: float = 150, sr: int = SR) -> list:
    """Return sample positions for rhythmic hits.

    Args:
        n_beats: number of beats
        subdivisions: hits per beat (1=quarter, 2=eighth, 4=sixteenth)
        pattern: optional bool list — which subdivisions get hits
        swing: 0.0=straight, 0.5=heavy shuffle (delays even subdivisions)
        bpm: tempo
        sr: sample rate

    Returns:
        List of (sample_position, velocity) tuples.
    """
    beat_samp = beat_duration(bpm, sr)
    sub_samp = beat_samp / subdivisions
    total_subs = n_beats * subdivisions

    if pattern is None:
        pattern = [True] * total_subs
    else:
        # Tile pattern to fill total_subs
        pattern = (pattern * ((total_subs // len(pattern)) + 1))[:total_subs]

    hits = []
    for i in range(total_subs):
        if not pattern[i]:
            continue
        pos = i * sub_samp
        # Apply swing to even-numbered subdivisions (0-indexed: 1, 3, 5, ...)
        if i % 2 == 1 and swing > 0:
            pos += sub_samp * swing
        hits.append((int(pos), 1.0))

    return hits


def render_pattern(hit_positions: list, hit_signal: np.ndarray,
                   total_samples: int) -> np.ndarray:
    """Place a hit sound at given positions into a buffer.

    Args:
        hit_positions: list of (sample_pos, velocity) tuples
        hit_signal: the one-shot sample to place
        total_samples: length of output buffer

    Returns:
        Mixed output array.
    """
    out = np.zeros(total_samples)
    hit_len = len(hit_signal)
    for pos, vel in hit_positions:
        end = min(pos + hit_len, total_samples)
        length = end - pos
        if length > 0 and pos >= 0:
            out[pos:end] += hit_signal[:length] * vel
    return out


# ---------------------------------------------------------------------------
# Loop utilities
# ---------------------------------------------------------------------------

def crossfade_loop(signal: np.ndarray, crossfade_samples: int = 2048) -> np.ndarray:
    """Crossfade the end into the beginning for seamless looping.

    Trims the signal by crossfade_samples, then blends the tail into the start
    so the loop boundary is smooth.
    """
    n = len(signal)
    if crossfade_samples >= n // 2:
        crossfade_samples = n // 4
    if crossfade_samples < 1:
        return signal.copy()

    # Take the body without the last crossfade_samples
    body = signal[:n - crossfade_samples].copy()
    tail = signal[n - crossfade_samples:]

    fade_in = np.linspace(0, 1, crossfade_samples)
    fade_out = 1.0 - fade_in

    # Blend tail into the start of body
    body[:crossfade_samples] = body[:crossfade_samples] * fade_in + tail * fade_out

    return body


def normalize(signal: np.ndarray, peak: float = 0.9) -> np.ndarray:
    """Normalize signal to given peak amplitude."""
    mx = np.max(np.abs(signal))
    if mx > 0:
        return signal * (peak / mx)
    return signal.copy()


# ---------------------------------------------------------------------------
# Musical utilities
# ---------------------------------------------------------------------------

_NOTE_NAMES = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
    'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}


def note_freq(note: str) -> float:
    """Convert note name (e.g., 'A4', 'C#3', 'Eb2') to frequency in Hz.

    A4 = 440 Hz.
    """
    # Parse note name and octave
    if len(note) >= 3 and note[1] in '#b':
        name = note[:2]
        octave = int(note[2:])
    else:
        name = note[0]
        octave = int(note[1:])

    semitone = _NOTE_NAMES[name]
    # MIDI note number: C4 = 60, A4 = 69
    midi = semitone + (octave + 1) * 12
    return 440.0 * 2 ** ((midi - 69) / 12)


def chord_freqs(root: str, chord_type: str = 'minor') -> list:
    """Return frequencies for a chord.

    chord_type: 'minor', 'major', 'min7', 'maj7', 'dom7'
    """
    intervals = {
        'minor': [0, 3, 7],
        'major': [0, 4, 7],
        'min7': [0, 3, 7, 10],
        'maj7': [0, 4, 7, 11],
        'dom7': [0, 4, 7, 10],
    }
    root_freq = note_freq(root)
    return [root_freq * 2 ** (i / 12) for i in intervals[chord_type]]


def scale_freqs(root: str, scale_type: str = 'minor',
                octaves: int = 1) -> list:
    """Return frequencies for a scale.

    scale_type: 'minor', 'major', 'pentatonic_major', 'pentatonic_minor',
                'phrygian', 'chromatic'
    """
    patterns = {
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'major': [0, 2, 4, 5, 7, 9, 11],
        'pentatonic_major': [0, 2, 4, 7, 9],
        'pentatonic_minor': [0, 3, 5, 7, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'chromatic': list(range(12)),
    }
    root_freq = note_freq(root)
    freqs = []
    for oct in range(octaves):
        for interval in patterns[scale_type]:
            freqs.append(root_freq * 2 ** ((interval + oct * 12) / 12))
    return freqs
