"""Tests for stem definition schema and set generator."""

import json
from pathlib import Path

import pytest

from soundscape.stem_definition import (
    EnergyProfile,
    ListenerContext,
    MixHints,
    MoodProfile,
    MusicalInfo,
    PackDefinition,
    RoleInfo,
    SonicProfile,
    StemDefinition,
    TransitionHints,
    load_all_packs,
    load_pack,
)
from soundscape.set_generator import (
    RunPhase,
    RunPlan,
    SetTimeline,
    StemActivation,
    SetSegment,
    build_messages,
    build_prompt,
    parse_timeline_response,
    validate_timeline,
    EXAMPLE_EASY_RUN,
    EXAMPLE_TEMPO_RUN,
)


STEMS_DIR = Path(__file__).parent.parent / "stems"


# ---------------------------------------------------------------------------
# StemDefinition round-trip
# ---------------------------------------------------------------------------

def _make_stem_def() -> StemDefinition:
    return StemDefinition(
        id="test_pad",
        file="test_pad.wav",
        musical=MusicalInfo(key="Am", bpm=120, duration_s=16.0),
        role=RoleInfo(type="harmonic", layer="mid", function="foundation"),
        energy=EnergyProfile(intensity=0.4, drive=0.2, groove=0.3),
        mood=MoodProfile(tags=["calm", "warm"], valence=0.6, arousal=0.3),
        sonic=SonicProfile(brightness=0.5, density=0.4, space=0.7, warmth=0.8),
    )


def test_stem_definition_roundtrip():
    original = _make_stem_def()
    d = original.to_dict()
    restored = StemDefinition.from_dict(d)

    assert restored.id == original.id
    assert restored.musical.key == "Am"
    assert restored.energy.intensity == 0.4
    assert restored.mood.tags == ["calm", "warm"]
    assert restored.sonic.warmth == 0.8


def test_stem_definition_json_roundtrip():
    original = _make_stem_def()
    json_str = json.dumps(original.to_dict())
    restored = StemDefinition.from_dict(json.loads(json_str))
    assert restored.id == original.id
    assert restored.role.type == "harmonic"


def test_stem_definition_defaults():
    stem = _make_stem_def()
    assert stem.mix_hints.pairs_well_with == []
    assert stem.mix_hints.solo_capable is False
    assert stem.transition_hints.fade_in_beats == 8
    assert stem.listener_context.best_for == []


# ---------------------------------------------------------------------------
# PackDefinition round-trip
# ---------------------------------------------------------------------------

def _make_pack_def() -> PackDefinition:
    return PackDefinition(
        pack="test_pack",
        genre="test_genre",
        mood_summary="A test pack",
        key_center="Am",
        bpm_center=120,
        energy_range=[0.2, 0.8],
        best_for_phases=["easy_run"],
        stems=[_make_stem_def()],
    )


def test_pack_definition_roundtrip():
    original = _make_pack_def()
    d = original.to_dict()
    restored = PackDefinition.from_dict(d)

    assert restored.pack == "test_pack"
    assert len(restored.stems) == 1
    assert restored.stems[0].id == "test_pad"
    assert restored.energy_range == [0.2, 0.8]


# ---------------------------------------------------------------------------
# Loading from disk
# ---------------------------------------------------------------------------

def test_load_forest_pack():
    pack = load_pack(STEMS_DIR / "forest" / "definitions.json")
    assert pack.pack == "forest"
    assert pack.genre == "organic_electronic"
    assert len(pack.stems) == 8
    stem_ids = {s.id for s in pack.stems}
    assert "forest_marimba" in stem_ids
    assert "forest_drone" in stem_ids


def test_load_all_packs():
    packs = load_all_packs(STEMS_DIR)
    pack_names = {p.pack for p in packs}
    assert "forest" in pack_names
    assert "neon" in pack_names
    assert "midnight" in pack_names
    assert "dynamic" in pack_names


def test_all_packs_have_stems():
    packs = load_all_packs(STEMS_DIR)
    for pack in packs:
        assert len(pack.stems) > 0, f"Pack '{pack.pack}' has no stems"


def test_all_stems_have_required_fields():
    packs = load_all_packs(STEMS_DIR)
    for pack in packs:
        for stem in pack.stems:
            assert stem.id, f"Stem missing id in pack '{pack.pack}'"
            assert stem.file, f"Stem '{stem.id}' missing file"
            assert stem.musical.bpm > 0
            assert 0 <= stem.energy.intensity <= 1
            assert 0 <= stem.energy.drive <= 1
            assert 0 <= stem.energy.groove <= 1
            assert 0 <= stem.mood.valence <= 1
            assert 0 <= stem.mood.arousal <= 1


def test_stem_files_exist_on_disk():
    packs = load_all_packs(STEMS_DIR)
    for pack in packs:
        pack_dir = STEMS_DIR / pack.pack
        for stem in pack.stems:
            wav_path = pack_dir / stem.file
            assert wav_path.exists(), (
                f"Stem file '{stem.file}' not found in {pack_dir}"
            )


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def test_build_prompt_contains_stems():
    packs = load_all_packs(STEMS_DIR)
    prompt = build_prompt(packs, EXAMPLE_EASY_RUN)
    assert "forest_marimba" in prompt
    assert "neon_lead" in prompt
    assert "warmup" in prompt


