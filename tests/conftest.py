import tempfile
import os

import numpy as np
import pytest


@pytest.fixture
def mono_audio():
    """1 second of 440 Hz sine wave, mono, 44100 Hz."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    return np.sin(2 * np.pi * 440 * t).astype(np.float32), sr


@pytest.fixture
def stereo_audio():
    """1 second of stereo audio (440 Hz left, 880 Hz right), 44100 Hz."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    left = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    right = np.sin(2 * np.pi * 880 * t).astype(np.float32)
    return np.column_stack((left, right)), sr


@pytest.fixture
def mono_wav(mono_audio, tmp_path):
    """Write mono audio to a temp wav file, return path."""
    import soundfile as sf

    data, sr = mono_audio
    path = tmp_path / "mono.wav"
    sf.write(str(path), data, sr)
    return str(path)


@pytest.fixture
def stereo_wav(stereo_audio, tmp_path):
    """Write stereo audio to a temp wav file, return path."""
    import soundfile as sf

    data, sr = stereo_audio
    path = tmp_path / "stereo.wav"
    sf.write(str(path), data, sr)
    return str(path)


@pytest.fixture
def short_mono_audio():
    """Very short mono audio (0.1 seconds) for fast tests."""
    sr = 44100
    samples = int(sr * 0.1)
    t = np.linspace(0, 0.1, samples, endpoint=False)
    return np.sin(2 * np.pi * 440 * t).astype(np.float32), sr


@pytest.fixture
def short_mono_wav(short_mono_audio, tmp_path):
    """Write short mono audio to a temp wav file."""
    import soundfile as sf

    data, sr = short_mono_audio
    path = tmp_path / "short_mono.wav"
    sf.write(str(path), data, sr)
    return str(path)
