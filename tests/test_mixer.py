import numpy as np
import pytest

from soundscape.stem import Stem
from soundscape.mixer import Mixer


def _make_stem(audio, sr=44100, bpm_low=100, bpm_high=200, base_bpm=150.0, **kwargs):
    """Helper to create a stem with inline audio data."""
    return Stem(
        bpm_low=bpm_low,
        bpm_high=bpm_high,
        audio_data=audio.astype(np.float32),
        sample_rate=sr,
        base_bpm=base_bpm,
        **kwargs,
    )


class TestGenerateBlock:
    def test_single_stem_in_range(self):
        audio = np.ones(44100, dtype=np.float32) * 0.5
        stem = _make_stem(audio)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        assert block.shape == (1024,)
        np.testing.assert_allclose(block, 0.5, atol=0.01)

    def test_single_stem_out_of_range(self):
        audio = np.ones(44100, dtype=np.float32) * 0.5
        stem = _make_stem(audio, bpm_low=100, bpm_high=120)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(200.0)  # well outside range

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.0, atol=1e-7)

    def test_multiple_stems_summed(self):
        audio1 = np.ones(44100, dtype=np.float32) * 0.3
        audio2 = np.ones(44100, dtype=np.float32) * 0.2
        stem1 = _make_stem(audio1)
        stem2 = _make_stem(audio2)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem1, stem2])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.5, atol=0.01)

    def test_muted_stem_excluded(self):
        audio = np.ones(44100, dtype=np.float32) * 0.5
        stem = _make_stem(audio, muted=True)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.0, atol=1e-7)

    def test_solo_isolates_stem(self):
        audio1 = np.ones(44100, dtype=np.float32) * 0.3
        audio2 = np.ones(44100, dtype=np.float32) * 0.7
        stem1 = _make_stem(audio1, solo=True)
        stem2 = _make_stem(audio2)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem1, stem2])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        # Only solo stem should be heard
        np.testing.assert_allclose(block, 0.3, atol=0.01)

    def test_multiple_solos(self):
        audio1 = np.ones(44100, dtype=np.float32) * 0.3
        audio2 = np.ones(44100, dtype=np.float32) * 0.2
        stem1 = _make_stem(audio1, solo=True)
        stem2 = _make_stem(audio2, solo=True)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem1, stem2])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.5, atol=0.01)

    def test_master_volume(self):
        audio = np.ones(44100, dtype=np.float32) * 0.8
        stem = _make_stem(audio)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(150.0)
        mixer.set_master_volume(0.5)

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.4, atol=0.01)

    def test_clipping(self):
        audio1 = np.ones(44100, dtype=np.float32) * 0.8
        audio2 = np.ones(44100, dtype=np.float32) * 0.8
        stem1 = _make_stem(audio1)
        stem2 = _make_stem(audio2)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem1, stem2])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        # Sum would be 1.6, should clip to 1.0
        assert block.max() <= 1.0
        assert block.min() >= -1.0

    def test_empty_mixer(self):
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        assert block.shape == (1024,)
        np.testing.assert_allclose(block, 0.0, atol=1e-7)

    def test_resampling_ratio(self):
        """Playback at double BPM should consume audio at double rate."""
        sr = 44100
        duration = 2.0
        n_samples = int(sr * duration)
        # Ramp from 0 to 1 over duration
        audio = np.linspace(0, 1, n_samples, dtype=np.float32)
        stem = _make_stem(audio, bpm_low=50, bpm_high=400, base_bpm=100.0)

        mixer = Mixer(sample_rate=sr, block_size=1024)
        mixer.set_stems([stem])

        # At base BPM (100), 1024 samples should map to positions 0..1023
        mixer.set_bpm(100.0)
        mixer._playback_positions = {id(stem): 0.0}
        block_normal = mixer._generate_block(1024)

        # At 2x BPM (200), 1024 samples should map to positions 0..2047
        mixer.set_bpm(200.0)
        mixer._playback_positions = {id(stem): 0.0}
        block_fast = mixer._generate_block(1024)

        # The fast block should reach higher values (further into the ramp)
        assert block_fast[-1] > block_normal[-1] * 1.5

    def test_looping(self):
        """Audio should loop when playback position exceeds length."""
        sr = 44100
        short_audio = np.ones(512, dtype=np.float32) * 0.5
        stem = _make_stem(short_audio, sr=sr)

        mixer = Mixer(sample_rate=sr, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(150.0)

        # Generate a block larger than the audio — should loop without error
        block = mixer._generate_block(1024)
        assert block.shape == (1024,)
        np.testing.assert_allclose(block, 0.5, atol=0.01)

    def test_stem_volume_applied(self):
        audio = np.ones(44100, dtype=np.float32) * 1.0
        stem = _make_stem(audio, volume=0.4)
        mixer = Mixer(sample_rate=44100, block_size=1024)
        mixer.set_stems([stem])
        mixer.set_bpm(150.0)

        block = mixer._generate_block(1024)
        np.testing.assert_allclose(block, 0.4, atol=0.01)

    def test_per_stem_base_bpm_different_rates(self):
        """Two stems with different base_bpm should advance at different rates."""
        sr = 44100
        n_samples = int(sr * 2.0)
        # Ramp audio so playback position is audible in the output
        audio = np.linspace(0, 1, n_samples, dtype=np.float32)

        # Stem A: base_bpm=100 → at 200 BPM plays at 2x speed
        stem_a = _make_stem(audio, bpm_low=50, bpm_high=400, base_bpm=100.0)
        # Stem B: base_bpm=200 → at 200 BPM plays at 1x speed
        stem_b = _make_stem(audio, bpm_low=50, bpm_high=400, base_bpm=200.0)

        mixer = Mixer(sample_rate=sr, block_size=1024)
        mixer.set_bpm(200.0)

        # Generate block for stem A alone
        mixer.set_stems([stem_a])
        mixer._playback_positions = {id(stem_a): 0.0}
        block_a = mixer._generate_block(1024)

        # Generate block for stem B alone
        mixer.set_stems([stem_b])
        mixer._playback_positions = {id(stem_b): 0.0}
        block_b = mixer._generate_block(1024)

        # Stem A (base 100, playing at 200) should reach further into the ramp
        assert block_a[-1] > block_b[-1] * 1.5
