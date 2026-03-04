from typing import List, Optional

import numpy as np

from soundscape.stem import Stem


class Mixer:
    """Real-time audio mixer with BPM-reactive volume curves.

    The mixer sums audio from multiple stems, applying per-stem volume
    curves based on the current BPM. Audio is resampled on the fly to
    match tempo changes (pitch shifts proportionally).

    Thread safety: the stems list is replaced atomically (never mutated).
    The audio callback reads a snapshot of the list reference.
    """

    def __init__(self, sample_rate: int = 44100, block_size: int = 1024):
        self._sample_rate = sample_rate
        self._block_size = block_size
        self._stems: List[Stem] = []
        self._bpm: float = 150.0
        self._master_volume: float = 1.0
        self._playback_positions: dict = {}
        self._stream = None

    def set_stems(self, stems: List[Stem]):
        """Replace the stems list atomically."""
        self._stems = list(stems)
        # Initialize playback positions for new stems
        for stem in self._stems:
            if id(stem) not in self._playback_positions:
                self._playback_positions[id(stem)] = 0.0

    def set_bpm(self, bpm: float):
        self._bpm = bpm

    def set_master_volume(self, volume: float):
        self._master_volume = max(0.0, min(1.0, volume))

    @property
    def bpm(self) -> float:
        return self._bpm

    @property
    def master_volume(self) -> float:
        return self._master_volume

    def _generate_block(self, n_frames: int) -> np.ndarray:
        """Generate a block of mixed audio.

        This is the core mixing function, called by the audio callback
        or directly in tests. No audio hardware needed.
        """
        output = np.zeros(n_frames, dtype=np.float32)
        stems = self._stems  # snapshot
        bpm = self._bpm

        # Check if any stem has solo enabled
        any_solo = any(s.solo for s in stems)

        for stem in stems:
            if stem.audio_data is None or stem.sample_rate is None:
                continue

            # Solo/mute logic
            if any_solo and not stem.solo:
                continue

            vol = stem.volume_at_bpm(bpm)
            if vol < 1e-7:
                continue

            # Resampling ratio: how fast to consume source samples
            ratio = bpm / stem.base_bpm
            pos = self._playback_positions.get(id(stem), 0.0)
            audio = stem.audio_data
            audio_len = len(audio)

            # Compute source sample positions for this block
            source_positions = pos + np.arange(n_frames, dtype=np.float64) * ratio
            # Wrap for looping
            source_positions = source_positions % audio_len

            # Resample via linear interpolation
            indices = np.arange(audio_len, dtype=np.float64)
            # np.interp handles wrapping if we use the modulo'd positions
            resampled = np.interp(source_positions, indices, audio)

            output += resampled.astype(np.float32) * vol

            # Update playback position
            new_pos = (pos + n_frames * ratio) % audio_len
            self._playback_positions[id(stem)] = new_pos

        # Apply master volume and clip
        output *= self._master_volume
        np.clip(output, -1.0, 1.0, out=output)

        return output

    def _audio_callback(self, outdata, frames, time_info, status):
        """sounddevice OutputStream callback."""
        block = self._generate_block(frames)
        outdata[:, 0] = block

    def start(self):
        """Start audio playback."""
        import sounddevice as sd

        self._stream = sd.OutputStream(
            samplerate=self._sample_rate,
            channels=1,
            blocksize=self._block_size,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        """Stop audio playback."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def reset_positions(self):
        """Reset all playback positions to the start."""
        self._playback_positions.clear()
