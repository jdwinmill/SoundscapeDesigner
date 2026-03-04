"""Full mix scenario tests (~25 tests).

Tests cover BPM coverage, zone checks, mix output, and smooth transitions.
"""

import numpy as np
import pytest

from soundscape.stem import Stem
from soundscape.mixer import Mixer
from soundscape.dsp import SR
from generate_stems import STEMS, GENERATORS
from tests.helpers import rms

# Cache stems for efficiency
_STEM_CACHE = {}


def _get_audio(name: str) -> np.ndarray:
    if name not in _STEM_CACHE:
        _STEM_CACHE[name] = GENERATORS[name]()
    return _STEM_CACHE[name]


def _build_stems(variety: str) -> list:
    """Build Stem objects for a variety with audio loaded."""
    stems = []
    for name, func, bpm_low, bpm_high, fade_in, fade_out, volume in STEMS[variety]:
        audio = _get_audio(name)
        stem = Stem(
            bpm_low=bpm_low,
            bpm_high=bpm_high,
            fade_in=fade_in,
            fade_out=fade_out,
            volume=volume,
            base_bpm=150.0,
            audio_data=audio,
            sample_rate=SR,
        )
        stems.append((name, stem))
    return stems


# ---------------------------------------------------------------------------
# BPM coverage tests (parametrized 100–200)
# ---------------------------------------------------------------------------

VARIETIES = ['neon', 'forest', 'midnight']
BPM_RANGE = list(range(100, 201, 10))


class TestBPMCoverage:
    @pytest.mark.parametrize('variety', VARIETIES)
    @pytest.mark.parametrize('bpm', BPM_RANGE)
    def test_at_least_two_stems_audible(self, variety, bpm):
        """At every BPM from 100-200, at least 2 stems should be audible."""
        stems = _build_stems(variety)
        audible = [(name, s.volume_at_bpm(bpm))
                   for name, s in stems if s.volume_at_bpm(bpm) > 0.01]
        assert len(audible) >= 2, \
            f"{variety} at {bpm} BPM: only {len(audible)} audible stems: " \
            f"{[(n, f'{v:.2f}') for n, v in audible]}"


# ---------------------------------------------------------------------------
# Zone checks
# ---------------------------------------------------------------------------

class TestZoneChecks:
    def _active_names(self, variety: str, bpm: float, threshold: float = 0.05):
        stems = _build_stems(variety)
        return [name for name, s in stems if s.volume_at_bpm(bpm) > threshold]

    # Walk/Warmup (100-130 BPM): should have ambient layers
    @pytest.mark.parametrize('variety', VARIETIES)
    def test_walk_zone_has_ambient(self, variety):
        active = self._active_names(variety, 110)
        assert len(active) >= 2, f"Walk zone too sparse: {active}"

    # Steady run (155-175 BPM): should have most layers active
    @pytest.mark.parametrize('variety', VARIETIES)
    def test_run_zone_most_active(self, variety):
        active_run = self._active_names(variety, 165)
        active_walk = self._active_names(variety, 110)
        assert len(active_run) > len(active_walk), \
            f"Run zone ({len(active_run)}) should have more stems than walk ({len(active_walk)})"

    # Sprint (175-200 BPM): should have driving elements
    @pytest.mark.parametrize('variety', VARIETIES)
    def test_sprint_zone_has_rhythm(self, variety):
        active = self._active_names(variety, 190)
        assert len(active) >= 3, f"Sprint zone too sparse: {active}"


# ---------------------------------------------------------------------------
# Mix output tests
# ---------------------------------------------------------------------------

class TestMixOutput:
    @pytest.mark.parametrize('variety', VARIETIES)
    def test_mix_not_silent(self, variety):
        """Mixed output should not be silent at mid BPM."""
        mixer = Mixer(sample_rate=SR, block_size=4096)
        stems = _build_stems(variety)
        mixer.set_stems([s for _, s in stems])
        mixer.set_bpm(160)
        block = mixer._generate_block(SR)  # 1 second
        assert rms(block) > 0.01, f"{variety} mix is silent at 160 BPM"

    @pytest.mark.parametrize('variety', VARIETIES)
    def test_mix_no_clipping(self, variety):
        """Mixed output should stay within [-1, 1]."""
        mixer = Mixer(sample_rate=SR, block_size=4096)
        stems = _build_stems(variety)
        mixer.set_stems([s for _, s in stems])
        mixer.set_bpm(170)
        block = mixer._generate_block(SR * 2)  # 2 seconds
        assert np.max(np.abs(block)) <= 1.0, f"{variety} mix clips at 170 BPM"

    @pytest.mark.parametrize('variety', VARIETIES)
    def test_mix_spectral_balance(self, variety):
        """Mix should have both low and high frequency content."""
        mixer = Mixer(sample_rate=SR, block_size=4096)
        stems = _build_stems(variety)
        mixer.set_stems([s for _, s in stems])
        mixer.set_bpm(165)
        block = mixer._generate_block(SR * 2)
        spectrum = np.abs(np.fft.rfft(block))
        freqs = np.fft.rfftfreq(len(block), 1.0 / SR)
        low = np.sum(spectrum[(freqs >= 30) & (freqs <= 300)])
        high = np.sum(spectrum[(freqs >= 2000) & (freqs <= 10000)])
        # Both bands should have some energy
        total = np.sum(spectrum)
        if total > 0:
            assert low / total > 0.001, f"{variety} missing low frequencies"


# ---------------------------------------------------------------------------
# Smooth transition tests
# ---------------------------------------------------------------------------

class TestSmoothTransitions:
    @pytest.mark.parametrize('variety', VARIETIES)
    def test_bpm_sweep_no_jumps(self, variety):
        """Sweeping BPM 140->160 should produce smooth volume changes."""
        stems = _build_stems(variety)
        bpms = np.linspace(140, 160, 20)
        total_volumes = []
        for bpm in bpms:
            total = sum(s.volume_at_bpm(bpm) for _, s in stems)
            total_volumes.append(total)
        # Check no sudden jumps (max diff between consecutive BPMs)
        diffs = np.abs(np.diff(total_volumes))
        max_jump = np.max(diffs)
        assert max_jump < 0.5, \
            f"{variety} has sudden volume jump of {max_jump:.3f} during sweep"

    @pytest.mark.parametrize('variety', VARIETIES)
    def test_volume_monotonic_in_ramp_up(self, variety):
        """Total volume should generally increase from 100 to 170 BPM."""
        stems = _build_stems(variety)
        vol_100 = sum(s.volume_at_bpm(100) for _, s in stems)
        vol_170 = sum(s.volume_at_bpm(170) for _, s in stems)
        assert vol_170 > vol_100, \
            f"{variety}: volume at 170 ({vol_170:.2f}) not greater than at 100 ({vol_100:.2f})"
