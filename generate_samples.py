"""Generate 10 diverse audio stems for testing the Soundscape Designer.

Each stem is a short loopable clip (4-8 seconds) at 44100 Hz mono.
Run once: python generate_samples.py
"""

import os
import numpy as np
import soundfile as sf

SR = 44100
OUT_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(OUT_DIR, exist_ok=True)


def save(name: str, data: np.ndarray):
    # Normalize to -0.9..0.9 to avoid clipping
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data / peak * 0.9
    path = os.path.join(OUT_DIR, f"{name}.wav")
    sf.write(path, data.astype(np.float32), SR)
    print(f"  {name}.wav  ({len(data)/SR:.1f}s)")


def kick_loop():
    """Punchy four-on-the-floor kick at 150 BPM — 4 beats, ~1.6s loop."""
    bpm = 150
    beat = SR * 60 // bpm
    loop = np.zeros(beat * 4)
    for i in range(4):
        t = np.arange(beat) / SR
        env = np.exp(-t * 30)
        hit = np.sin(2 * np.pi * (60 - 40 * t) * t) * env
        loop[i * beat : i * beat + beat] = hit
    return loop


def hihat_loop():
    """16th-note hi-hat pattern — filtered noise bursts."""
    bpm = 150
    sixteenth = SR * 60 // bpm // 4
    loop = np.zeros(sixteenth * 16)
    for i in range(16):
        t = np.arange(sixteenth) / SR
        env = np.exp(-t * 80)
        noise = np.random.randn(sixteenth) * env * 0.4
        # Simple highpass via diff
        noise = np.diff(np.concatenate([[0], noise]))
        accent = 1.0 if i % 4 == 0 else 0.5
        loop[i * sixteenth : i * sixteenth + sixteenth] = noise * accent
    return loop


def bass_pulse():
    """Sub-bass pulse — sine wave with rhythmic envelope."""
    bpm = 150
    beat = SR * 60 // bpm
    loop = np.zeros(beat * 4)
    for i in range(4):
        t = np.arange(beat) / SR
        env = np.exp(-t * 8) * 0.7
        freq = 55 if i % 2 == 0 else 65.41  # A1 / C2
        loop[i * beat : i * beat + beat] = np.sin(2 * np.pi * freq * t) * env
    return loop


def pad_warm():
    """Warm synth pad — stacked detuned saws, slow attack/release."""
    dur = 6.0
    t = np.arange(int(SR * dur)) / SR
    env = np.minimum(t / 1.5, 1.0) * np.minimum((dur - t) / 1.5, 1.0)
    # Detuned saw stack around C3
    freqs = [130.81, 131.2, 130.4, 261.63, 196.0]
    out = np.zeros_like(t)
    for f in freqs:
        phase = (t * f) % 1.0
        out += (phase * 2 - 1) * 0.2
    return out * env


def pad_dark():
    """Dark ambient pad — low filtered noise + sub sine drone."""
    dur = 8.0
    n = int(SR * dur)
    t = np.arange(n) / SR
    env = np.minimum(t / 2.0, 1.0) * np.minimum((dur - t) / 2.0, 1.0)
    # Brownian noise (integrated white noise)
    noise = np.cumsum(np.random.randn(n) * 0.001)
    noise -= np.linspace(noise[0], noise[-1], n)  # detrend for looping
    # Sub drone
    drone = np.sin(2 * np.pi * 55 * t) * 0.3
    return (noise + drone) * env


def arp_bright():
    """Bright arpeggio — cycling C-E-G-C pattern."""
    bpm = 150
    sixteenth = SR * 60 // bpm // 4
    notes = [261.63, 329.63, 392.0, 523.25]  # C4 E4 G4 C5
    loop = np.zeros(sixteenth * len(notes) * 4)
    for i in range(len(notes) * 4):
        freq = notes[i % len(notes)]
        t = np.arange(sixteenth) / SR
        env = np.exp(-t * 15)
        tone = np.sin(2 * np.pi * freq * t) * env * 0.5
        # Add a bit of overtone
        tone += np.sin(2 * np.pi * freq * 2 * t) * env * 0.15
        loop[i * sixteenth : i * sixteenth + sixteenth] = tone
    return loop


