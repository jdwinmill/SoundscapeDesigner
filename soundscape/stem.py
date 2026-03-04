from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class Stem:
    """A single audio stem with a trapezoidal BPM-volume curve.

    Volume curve shape:
    1.0  |        ___________
         |       /           \\
    0.0  |_____/               \\________
             A  B           C  D

    A = bpm_low - fade_in
    B = bpm_low
    C = bpm_high
    D = bpm_high + fade_out
    """

    bpm_low: float
    bpm_high: float
    fade_in: float = 5.0
    fade_out: float = 5.0
    volume: float = 1.0
    base_bpm: float = 150.0
    speed: float = 1.0
    muted: bool = False
    solo: bool = False
    file_path: Optional[str] = None
    audio_data: Optional[np.ndarray] = field(default=None, repr=False)
    sample_rate: Optional[int] = None

    def volume_at_bpm(self, bpm: float) -> float:
        """Compute the volume for this stem at a given BPM."""
        if self.muted:
            return 0.0

        a = self.bpm_low - self.fade_in
        b = self.bpm_low
        c = self.bpm_high
        d = self.bpm_high + self.fade_out

        if bpm < a:
            curve = 0.0
        elif bpm < b:
            # fade-in zone
            if self.fade_in == 0:
                curve = 0.0
            else:
                curve = (bpm - a) / (b - a)
        elif bpm <= c:
            curve = 1.0
        elif bpm < d:
            # fade-out zone
            if self.fade_out == 0:
                curve = 0.0
            else:
                curve = 1.0 - (bpm - c) / (d - c)
        else:
            curve = 0.0

        return curve * self.volume

    @classmethod
    def from_file(cls, path: str, **kwargs) -> "Stem":
        """Load a stem from a wav file."""
        import soundfile as sf

        data, sr = sf.read(path, dtype="float32")
        # Ensure mono (mix down if stereo)
        if data.ndim > 1:
            data = data.mean(axis=1)
        return cls(file_path=path, audio_data=data, sample_rate=sr, **kwargs)