def test_build_messages_structure():
    packs = load_all_packs(STEMS_DIR)
    messages = build_messages(packs, EXAMPLE_EASY_RUN)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Stem Library" in messages[1]["content"]


# ---------------------------------------------------------------------------
# Timeline parsing & validation
# ---------------------------------------------------------------------------

SAMPLE_TIMELINE_JSON = json.dumps({
    "total_duration_min": 30,
    "packs_used": ["forest"],
    "reasoning": "Test timeline",
    "segments": [
        {
            "phase_name": "warmup",
            "start_min": 0,
            "end_min": 5,
            "target_bpm": None,
            "notes": "",
            "active_stems": [
                {
                    "stem_id": "forest_texture",
                    "start_min": 0,
                    "end_min": 5,
                    "volume": 0.8,
                    "fade_in_beats": 16,
                    "fade_out_beats": 8,
                },
                {
                    "stem_id": "forest_drone",
                    "start_min": 0,
                    "end_min": 5,
                    "volume": 0.6,
                    "fade_in_beats": 16,
                    "fade_out_beats": 8,
                },
            ],
        },
        {
            "phase_name": "easy_run",
            "start_min": 5,
            "end_min": 25,
            "target_bpm": None,
            "notes": "",
            "active_stems": [
                {
                    "stem_id": "forest_pad",
                    "start_min": 5,
                    "end_min": 25,
                    "volume": 0.7,
                    "fade_in_beats": 8,
                    "fade_out_beats": 8,
                },
                {
                    "stem_id": "forest_marimba",
                    "start_min": 5,
                    "end_min": 25,
                    "volume": 0.6,
                    "fade_in_beats": 8,
                    "fade_out_beats": 4,
                },
            ],
        },
        {
            "phase_name": "cooldown",
            "start_min": 25,
            "end_min": 30,
            "target_bpm": None,
            "notes": "",
            "active_stems": [
                {
                    "stem_id": "forest_texture",
                    "start_min": 25,
                    "end_min": 30,
                    "volume": 0.5,
                    "fade_in_beats": 8,
                    "fade_out_beats": 16,
                },
                {
                    "stem_id": "forest_drone",
                    "start_min": 25,
                    "end_min": 30,
                    "volume": 0.4,
                    "fade_in_beats": 8,
                    "fade_out_beats": 16,
                },
            ],
        },
    ],
})


def test_parse_timeline():
    timeline = parse_timeline_response(SAMPLE_TIMELINE_JSON)
    assert timeline.total_duration_min == 30
    assert len(timeline.segments) == 3
    assert timeline.segments[0].phase_name == "warmup"
    assert len(timeline.segments[0].active_stems) == 2


def test_parse_timeline_with_code_fences():
    fenced = f"```json\n{SAMPLE_TIMELINE_JSON}\n```"
    timeline = parse_timeline_response(fenced)
    assert timeline.total_duration_min == 30


def test_validate_valid_timeline():
    packs = load_all_packs(STEMS_DIR)
    timeline = parse_timeline_response(SAMPLE_TIMELINE_JSON)
    errors = validate_timeline(timeline, packs)
    assert errors == [], f"Unexpected errors: {errors}"


def test_validate_catches_conflict():
    packs = load_all_packs(STEMS_DIR)
    bad_timeline = SetTimeline(
        total_duration_min=5,
        packs_used=["forest"],
        segments=[
            SetSegment(
                phase_name="easy_run",
                start_min=0,
                end_min=5,
                target_bpm=None,
                active_stems=[
                    StemActivation("forest_clicks", 0, 5),
                    StemActivation("forest_shaker", 0, 5),  # conflicts_with clicks
                ],
            ),
        ],
    )
    errors = validate_timeline(bad_timeline, packs)
    assert any("conflict" in e for e in errors)


def test_validate_catches_key_clash():
    packs = load_all_packs(STEMS_DIR)
    # forest (Cm) + neon (F#m) stems with high key confidence
    bad_timeline = SetTimeline(
        total_duration_min=5,
        packs_used=["forest", "neon"],
        segments=[
            SetSegment(
                phase_name="easy_run",
                start_min=0,
                end_min=5,
                target_bpm=None,
                active_stems=[
                    StemActivation("forest_marimba", 0, 5),  # Cm, conf 0.9
                    StemActivation("neon_arp", 0, 5),         # F#m, conf 0.95
                ],
            ),
        ],
    )
    errors = validate_timeline(bad_timeline, packs)
    assert any("key" in e.lower() or "clash" in e.lower() for e in errors)


def test_validate_catches_avoid_for():
    packs = load_all_packs(STEMS_DIR)
    bad_timeline = SetTimeline(
        total_duration_min=5,
        packs_used=["midnight"],
        segments=[
            SetSegment(
                phase_name="cooldown",
                start_min=0,
                end_min=5,
                target_bpm=None,
                active_stems=[
                    StemActivation("midnight_kick", 0, 5),  # avoid cooldown
                    StemActivation("midnight_hat", 0, 5),   # avoid cooldown
                ],
            ),
        ],
    )
    errors = validate_timeline(bad_timeline, packs)
    assert any("avoided" in e for e in errors)


def test_timeline_roundtrip():
    timeline = parse_timeline_response(SAMPLE_TIMELINE_JSON)
    d = timeline.to_dict()
    restored = SetTimeline.from_dict(d)
    assert restored.total_duration_min == timeline.total_duration_min
    assert len(restored.segments) == len(timeline.segments)
