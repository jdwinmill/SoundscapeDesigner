"""Unit tests for the DSP utility module (~35 tests)."""

import numpy as np
import pytest

from soundscape.dsp import (
    SR, sine, saw, square, noise_white, noise_brown,
    fm_synth, fm_bell, fm_bass,
    adsr, exponential_decay, tremolo,
    biquad_coeffs, biquad_apply, lowpass, highpass, bandpass, resonant_lowpass,
    reverb_schroeder, chorus, detune,
    beat_duration, place_hits, render_pattern,
    crossfade_loop, normalize,
    note_freq, chord_freqs, scale_freqs,
)
from tests.helpers import fft_peaks, rms, spectral_band_energy


# ---------------------------------------------------------------------------
# Oscillators
# ---------------------------------------------------------------------------

class TestOscillators:
    def test_sine_frequency(self):
        sig = sine(440, 1.0)
        peaks = fft_peaks(sig, SR, 1)
        assert abs(peaks[0][0] - 440) < 2

    def test_sine_duration(self):
        sig = sine(440, 0.5)
        assert len(sig) == int(SR * 0.5)

    def test_sine_amplitude(self):
        sig = sine(440, 0.1)
        assert np.max(np.abs(sig)) <= 1.001

    def test_saw_frequency(self):
        sig = saw(220, 1.0)
        peaks = fft_peaks(sig, SR, 1)
        assert abs(peaks[0][0] - 220) < 2

    def test_saw_harmonics(self):
        sig = saw(200, 1.0)
        peaks = fft_peaks(sig, SR, 3)
        freqs = sorted([p[0] for p in peaks])
        # Should have fundamental ~200 and harmonics ~400, ~600
        assert abs(freqs[0] - 200) < 5
        assert abs(freqs[1] - 400) < 5

    def test_square_frequency(self):
        sig = square(330, 1.0)
        peaks = fft_peaks(sig, SR, 1)
        assert abs(peaks[0][0] - 330) < 2

    def test_square_odd_harmonics(self):
        sig = square(200, 1.0)
        peaks = fft_peaks(sig, SR, 3)
        freqs = sorted([p[0] for p in peaks])
        # Square: only odd harmonics — 200, 600, 1000
        assert abs(freqs[0] - 200) < 5
        assert abs(freqs[1] - 600) < 5

    def test_noise_white_duration(self):
        sig = noise_white(2.0)
        assert len(sig) == int(SR * 2.0)

    def test_noise_white_zero_mean(self):
        np.random.seed(42)
        sig = noise_white(5.0)
        assert abs(np.mean(sig)) < 0.02

    def test_noise_brown_normalized(self):
        np.random.seed(42)
        sig = noise_brown(1.0)
        assert np.max(np.abs(sig)) <= 1.001


# ---------------------------------------------------------------------------
# FM Synthesis
# ---------------------------------------------------------------------------

