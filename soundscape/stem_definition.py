"""Semantic stem and pack definitions for AI-driven mix generation.

These definitions describe *what a stem sounds like* so an AI can reason
about music the way a DJ does — mood, energy, harmonic compatibility,
and listener experience.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class MusicalInfo:
    """Harmonic and rhythmic identity."""
    key: str                          # e.g. "Cm", "F#m", "none"
    bpm: float
    scale: str = "chromatic"          # e.g. "minor_pentatonic", "dorian"
    time_signature: str = "4/4"
    duration_s: float = 0.0
    loopable: bool = True
    key_confidence: float = 1.0       # 0-1, low = harmonically neutral


@dataclass
class RoleInfo:
    """What this stem does in a mix."""
    type: str       # rhythmic | melodic | textural | harmonic | percussive
    layer: str      # low | mid | high | full
    function: str   # foundation | hook | fill | accent | atmosphere | drive


@dataclass
class EnergyProfile:
    """Numeric intensity profile — maps to running effort."""
    intensity: float   # 0-1 overall energy
    drive: float       # 0-1 perceived push / forward momentum
    groove: float      # 0-1 rhythmic pull / body-movement factor


@dataclass
class MoodProfile:
    """Emotional character using circumplex model."""
    tags: List[str]
    valence: float     # 0-1, negative to positive emotion
    arousal: float     # 0-1, calm to excited


@dataclass
class SonicProfile:
    """Timbral qualities for mix balancing."""
    brightness: float  # 0-1
    density: float     # 0-1
    space: float       # 0-1, how much reverb/stereo width
    warmth: float      # 0-1


@dataclass
class MixHints:
    """Explicit compatibility rules."""
    pairs_well_with: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    solo_capable: bool = False
    intro_suitable: bool = False
    climax_suitable: bool = False


@dataclass
class TransitionHints:
    """How this stem should enter and exit a mix."""
    fade_in_beats: int = 8
    fade_out_beats: int = 4
    entry_point: str = "downbeat"     # downbeat | any | pickup
    exit_style: str = "fade"          # fade | cut | filter_sweep


@dataclass
class ListenerContext:
    """Activity-phase mapping for running."""
    best_for: List[str] = field(default_factory=list)   # warmup, easy_run, tempo, interval_peak, cooldown, sprint
    avoid_for: List[str] = field(default_factory=list)


@dataclass
class StemDefinition:
    """Complete semantic definition of a single audio stem."""
    id: str
    file: str
    musical: MusicalInfo
    role: RoleInfo
    energy: EnergyProfile
    mood: MoodProfile
    sonic: SonicProfile
    mix_hints: MixHints = field(default_factory=MixHints)
    transition_hints: TransitionHints = field(default_factory=TransitionHints)
    listener_context: ListenerContext = field(default_factory=ListenerContext)

    def to_dict(self) -> dict:
        """Serialize to a plain dict for JSON export / AI prompt injection."""
        def _dc_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: _dc_to_dict(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [_dc_to_dict(i) for i in obj]
            return obj
        return _dc_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> StemDefinition:
        return cls(
            id=d["id"],
            file=d["file"],
            musical=MusicalInfo(**d["musical"]),
            role=RoleInfo(**d["role"]),
            energy=EnergyProfile(**d["energy"]),
            mood=MoodProfile(**d["mood"]),
            sonic=SonicProfile(**d["sonic"]),
            mix_hints=MixHints(**d.get("mix_hints", {})),
            transition_hints=TransitionHints(**d.get("transition_hints", {})),
            listener_context=ListenerContext(**d.get("listener_context", {})),
        )


@dataclass
class PackDefinition:
    """Collection-level metadata for a stem pack."""
    pack: str
    genre: str
    mood_summary: str
    key_center: str
    bpm_center: float
    energy_range: List[float]              # [min, max]
    best_for_phases: List[str]
    stems: List[StemDefinition] = field(default_factory=list)
    cross_pack_compatible_with: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def _dc_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: _dc_to_dict(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [_dc_to_dict(i) for i in obj]
            return obj
        return _dc_to_dict(self)

    @classmethod
    def from_dict(cls, d: dict) -> PackDefinition:
        stems = [StemDefinition.from_dict(s) for s in d.get("stems", [])]
        return cls(
            pack=d["pack"],
            genre=d["genre"],
            mood_summary=d["mood_summary"],
            key_center=d["key_center"],
            bpm_center=d["bpm_center"],
            energy_range=d["energy_range"],
            best_for_phases=d["best_for_phases"],
            stems=stems,
            cross_pack_compatible_with=d.get("cross_pack_compatible_with", []),
        )


def load_pack(path: str | Path) -> PackDefinition:
    """Load a pack definition from a JSON file."""
    with open(path) as f:
        return PackDefinition.from_dict(json.load(f))


def load_all_packs(stems_dir: str | Path) -> List[PackDefinition]:
    """Discover and load all pack definitions under a stems directory."""
    stems_dir = Path(stems_dir)
    packs = []
    for defn_file in sorted(stems_dir.glob("*/definitions.json")):
        packs.append(load_pack(defn_file))
    return packs
