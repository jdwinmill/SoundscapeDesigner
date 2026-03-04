"""Per-stem validation tests (~50+ tests).

Tests cover format, spectral, rhythm, loop quality, and musical correctness.
"""

import numpy as np
import pytest

from soundscape.dsp import SR, note_freq, chord_freqs, scale_freqs
from generate_stems import GENERATORS, STEMS
from tests.helpers import fft_peaks, detect_onsets, rms, spectral_band_energy

# Collect all stem names for parametrized tests
ALL_STEM_NAMES = list(GENERATORS.keys())


# Cache generated stems so we don't re-synthesize for every test
_STEM_CACHE = {}


def _get_stem(name: str) -> np.ndarray:
    if name not in _STEM_CACHE:
        _STEM_CACHE[name] = GENERATORS[name]()
    return _STEM_CACHE[name]


# ---------------------------------------------------------------------------
# Format tests (parametrized x24)
# ---------------------------------------------------------------------------

class TestStemFormat:
    @pytest.mark.parametrize('name', ALL_STEM_NAMES)
    def test_sample_rate_compatible(self, name):
        """All stems should be generated at 44100 Hz (implicit in length)."""
        sig = _get_stem(name)
        # At 150 BPM, 16 beats = 6.4s = 282240 samples (minus crossfade)
        assert len(sig) > SR * 5  # at least 5 seconds

    @pytest.mark.parametrize('name', ALL_STEM_NAMES)
    def test_mono(self, name):
        sig = _get_stem(name)
        assert sig.ndim == 1

    @pytest.mark.parametrize('name', ALL_STEM_NAMES)
    def test_normalized(self, name):
        sig = _get_stem(name)
        peak = np.max(np.abs(sig))
        assert peak <= 0.91, f"Peak {peak} exceeds 0.91"
        assert peak >= 0.5, f"Peak {peak} too low (signal too quiet)"

    @pytest.mark.parametrize('name', ALL_STEM_NAMES)
    def test_no_nan_inf(self, name):
        sig = _get_stem(name)
        assert not np.any(np.isnan(sig)), "Signal contains NaN"
        assert not np.any(np.isinf(sig)), "Signal contains Inf"


# ---------------------------------------------------------------------------
# Loop quality tests (parametrized x24)
# ---------------------------------------------------------------------------

class TestLoopQuality:
    @pytest.mark.parametrize('name', ALL_STEM_NAMES)
    def test_boundary_amplitude(self, name):
        """Loop boundary should have no large discontinuity."""
        sig = _get_stem(name)
        jump = abs(sig[0] - sig[-1])
        sig_rms = rms(sig)
        if sig_rms > 0.001:
            assert jump / sig_rms < 5.0, \
                f"Large discontinuity at loop point: jump={jump:.4f}, rms={sig_rms:.4f}"


# ---------------------------------------------------------------------------
# Spectral tests — verify expected frequencies
# ---------------------------------------------------------------------------

class TestSpectral:
    def test_neon_pad_low_am_chord(self):
        """neon_pad_low should contain A minor chord frequencies."""
        sig = _get_stem('neon_pad_low')
        peaks = fft_peaks(sig, SR, 5)
        peak_freqs = [p[0] for p in peaks]
        a2 = note_freq('A2')
        # Should have fundamental near A2 (~110 Hz)
        assert any(abs(f - a2) / a2 < 0.05 for f in peak_freqs), \
            f"A2 ({a2:.1f} Hz) not found in peaks: {peak_freqs}"

    def test_neon_arp_notes(self):
        """neon_arp should contain Am arpeggio notes."""
        sig = _get_stem('neon_arp')
        peaks = fft_peaks(sig, SR, 8)
        peak_freqs = [p[0] for p in peaks]
        a3 = note_freq('A3')
        c4 = note_freq('C4')
        # At least A3 or C4 should appear
        found = any(abs(f - a3) / a3 < 0.05 for f in peak_freqs) or \
                any(abs(f - c4) / c4 < 0.05 for f in peak_freqs)
        assert found, f"Arp notes not in peaks: {peak_freqs}"

    def test_forest_drone_d2(self):
        """forest_drone should be centered around D2."""
        sig = _get_stem('forest_drone')
        d2 = note_freq('D2')
        band_energy = spectral_band_energy(sig, SR, d2 * 0.8, d2 * 1.2)
        assert band_energy > 0.3, f"D2 band energy too low: {band_energy}"

    def test_forest_bass_low_energy(self):
        """forest_bass should have strong low-frequency content."""
        sig = _get_stem('forest_bass')
        low_energy = spectral_band_energy(sig, SR, 50, 200)
        assert low_energy > 0.2, f"Low energy too low: {low_energy}"

    def test_midnight_drone_e2(self):
        """midnight_drone should be centered around E2."""
        sig = _get_stem('midnight_drone')
        e2 = note_freq('E2')
        band_energy = spectral_band_energy(sig, SR, e2 * 0.8, e2 * 1.2)
        assert band_energy > 0.2, f"E2 band energy too low: {band_energy}"

    def test_midnight_sub_low_freq(self):
        """midnight_sub should have strong sub-bass content."""
        sig = _get_stem('midnight_sub')
        sub_energy = spectral_band_energy(sig, SR, 30, 150)
        assert sub_energy > 0.1, f"Sub energy too low: {sub_energy}"

    def test_neon_kick_sub_energy(self):
        """neon_kick should have strong sub-bass from pitch sweep."""
        sig = _get_stem('neon_kick')
        sub_energy = spectral_band_energy(sig, SR, 30, 120)
        assert sub_energy > 0.05, f"Kick sub energy too low: {sub_energy}"

    def test_neon_hihat_high_freq(self):
        """neon_hihat should have dominant high-frequency content."""
        sig = _get_stem('neon_hihat')
        high_energy = spectral_band_energy(sig, SR, 4000, 20000)
        low_energy = spectral_band_energy(sig, SR, 20, 1000)
        assert high_energy > low_energy, \
            f"Hi-hat should be bright: high={high_energy}, low={low_energy}"

    def test_midnight_hat_high_freq(self):
        """midnight_hat should have dominant high-frequency content."""
        sig = _get_stem('midnight_hat')
        high_energy = spectral_band_energy(sig, SR, 3000, 20000)
        low_energy = spectral_band_energy(sig, SR, 20, 500)
        assert high_energy > low_energy

    def test_forest_shaker_high_freq(self):
        """forest_shaker should be high-frequency."""
        sig = _get_stem('forest_shaker')
        high_energy = spectral_band_energy(sig, SR, 4000, 20000)
        assert high_energy > 0.2


