"""Shared test utilities for audio analysis."""

import numpy as np


def fft_peaks(signal: np.ndarray, sr: int, n_peaks: int = 5) -> list:
    """Find the top N frequency peaks via windowed FFT.

    Returns list of (frequency_hz, magnitude) tuples sorted by magnitude desc.
    """
    windowed = signal * np.hanning(len(signal))
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(signal), 1.0 / sr)

    # Ignore DC and very low frequencies
    min_bin = max(1, int(20 * len(signal) / sr))
    spectrum[:min_bin] = 0

    peaks = []
    spec_copy = spectrum.copy()
    for _ in range(n_peaks):
        idx = np.argmax(spec_copy)
        if spec_copy[idx] < 1e-10:
            break
        peaks.append((freqs[idx], spec_copy[idx]))
        # Zero out neighborhood to find next peak
        radius = max(3, int(50 * len(signal) / sr))
        lo = max(0, idx - radius)
        hi = min(len(spec_copy), idx + radius + 1)
        spec_copy[lo:hi] = 0

    return peaks


def detect_onsets(signal: np.ndarray, sr: int,
                  threshold: float = 0.1) -> list:
    """Detect amplitude onsets using envelope follower.

    Returns list of onset times in seconds.
    """
    # Compute amplitude envelope (rectify + smooth)
    rectified = np.abs(signal)
    # Smooth with ~5ms window
    window_size = max(1, int(sr * 0.005))
    kernel = np.ones(window_size) / window_size
    envelope = np.convolve(rectified, kernel, mode='same')

    # Normalize envelope
    peak = np.max(envelope)
    if peak > 0:
        envelope = envelope / peak

    # Find rising edges above threshold
    onsets = []
    above = False
    min_gap = int(sr * 0.03)  # Minimum 30ms between onsets
    last_onset = -min_gap

    for i in range(1, len(envelope)):
        if not above and envelope[i] > threshold and (i - last_onset) >= min_gap:
            onsets.append(i / sr)
            above = True
            last_onset = i
        elif above and envelope[i] < threshold * 0.5:
            above = False

    return onsets


def rms(signal: np.ndarray) -> float:
    """Root mean square of a signal."""
    return float(np.sqrt(np.mean(signal ** 2)))


def spectral_band_energy(signal: np.ndarray, sr: int,
                         low_hz: float, high_hz: float) -> float:
    """Compute energy in a frequency band (as fraction of total energy)."""
    spectrum = np.abs(np.fft.rfft(signal)) ** 2
    freqs = np.fft.rfftfreq(len(signal), 1.0 / sr)

    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    total = np.sum(spectrum)
    if total < 1e-20:
        return 0.0
    return float(np.sum(spectrum[band_mask]) / total)
