"""AI-driven set generator.

Takes stem definitions + a run plan and produces a structured timeline
that an AI can generate or that can be fed into the existing mixer.

This module:
1. Loads pack definitions from disk
2. Builds a structured prompt for an LLM
3. Defines the expected output schema (SetTimeline)
4. Provides parsing/validation of AI responses
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from soundscape.stem_definition import PackDefinition, load_all_packs


# ---------------------------------------------------------------------------
# Run plan & output schema
# ---------------------------------------------------------------------------

@dataclass
class RunPhase:
    """A single phase of a run."""
    name: str               # warmup | easy_run | tempo | interval_peak | sprint | cooldown
    duration_min: float
    target_bpm: Optional[float] = None
    target_energy: Optional[float] = None


@dataclass
class RunPlan:
    """Complete run plan the AI will design a set for."""
    total_duration_min: float
    phases: List[RunPhase]
    mood_arc: str = "uplifting_journey"         # descriptive label
    genre_preferences: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "total_duration_min": self.total_duration_min,
            "mood_arc": self.mood_arc,
            "genre_preferences": self.genre_preferences,
            "notes": self.notes,
            "phases": [
                {
                    "name": p.name,
                    "duration_min": p.duration_min,
                    "target_bpm": p.target_bpm,
                    "target_energy": p.target_energy,
                }
                for p in self.phases
            ],
        }


@dataclass
class StemActivation:
    """A single stem turning on/off in the timeline."""
    stem_id: str
    start_min: float
    end_min: float
    volume: float = 1.0
    fade_in_beats: int = 8
    fade_out_beats: int = 4


@dataclass
class SetSegment:
    """A segment of the set (maps to a run phase)."""
    phase_name: str
    start_min: float
    end_min: float
    target_bpm: Optional[float]
    active_stems: List[StemActivation]
    notes: str = ""


@dataclass
class SetTimeline:
    """Complete AI-generated set timeline."""
    segments: List[SetSegment]
    total_duration_min: float
    packs_used: List[str]
    reasoning: str = ""

    def to_dict(self) -> dict:
        return {
            "total_duration_min": self.total_duration_min,
            "packs_used": self.packs_used,
            "reasoning": self.reasoning,
            "segments": [
                {
                    "phase_name": s.phase_name,
                    "start_min": s.start_min,
                    "end_min": s.end_min,
                    "target_bpm": s.target_bpm,
                    "notes": s.notes,
                    "active_stems": [
                        {
                            "stem_id": a.stem_id,
                            "start_min": a.start_min,
                            "end_min": a.end_min,
                            "volume": a.volume,
                            "fade_in_beats": a.fade_in_beats,
                            "fade_out_beats": a.fade_out_beats,
                        }
                        for a in s.active_stems
                    ],
                }
                for s in self.segments
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> SetTimeline:
        segments = []
        for seg in d["segments"]:
            activations = [
                StemActivation(**a) for a in seg["active_stems"]
            ]
            segments.append(SetSegment(
                phase_name=seg["phase_name"],
                start_min=seg["start_min"],
                end_min=seg["end_min"],
                target_bpm=seg.get("target_bpm"),
                active_stems=activations,
                notes=seg.get("notes", ""),
            ))
        return cls(
            segments=segments,
            total_duration_min=d["total_duration_min"],
            packs_used=d["packs_used"],
            reasoning=d.get("reasoning", ""),
        )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert DJ and running coach. Your job is to create a music set \
timeline for someone to run to. You will be given:

1. A library of audio stems with semantic definitions describing their \
musical properties, energy, mood, sonic character, and suitability for \
different running phases.
2. A run plan describing the phases of the run (warmup, tempo, intervals, \
cooldown, etc.) with target durations and energy levels.

Your task is to select and layer stems across the timeline so the runner \
has a pleasant, motivating, and musically coherent experience.

## Rules

1. **Layer balance**: Each active segment should have stems covering \
different layers (low/mid/high) and roles (rhythmic/melodic/textural/harmonic). \
Don't stack multiple stems with the same role.function.
2. **Energy curve**: Match stem energy.intensity to the run phase. \
Warmup = low energy, peak = high energy, cooldown = wind down.
3. **Harmonic safety**: Only layer stems that share the same key or where \
at least one stem has key_confidence < 0.3 (harmonically neutral). \
Never layer stems in clashing keys.
4. **Respect conflicts**: Never activate stems that are listed in each \
other's mix_hints.conflicts_with at the same time.
5. **Respect listener_context**: Prefer stems whose listener_context.best_for \
includes the current phase. Never use stems whose avoid_for includes the \
current phase.
6. **Transitions**: When changing stems, respect transition_hints. \
Overlap fade-outs with fade-ins for smooth crossfades. Don't change \
more than 2 stems at once.
7. **Variety**: Don't loop the exact same stem combination for more than \
3-4 minutes. Rotate accents and hooks to maintain interest.
8. **Cross-pack mixing**: You may mix stems from different packs if their \
pack definitions list each other in cross_pack_compatible_with AND the \
individual stems are harmonically compatible.
9. **Coverage**: Every minute of the run should have at least 2 active stems.

## Output Format

Return ONLY valid JSON matching this schema:
```json
{
  "total_duration_min": <number>,
  "packs_used": [<pack names>],
  "reasoning": "<brief explanation of your mixing decisions>",
  "segments": [
    {
      "phase_name": "<run phase name>",
      "start_min": <number>,
      "end_min": <number>,
      "target_bpm": <number or null>,
      "notes": "<mixing notes for this segment>",
      "active_stems": [
        {
          "stem_id": "<stem id from definitions>",
          "start_min": <number>,
          "end_min": <number>,
          "volume": <0.0-1.0>,
          "fade_in_beats": <int>,
          "fade_out_beats": <int>
        }
      ]
    }
  ]
}
```
"""