class TestFMSynthesis:
    def test_fm_synth_carrier_present(self):
        sig = fm_synth(440, 440, 0.0, 1.0)
        peaks = fft_peaks(sig, SR, 1)
        assert abs(peaks[0][0] - 440) < 2

    def test_fm_synth_sidebands(self):
        sig = fm_synth(440, 100, 5.0, 1.0)
        peaks = fft_peaks(sig, SR, 5)
        freqs = sorted([p[0] for p in peaks])
        # With mod_freq=100, expect sidebands at 440±100, 440±200, etc.
        assert any(abs(f - 340) < 5 for f in freqs) or \
               any(abs(f - 540) < 5 for f in freqs)

    def test_fm_bell_decay(self):
        sig = fm_bell(800, 2.0)
        first_quarter = rms(sig[:len(sig) // 4])
        last_quarter = rms(sig[-len(sig) // 4:])
        assert first_quarter > last_quarter * 3

    def test_fm_bass_fundamental(self):
        sig = fm_bass(110, 1.0)
        peaks = fft_peaks(sig, SR, 1)
        # Fundamental should be near 110 Hz
        assert abs(peaks[0][0] - 110) < 10


# ---------------------------------------------------------------------------
# Envelopes
# ---------------------------------------------------------------------------

class TestEnvelopes:
    def test_adsr_attack_ramp(self):
        env = adsr(SR, 0.1, 0.05, 0.7, 0.1)
        attack_end = int(0.1 * SR)
        # Should ramp up to ~1.0
        assert env[attack_end - 1] > 0.95

    def test_adsr_sustain_hold(self):
        env = adsr(SR, 0.1, 0.05, 0.7, 0.1)
        mid = len(env) // 2
        assert abs(env[mid] - 0.7) < 0.05

    def test_adsr_release_to_zero(self):
        env = adsr(SR, 0.1, 0.05, 0.7, 0.1)
        assert env[-1] < 0.01

    def test_adsr_length(self):
        n = 10000
        env = adsr(n, 0.01, 0.01, 0.5, 0.01)
        assert len(env) == n

    def test_exponential_decay_shape(self):
        env = exponential_decay(SR, 5.0)
        assert abs(env[0] - 1.0) < 0.001
        assert env[-1] < 0.01

    def test_tremolo_range(self):
        env = tremolo(SR, 5.0, 0.5)
        # depth=0.5: oscillates between 0.5 and 1.0
        assert np.min(env) >= 0.49
        assert np.max(env) <= 1.01


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

class TestFilters:
    def test_lowpass_passes_low(self):
        sig = sine(100, 0.5)
        filtered = lowpass(sig, 500)
        assert rms(filtered) > rms(sig) * 0.8

    def test_lowpass_attenuates_high(self):
        sig = sine(5000, 0.5)
        filtered = lowpass(sig, 500)
        assert rms(filtered) < rms(sig) * 0.1

    def test_highpass_passes_high(self):
        sig = sine(5000, 0.5)
        filtered = highpass(sig, 500)
        assert rms(filtered) > rms(sig) * 0.8

    def test_highpass_attenuates_low(self):
        sig = sine(100, 0.5)
        filtered = highpass(sig, 500)
        assert rms(filtered) < rms(sig) * 0.15

    def test_bandpass_center(self):
        sig = sine(1000, 0.5)
        filtered = bandpass(sig, 1000, q=2.0)
        assert rms(filtered) > rms(sig) * 0.5

    def test_filter_stability(self):
        sig = noise_white(1.0)
        filtered = lowpass(sig, 1000)
        assert not np.any(np.isnan(filtered))
        assert not np.any(np.isinf(filtered))

    def test_resonant_lowpass_boost(self):
        np.random.seed(42)
        sig = noise_white(0.5)
        normal = lowpass(sig, 1000, q=0.707)
        resonant = resonant_lowpass(sig, 1000, q=8.0)
        # Resonant version should have higher energy around cutoff
        band_normal = spectral_band_energy(normal, SR, 800, 1200)
        band_resonant = spectral_band_energy(resonant, SR, 800, 1200)
        assert band_resonant > band_normal


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------

class TestEffects:
    def test_reverb_tail(self):
        # Impulse
        impulse = np.zeros(SR * 2)
        impulse[0] = 1.0
        wet = reverb_schroeder(impulse, mix=1.0)
        # Tail should have energy after the impulse
        tail_energy = rms(wet[SR // 4:])
        assert tail_energy > 0.0005

    def test_reverb_no_nan(self):
        sig = sine(440, 0.5)
        wet = reverb_schroeder(sig)
        assert not np.any(np.isnan(wet))

    def test_reverb_wet_dry(self):
        sig = sine(440, 0.5)
        dry = reverb_schroeder(sig, mix=0.0)
        np.testing.assert_allclose(dry, sig, atol=1e-10)


# ---------------------------------------------------------------------------
# Rhythm
# ---------------------------------------------------------------------------

class TestRhythm:
    def test_beat_duration_150bpm(self):
        bd = beat_duration(150)
        expected = int(SR * 60 / 150)
        assert bd == expected

    def test_place_hits_four_on_floor(self):
        hits = place_hits(4, subdivisions=1, bpm=120)
        assert len(hits) == 4
        bd = beat_duration(120)
        for i, (pos, vel) in enumerate(hits):
            assert abs(pos - i * bd) < 2

    def test_place_hits_sixteenths(self):
        hits = place_hits(1, subdivisions=4, bpm=120)
        assert len(hits) == 4

    def test_place_hits_swing(self):
        straight = place_hits(2, subdivisions=2, bpm=120, swing=0.0)
        swung = place_hits(2, subdivisions=2, bpm=120, swing=0.3)
        # Swung 2nd hit should be later than straight 2nd hit
        assert swung[1][0] > straight[1][0]

    def test_place_hits_pattern(self):
        hits = place_hits(2, subdivisions=4, pattern=[True, False, True, False],
                          bpm=120)
        assert len(hits) == 4  # 2 beats x 2 active per beat

    def test_render_pattern_length(self):
        hits = [(0, 1.0), (1000, 0.8)]
        one_shot = np.ones(100)
        out = render_pattern(hits, one_shot, 5000)
        assert len(out) == 5000
        assert out[0] > 0.9
        assert out[1000] > 0.7


# ---------------------------------------------------------------------------
# Musical
# ---------------------------------------------------------------------------

class TestMusical:
    def test_note_freq_a4(self):
        assert abs(note_freq('A4') - 440.0) < 0.01

    def test_note_freq_c4(self):
        assert abs(note_freq('C4') - 261.63) < 0.1

    def test_note_freq_octave(self):
        a3 = note_freq('A3')
        a4 = note_freq('A4')
        assert abs(a4 / a3 - 2.0) < 0.001

    def test_chord_minor(self):
        freqs = chord_freqs('A3', 'minor')
        assert len(freqs) == 3
        # Minor third = 3 semitones, perfect fifth = 7 semitones
        assert abs(freqs[1] / freqs[0] - 2 ** (3 / 12)) < 0.01
        assert abs(freqs[2] / freqs[0] - 2 ** (7 / 12)) < 0.01

    def test_chord_major(self):
        freqs = chord_freqs('C4', 'major')
        assert len(freqs) == 3
        assert abs(freqs[1] / freqs[0] - 2 ** (4 / 12)) < 0.01

    def test_scale_pentatonic(self):
        freqs = scale_freqs('D4', 'pentatonic_major', octaves=1)
        assert len(freqs) == 5

    def test_scale_phrygian(self):
        freqs = scale_freqs('E2', 'phrygian', octaves=1)
        assert len(freqs) == 7
        # Phrygian: half step from root (1 semitone)
        assert abs(freqs[1] / freqs[0] - 2 ** (1 / 12)) < 0.01


# ---------------------------------------------------------------------------
# Loop & Normalize
# ---------------------------------------------------------------------------

class TestLoopAndNormalize:
    def test_crossfade_loop_boundary(self):
        np.random.seed(42)
        sig = np.random.randn(SR)
        looped = crossfade_loop(sig, 1024)
        # Output should be shorter by crossfade_samples
        assert len(looped) == SR - 1024
        # The transition at the loop point should be smooth (no click).
        # Check that the jump from end to start is small relative to RMS.
        jump = abs(looped[0] - looped[-1])
        sig_rms = np.sqrt(np.mean(looped ** 2))
        assert jump / sig_rms < 3.0  # no drastic discontinuity

    def test_normalize_peak(self):
        sig = np.array([0.5, -0.3, 0.2])
        normed = normalize(sig, 0.9)
        assert abs(np.max(np.abs(normed)) - 0.9) < 0.001

    def test_normalize_zero_signal(self):
        sig = np.zeros(100)
        normed = normalize(sig)
        assert np.all(normed == 0)