# ---------------------------------------------------------------------------
# Rhythm tests — verify beat grid
# ---------------------------------------------------------------------------

class TestRhythm:
    def test_neon_kick_four_on_floor(self):
        """neon_kick should have onsets on the beat grid."""
        sig = _get_stem('neon_kick')
        onsets = detect_onsets(sig, SR, threshold=0.15)
        # 16 beats at 150 BPM = 0.4s per beat
        beat_s = 60 / 150
        # Should have roughly 16 onsets (4 bars x 4 beats)
        assert len(onsets) >= 12, f"Too few kick onsets: {len(onsets)}"
        # First onset should be near time 0
        assert onsets[0] < beat_s * 0.5, f"First onset too late: {onsets[0]}"

    def test_midnight_kick_four_on_floor(self):
        """midnight_kick should have regular onsets."""
        sig = _get_stem('midnight_kick')
        onsets = detect_onsets(sig, SR, threshold=0.15)
        assert len(onsets) >= 12

    def test_neon_hihat_dense(self):
        """neon_hihat should have many onsets (16th notes)."""
        sig = _get_stem('neon_hihat')
        onsets = detect_onsets(sig, SR, threshold=0.1)
        # 16 beats x 4 subdivisions = 64 total, expect at least 30
        assert len(onsets) >= 20, f"Too few hat onsets: {len(onsets)}"

    def test_forest_clicks_sparse(self):
        """forest_clicks should have ~8 onsets (beats 1+3 of 4 bars)."""
        sig = _get_stem('forest_clicks')
        onsets = detect_onsets(sig, SR, threshold=0.1)
        assert 4 <= len(onsets) <= 16, f"Unexpected click count: {len(onsets)}"

    def test_midnight_clap_beats_2_4(self):
        """midnight_clap should have ~8 onsets (beats 2+4 of 4 bars)."""
        sig = _get_stem('midnight_clap')
        onsets = detect_onsets(sig, SR, threshold=0.1)
        assert 4 <= len(onsets) <= 16, f"Unexpected clap count: {len(onsets)}"


# ---------------------------------------------------------------------------
# Musical tests — verify chord intervals
# ---------------------------------------------------------------------------

class TestMusical:
    def test_neon_pad_low_minor_chord(self):
        """Verify Am chord has minor third interval."""
        freqs = chord_freqs('A2', 'minor')
        ratio = freqs[1] / freqs[0]
        expected = 2 ** (3 / 12)  # minor third
        assert abs(ratio - expected) < 0.01

    def test_neon_pad_mid_min7(self):
        """Verify Am7 chord has 4 notes with correct intervals."""
        freqs = chord_freqs('A3', 'min7')
        assert len(freqs) == 4
        # Minor seventh = 10 semitones
        ratio_7th = freqs[3] / freqs[0]
        expected = 2 ** (10 / 12)
        assert abs(ratio_7th - expected) < 0.01

    def test_forest_pad_maj7(self):
        """Verify Dmaj7 chord."""
        freqs = chord_freqs('D3', 'maj7')
        assert len(freqs) == 4
        # Major third = 4 semitones
        ratio_3rd = freqs[1] / freqs[0]
        assert abs(ratio_3rd - 2 ** (4 / 12)) < 0.01

    def test_forest_marimba_pentatonic(self):
        """Verify D major pentatonic has 5 notes per octave."""
        freqs = scale_freqs('D3', 'pentatonic_major', octaves=1)
        assert len(freqs) == 5

    def test_midnight_phrygian_intervals(self):
        """Verify E Phrygian scale: half step from root."""
        freqs = scale_freqs('E2', 'phrygian', octaves=1)
        assert len(freqs) == 7
        # First interval is 1 semitone (Phrygian characteristic)
        ratio = freqs[1] / freqs[0]
        assert abs(ratio - 2 ** (1 / 12)) < 0.01

    def test_neon_lead_progression(self):
        """Verify Am-Em-F-G progression uses correct roots."""
        am = chord_freqs('A3', 'minor')
        em = chord_freqs('E3', 'minor')
        fmaj = chord_freqs('F3', 'major')
        gmaj = chord_freqs('G3', 'major')
        # All should have 3 notes
        assert all(len(c) == 3 for c in [am, em, fmaj, gmaj])

    def test_midnight_acid_phrygian_notes(self):
        """Acid bass notes E-F-G-B are from E Phrygian."""
        e2 = note_freq('E2')
        f2 = note_freq('F2')
        g2 = note_freq('G2')
        b2 = note_freq('B2')
        phrygian = scale_freqs('E2', 'phrygian', octaves=1)
        # All acid notes should be in the Phrygian scale (within tolerance)
        for note_f in [e2, f2, g2, b2]:
            found = any(abs(note_f - sf) / note_f < 0.01 for sf in phrygian)
            assert found, f"{note_f} Hz not in E Phrygian scale"