def build_prompt(packs: List[PackDefinition], run_plan: RunPlan) -> str:
    """Build the complete user prompt with stem library and run plan."""
    # Stem library section
    library_data = []
    for pack in packs:
        library_data.append(pack.to_dict())

    sections = [
        "## Stem Library\n",
        "```json",
        json.dumps(library_data, indent=2),
        "```\n",
        "## Run Plan\n",
        "```json",
        json.dumps(run_plan.to_dict(), indent=2),
        "```\n",
        "Generate the set timeline now.",
    ]
    return "\n".join(sections)


def build_messages(packs: List[PackDefinition], run_plan: RunPlan) -> list[dict]:
    """Build the complete message list for an LLM API call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(packs, run_plan)},
    ]


# ---------------------------------------------------------------------------
# Response parsing & validation
# ---------------------------------------------------------------------------

def parse_timeline_response(response_text: str) -> SetTimeline:
    """Parse an LLM response into a SetTimeline.

    Handles responses that may include markdown code fences.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last fence lines
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    data = json.loads(text)
    return SetTimeline.from_dict(data)


def validate_timeline(timeline: SetTimeline, packs: List[PackDefinition]) -> List[str]:
    """Validate a generated timeline against the stem definitions.

    Returns a list of warning/error strings. Empty list = valid.
    """
    errors = []

    # Build lookup tables
    all_stems = {}
    for pack in packs:
        for stem in pack.stems:
            all_stems[stem.id] = stem

    pack_compat = {}
    for pack in packs:
        pack_compat[pack.pack] = set(pack.cross_pack_compatible_with)

    stem_to_pack = {}
    for pack in packs:
        for stem in pack.stems:
            stem_to_pack[stem.id] = pack.pack

    for seg in timeline.segments:
        active_ids = [a.stem_id for a in seg.active_stems]

        # Check all stems exist
        for sid in active_ids:
            if sid not in all_stems:
                errors.append(f"Segment '{seg.phase_name}': unknown stem '{sid}'")

        # Check coverage
        if len(active_ids) < 2:
            errors.append(
                f"Segment '{seg.phase_name}' at {seg.start_min}min: "
                f"fewer than 2 active stems"
            )

        # Check conflicts
        for i, sid_a in enumerate(active_ids):
            if sid_a not in all_stems:
                continue
            stem_a = all_stems[sid_a]
            for sid_b in active_ids[i + 1:]:
                if sid_b not in all_stems:
                    continue
                if sid_b in stem_a.mix_hints.conflicts_with:
                    errors.append(
                        f"Segment '{seg.phase_name}': conflict between "
                        f"'{sid_a}' and '{sid_b}'"
                    )

        # Check harmonic compatibility
        keyed_stems = [
            (sid, all_stems[sid])
            for sid in active_ids
            if sid in all_stems and all_stems[sid].musical.key_confidence >= 0.3
            and all_stems[sid].musical.key != "none"
        ]
        if len(keyed_stems) > 1:
            keys = set(s.musical.key for _, s in keyed_stems)
            if len(keys) > 1:
                errors.append(
                    f"Segment '{seg.phase_name}': multiple keys active "
                    f"({', '.join(keys)}) — potential clash"
                )

        # Check listener context
        for sid in active_ids:
            if sid not in all_stems:
                continue
            stem = all_stems[sid]
            if seg.phase_name in stem.listener_context.avoid_for:
                errors.append(
                    f"Segment '{seg.phase_name}': stem '{sid}' should be "
                    f"avoided for this phase"
                )

        # Check cross-pack compatibility
        packs_in_segment = set()
        for sid in active_ids:
            if sid in stem_to_pack:
                packs_in_segment.add(stem_to_pack[sid])
        if len(packs_in_segment) > 1:
            for p in packs_in_segment:
                others = packs_in_segment - {p}
                for other in others:
                    if other not in pack_compat.get(p, set()):
                        errors.append(
                            f"Segment '{seg.phase_name}': packs '{p}' and "
                            f"'{other}' are not cross-pack compatible"
                        )

    return errors


