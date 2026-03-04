import json
import os
from dataclasses import dataclass
from typing import List

from soundscape.stem import Stem


@dataclass
class SoundscapeConfig:
    """Manages export/import of soundscape configurations for iOS.

    Export format:
    {
        "baseBPM": 150.0,
        "stems": [{
            "file": "march.wav",
            "bpmRange": [100, 140],
            "fadeIn": 5,
            "fadeOut": 10,
            "volume": 0.8
        }]
    }
    """

    base_bpm: float
    stems: List[Stem]

    def export(self, path: str) -> None:
        """Export configuration to a JSON file."""
        data = {
            "baseBPM": self.base_bpm,
            "stems": [self._stem_to_dict(s) for s in self.stems],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> "SoundscapeConfig":
        """Load configuration from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        base_bpm = data["baseBPM"]
        stems = [cls._dict_to_stem(s, base_bpm) for s in data["stems"]]
        return cls(base_bpm=base_bpm, stems=stems)

    def _stem_to_dict(self, stem: Stem) -> dict:
        filename = os.path.basename(stem.file_path) if stem.file_path else ""
        d = {
            "file": filename,
            "bpmRange": [stem.bpm_low, stem.bpm_high],
            "fadeIn": stem.fade_in,
            "fadeOut": stem.fade_out,
            "volume": stem.volume,
        }
        # Only include per-stem baseBPM if it differs from the global value
        if stem.base_bpm != self.base_bpm:
            d["baseBPM"] = stem.base_bpm
        if stem.speed != 1.0:
            d["speed"] = stem.speed
        return d

    @staticmethod
    def _dict_to_stem(d: dict, global_base_bpm: float = 150.0) -> Stem:
        bpm_range = d["bpmRange"]
        return Stem(
            bpm_low=bpm_range[0],
            bpm_high=bpm_range[1],
            fade_in=d.get("fadeIn", 5.0),
            fade_out=d.get("fadeOut", 5.0),
            volume=d.get("volume", 1.0),
            file_path=d.get("file"),
            base_bpm=d.get("baseBPM", global_base_bpm),
            speed=d.get("speed", 1.0),
        )
