import numpy as np
import pytest

from soundscape.stem import Stem


class TestVolumeAtBpm:
    """Test the trapezoidal volume curve.

    Curve shape:
    1.0  |        ___________
         |       /           \\
    0.0  |_____/               \\________
             A  B           C  D
    A = bpm_low - fade_in
    B = bpm_low
    C = bpm_high
    D = bpm_high + fade_out
    """

    def test_inside_range_full_volume(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(140) == pytest.approx(1.0)

    def test_at_bpm_low_boundary(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(120) == pytest.approx(1.0)

    def test_at_bpm_high_boundary(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(160) == pytest.approx(1.0)

    def test_fade_in_midpoint(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        # Midpoint of fade-in (A=110, B=120), so BPM 115 -> 0.5
        assert stem.volume_at_bpm(115) == pytest.approx(0.5)

    def test_fade_out_midpoint(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        # Midpoint of fade-out (C=160, D=170), so BPM 165 -> 0.5
        assert stem.volume_at_bpm(165) == pytest.approx(0.5)

    def test_below_fade_in_is_zero(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(100) == pytest.approx(0.0)

    def test_above_fade_out_is_zero(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(180) == pytest.approx(0.0)

    def test_at_fade_in_start_is_zero(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(110) == pytest.approx(0.0)

    def test_at_fade_out_end_is_zero(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10)
        assert stem.volume_at_bpm(170) == pytest.approx(0.0)

    def test_zero_width_fade_in(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=0, fade_out=10)
        # No fade-in: should jump from 0 to 1 at bpm_low
        assert stem.volume_at_bpm(119.9) == pytest.approx(0.0)
        assert stem.volume_at_bpm(120) == pytest.approx(1.0)

    def test_zero_width_fade_out(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=0)
        # No fade-out: should drop from 1 to 0 at bpm_high
        assert stem.volume_at_bpm(160) == pytest.approx(1.0)
        assert stem.volume_at_bpm(160.1) == pytest.approx(0.0)

    def test_volume_scaled_by_stem_volume(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10, volume=0.5)
        assert stem.volume_at_bpm(140) == pytest.approx(0.5)

    def test_muted_returns_zero(self):
        stem = Stem(bpm_low=120, bpm_high=160, fade_in=10, fade_out=10, muted=True)
        assert stem.volume_at_bpm(140) == pytest.approx(0.0)


class TestStemDefaults:
    def test_default_values(self):
        stem = Stem(bpm_low=100, bpm_high=140)
        assert stem.fade_in == 5.0
        assert stem.fade_out == 5.0
        assert stem.volume == 1.0
        assert stem.muted is False
        assert stem.solo is False
        assert stem.base_bpm == 150.0
        assert stem.file_path is None
        assert stem.audio_data is None
        assert stem.sample_rate is None