# ---------------------------------------------------------------------------
# Convenience: end-to-end
# ---------------------------------------------------------------------------

def generate_set(
    stems_dir: str | Path,
    run_plan: RunPlan,
    packs: Optional[List[PackDefinition]] = None,
) -> dict:
    """Build everything needed to call an LLM and generate a set.

    Returns a dict with:
        - messages: ready-to-send LLM messages
        - packs: loaded pack definitions (for later validation)
    """
    if packs is None:
        packs = load_all_packs(stems_dir)

    return {
        "messages": build_messages(packs, run_plan),
        "packs": packs,
    }


# ---------------------------------------------------------------------------
# Example run plans
# ---------------------------------------------------------------------------

EXAMPLE_EASY_RUN = RunPlan(
    total_duration_min=30,
    phases=[
        RunPhase("warmup", 5, target_energy=0.3),
        RunPhase("easy_run", 20, target_energy=0.5),
        RunPhase("cooldown", 5, target_energy=0.25),
    ],
    mood_arc="gentle_build_and_release",
    genre_preferences=["organic_electronic"],
    notes="Relaxed recovery run. Keep it chill.",
)

EXAMPLE_TEMPO_RUN = RunPlan(
    total_duration_min=45,
    phases=[
        RunPhase("warmup", 5, target_energy=0.3),
        RunPhase("easy_run", 10, target_energy=0.5),
        RunPhase("tempo", 15, target_energy=0.7),
        RunPhase("easy_run", 10, target_energy=0.5),
        RunPhase("cooldown", 5, target_energy=0.25),
    ],
    mood_arc="uplifting_journey",
    genre_preferences=["synthwave", "organic_electronic"],
    notes="Building to a strong tempo effort in the middle third.",
)

EXAMPLE_INTERVAL_RUN = RunPlan(
    total_duration_min=40,
    phases=[
        RunPhase("warmup", 5, target_energy=0.3),
        RunPhase("easy_run", 5, target_energy=0.5),
        RunPhase("interval_peak", 3, target_energy=0.9),
        RunPhase("easy_run", 3, target_energy=0.4),
        RunPhase("interval_peak", 3, target_energy=0.9),
        RunPhase("easy_run", 3, target_energy=0.4),
        RunPhase("interval_peak", 3, target_energy=0.9),
        RunPhase("easy_run", 3, target_energy=0.4),
        RunPhase("interval_peak", 3, target_energy=0.9),
        RunPhase("easy_run", 4, target_energy=0.4),
        RunPhase("cooldown", 5, target_energy=0.25),
    ],
    mood_arc="intense_intervals",
    genre_preferences=["dark_techno", "synthwave"],
    notes="4x3min intervals with 3min recovery. Go hard on peaks.",
)