def shaker():
    """Shaker / maracas — 8th-note shuffle pattern."""
    bpm = 150
    eighth = SR * 60 // bpm // 2
    loop = np.zeros(eighth * 8)
    for i in range(8):
        t = np.arange(eighth) / SR
        env = np.exp(-t * 60) * (0.8 if i % 2 == 0 else 0.4)
        noise = np.random.randn(eighth) * env
        # Bandpass-ish: diff twice for highpass
        noise = np.diff(np.diff(np.concatenate([[0, 0], noise])))
        loop[i * eighth : i * eighth + eighth] = noise
    return loop


def rain_texture():
    """Rain / nature texture — shaped noise with random droplet pings."""
    dur = 6.0
    n = int(SR * dur)
    t = np.arange(n) / SR
    # Base rain noise
    rain = np.random.randn(n) * 0.15
    # Simple lowpass via moving average
    kernel = np.ones(200) / 200
    rain = np.convolve(rain, kernel, mode='same')
    # Random droplet pings
    for _ in range(40):
        pos = np.random.randint(0, n - SR // 10)
        length = SR // 20
        dt = np.arange(length) / SR
        freq = np.random.uniform(2000, 5000)
        ping = np.sin(2 * np.pi * freq * dt) * np.exp(-dt * 80) * 0.3
        rain[pos : pos + length] += ping
    # Crossfade ends for looping
    fade = int(SR * 0.1)
    ramp = np.linspace(0, 1, fade)
    rain[:fade] *= ramp
    rain[-fade:] *= ramp[::-1]
    return rain


def breath_texture():
    """Rhythmic breathing texture — slow inhale/exhale noise shaped to BPM."""
    bpm = 150
    # One breath cycle = 2 beats
    cycle = SR * 60 // bpm * 2
    loops = 4
    out = np.zeros(cycle * loops)
    for i in range(loops):
        t = np.arange(cycle) / SR
        dur_s = cycle / SR
        # Envelope: rise then fall
        env = np.sin(np.pi * t / dur_s) ** 2 * 0.5
        noise = np.random.randn(cycle)
        # Bandpass: moving average then diff
        kernel = np.ones(100) / 100
        noise = np.convolve(noise, kernel, mode='same')
        out[i * cycle : i * cycle + cycle] = noise * env
    return out


def melodic_chime():
    """Pentatonic chime hits — sparse bell-like tones."""
    bpm = 150
    beat = SR * 60 // bpm
    bars = 4
    loop = np.zeros(beat * 4 * bars)
    # Pentatonic: C D E G A across octaves
    scale = [261.63, 293.66, 329.63, 392.0, 440.0,
             523.25, 587.33, 659.25, 783.99, 880.0]
    np.random.seed(42)  # Reproducible pattern
    hits = sorted(np.random.choice(beat * 4 * bars, size=12, replace=False))
    for pos in hits:
        freq = np.random.choice(scale)
        length = min(SR, len(loop) - pos)
        t = np.arange(length) / SR
        # Bell: fundamental + inharmonic partials
        tone = np.sin(2 * np.pi * freq * t) * 0.4
        tone += np.sin(2 * np.pi * freq * 2.76 * t) * 0.15
        tone += np.sin(2 * np.pi * freq * 5.4 * t) * 0.05
        env = np.exp(-t * 5)
        loop[pos : pos + length] += tone * env
    return loop


if __name__ == "__main__":
    print("Generating samples...")
    save("01_kick_loop", kick_loop())
    save("02_hihat_loop", hihat_loop())
    save("03_bass_pulse", bass_pulse())
    save("04_pad_warm", pad_warm())
    save("05_pad_dark", pad_dark())
    save("06_arp_bright", arp_bright())
    save("07_shaker", shaker())
    save("08_rain_texture", rain_texture())
    save("09_breath_texture", breath_texture())
    save("10_melodic_chime", melodic_chime())
    print(f"\nDone — {len(os.listdir(OUT_DIR))} files in {OUT_DIR}/")
