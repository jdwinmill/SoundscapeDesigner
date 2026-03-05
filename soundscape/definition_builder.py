"""Stem Definition Builder — GUI for creating and editing pack definitions.

Provides a full-page tab inside the DearPyGui app where users can add audio
files, fill out all stem metadata via dropdowns/sliders/checkboxes, and save
the result as a ``definitions.json`` pack that the Designer tab can consume.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import dearpygui.dearpygui as dpg

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
    load_pack,
)

STEMS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stems")

# ── Dropdown constants ────────────────────────────────────────────
ROLE_TYPES = ["rhythmic", "melodic", "textural", "harmonic", "percussive"]
LAYERS = ["low", "mid", "high", "full"]
FUNCTIONS = ["foundation", "hook", "fill", "accent", "atmosphere", "drive"]
SCALES = [
    "chromatic", "major", "minor", "aeolian", "dorian", "mixolydian",
    "phrygian", "lydian", "minor_pentatonic", "major_pentatonic",
    "blues", "harmonic_minor", "whole_tone", "none",
]
KEYS = [
    "none", "C", "Cm", "C#", "C#m", "D", "Dm", "D#", "D#m",
    "E", "Em", "F", "Fm", "F#", "F#m", "G", "Gm",
    "G#", "G#m", "A", "Am", "A#", "A#m", "B", "Bm",
]
TIME_SIGNATURES = ["4/4", "3/4", "6/8", "5/4", "7/8"]
ENTRY_POINTS = ["downbeat", "any", "pickup"]
EXIT_STYLES = ["fade", "cut", "filter_sweep"]
LISTENER_PHASES = ["warmup", "easy_run", "tempo", "interval_peak", "sprint", "cooldown"]

# Mood tag presets
MOOD_PRESETS = [
    "peaceful", "natural", "ambient", "deep", "grounding", "steady",
    "warm", "evolving", "lush", "serene", "organic", "playful",
    "light", "propulsive", "earthy", "energetic", "driving",
    "ethereal", "uplifting", "sparkling", "dark", "aggressive",
    "melancholy", "euphoric", "mysterious", "triumphant",
]


class DefinitionBuilder:
    """Full UI and logic for the Stem Definitions builder tab."""

    def __init__(self, accent_theme, danger_theme):
        self._accent_theme = accent_theme
        self._danger_theme = danger_theme
        self._stem_widgets: Dict[int, dict] = {}
        self._next_stem_id = 0
        self._pending_files: Dict[str, str] = {}  # stem_id_key -> original file path
        self._current_pack_name: Optional[str] = None
        # Track the tab tag for focus checking
        self.tab_tag = "def_tab"

    # ── Public ────────────────────────────────────────────────────

    def build(self, parent: int | str):
        """Build the full definition builder UI inside *parent*."""
        with dpg.child_window(parent=parent, border=False, tag="def_builder_root"):
            self._build_pack_controls()
            dpg.add_spacer(height=8)
            self._build_pack_metadata()
            dpg.add_spacer(height=8)
            self._build_stems_section()

    # ── Pack controls bar ─────────────────────────────────────────

    def _build_pack_controls(self):
        with dpg.group(horizontal=True):
            new_btn = dpg.add_button(label="New Pack", callback=self._on_new_pack)
            dpg.bind_item_theme(new_btn, self._accent_theme)

            dpg.add_spacer(width=12)
            dpg.add_text("Load:")
            dpg.add_combo(
                tag="def_load_combo",
                items=self._discover_packs(),
                default_value="",
                width=160,
                callback=self._on_load_pack,
            )

            dpg.add_spacer(width=12)
            dpg.add_text("Pack Name:")
            dpg.add_input_text(tag="def_pack_name", width=160)

            dpg.add_spacer(width=12)
            save_btn = dpg.add_button(label="Save Pack", callback=self._on_save_pack)
            dpg.bind_item_theme(save_btn, self._accent_theme)

            dpg.add_spacer(width=12)
            dpg.add_text("", tag="def_status_label", color=(99, 102, 241))

    # ── Pack metadata ─────────────────────────────────────────────

    def _build_pack_metadata(self):
        with dpg.collapsing_header(label="Pack Metadata", default_open=True):
            with dpg.group(horizontal=True):
                dpg.add_text("Genre:")
                dpg.add_input_text(tag="def_genre", width=200)
                dpg.add_spacer(width=16)
                dpg.add_text("Mood Summary:")
                dpg.add_input_text(tag="def_mood_summary", width=300)

            with dpg.group(horizontal=True):
                dpg.add_text("Key Center:")
                dpg.add_combo(tag="def_key_center", items=KEYS, default_value="none", width=100)
                dpg.add_spacer(width=16)
                dpg.add_text("BPM Center:")
                dpg.add_slider_float(
                    tag="def_bpm_center", default_value=150.0,
                    min_value=60.0, max_value=240.0, format="%.0f", width=200,
                )

            with dpg.group(horizontal=True):
                dpg.add_text("Energy Min:")
                dpg.add_slider_float(
                    tag="def_energy_min", default_value=0.0,
                    min_value=0.0, max_value=1.0, format="%.2f", width=160,
                )
                dpg.add_spacer(width=16)
                dpg.add_text("Energy Max:")
                dpg.add_slider_float(
                    tag="def_energy_max", default_value=1.0,
                    min_value=0.0, max_value=1.0, format="%.2f", width=160,
                )

            dpg.add_spacer(height=4)
            dpg.add_text("Best For Phases:")
            with dpg.group(horizontal=True):
                for phase in LISTENER_PHASES:
                    dpg.add_checkbox(label=phase, tag=f"def_phase_{phase}")

            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                dpg.add_text("Cross-Pack Compatible With:")
                dpg.add_input_text(
                    tag="def_cross_pack", width=300,
                    hint="comma-separated pack names",
                )

    # ── Stems section ─────────────────────────────────────────────

    def _build_stems_section(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Stems", color=(99, 102, 241))
            dpg.add_spacer(width=12)
            add_btn = dpg.add_button(
                label="+ Add Audio File", callback=self._on_add_audio_file,
            )
            dpg.bind_item_theme(add_btn, self._accent_theme)

        dpg.add_spacer(height=4)
        dpg.add_child_window(tag="def_stems_container", border=False, height=-1)

    # ── Single stem UI ────────────────────────────────────────────

    def _add_stem_ui(self, stem_id: int, filename: str, stem: Optional[StemDefinition] = None):
        """Add the full set of widgets for one stem definition."""
        tag_prefix = f"ds_{stem_id}"
        parent = "def_stems_container"

        label = filename if not stem else f"{stem.id} ({filename})"
        header_tag = f"{tag_prefix}_header"

        with dpg.collapsing_header(label=label, parent=parent, tag=header_tag, default_open=True):
            # ID & file
            with dpg.group(horizontal=True):
                dpg.add_text("ID:")
                default_id = stem.id if stem else Path(filename).stem
                dpg.add_input_text(tag=f"{tag_prefix}_id", default_value=default_id, width=200)
                dpg.add_spacer(width=16)
                dpg.add_text(f"File: {filename}", color=(140, 140, 160))

            # ── Musical ──
            with dpg.tree_node(label="Musical"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Key:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_key", items=KEYS, width=100,
                        default_value=stem.musical.key if stem else "none",
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Scale:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_scale", items=SCALES, width=140,
                        default_value=stem.musical.scale if stem else "chromatic",
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("BPM:")
                    dpg.add_input_float(
                        tag=f"{tag_prefix}_bpm", width=100,
                        default_value=stem.musical.bpm if stem else 150.0,
                    )
                with dpg.group(horizontal=True):
                    dpg.add_text("Time Sig:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_timesig", items=TIME_SIGNATURES, width=80,
                        default_value=stem.musical.time_signature if stem else "4/4",
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Duration (s):")
                    dpg.add_input_float(
                        tag=f"{tag_prefix}_duration", width=100,
                        default_value=stem.musical.duration_s if stem else 0.0,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_checkbox(
                        label="Loopable", tag=f"{tag_prefix}_loopable",
                        default_value=stem.musical.loopable if stem else True,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Key Confidence:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_key_conf", min_value=0.0, max_value=1.0,
                        format="%.2f", width=120,
                        default_value=stem.musical.key_confidence if stem else 1.0,
                    )

            # ── Role ──
            with dpg.tree_node(label="Role"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Type:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_role_type", items=ROLE_TYPES, width=120,
                        default_value=stem.role.type if stem else ROLE_TYPES[0],
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Layer:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_layer", items=LAYERS, width=100,
                        default_value=stem.role.layer if stem else LAYERS[0],
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Function:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_function", items=FUNCTIONS, width=120,
                        default_value=stem.role.function if stem else FUNCTIONS[0],
                    )

            # ── Energy ──
            with dpg.tree_node(label="Energy"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Intensity:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_intensity", min_value=0.0, max_value=1.0,
                        format="%.2f", width=140,
                        default_value=stem.energy.intensity if stem else 0.5,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Drive:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_drive", min_value=0.0, max_value=1.0,
                        format="%.2f", width=140,
                        default_value=stem.energy.drive if stem else 0.5,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Groove:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_groove", min_value=0.0, max_value=1.0,
                        format="%.2f", width=140,
                        default_value=stem.energy.groove if stem else 0.5,
                    )

            # ── Mood ──
            with dpg.tree_node(label="Mood"):
                dpg.add_text("Preset Tags:")
                with dpg.group(horizontal=True):
                    for i, tag_name in enumerate(MOOD_PRESETS[:13]):
                        checked = stem and tag_name in stem.mood.tags if stem else False
                        dpg.add_checkbox(
                            label=tag_name, tag=f"{tag_prefix}_mood_{tag_name}",
                            default_value=checked,
                        )
                with dpg.group(horizontal=True):
                    for tag_name in MOOD_PRESETS[13:]:
                        checked = stem and tag_name in stem.mood.tags if stem else False
                        dpg.add_checkbox(
                            label=tag_name, tag=f"{tag_prefix}_mood_{tag_name}",
                            default_value=checked,
                        )
                with dpg.group(horizontal=True):
                    dpg.add_text("Custom Tags:")
                    # Collect any tags from stem that aren't in presets
                    custom = ""
                    if stem:
                        custom = ", ".join(t for t in stem.mood.tags if t not in MOOD_PRESETS)
                    dpg.add_input_text(
                        tag=f"{tag_prefix}_mood_custom", width=300,
                        default_value=custom, hint="comma-separated",
                    )
                with dpg.group(horizontal=True):
                    dpg.add_text("Valence:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_valence", min_value=0.0, max_value=1.0,
                        format="%.2f", width=140,
                        default_value=stem.mood.valence if stem else 0.5,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Arousal:")
                    dpg.add_slider_float(
                        tag=f"{tag_prefix}_arousal", min_value=0.0, max_value=1.0,
                        format="%.2f", width=140,
                        default_value=stem.mood.arousal if stem else 0.5,
                    )

            # ── Sonic ──
            with dpg.tree_node(label="Sonic"):
                with dpg.group(horizontal=True):
                    for attr in ("brightness", "density", "space", "warmth"):
                        dpg.add_text(f"{attr.title()}:")
                        val = getattr(stem.sonic, attr) if stem else 0.5
                        dpg.add_slider_float(
                            tag=f"{tag_prefix}_{attr}", min_value=0.0, max_value=1.0,
                            format="%.2f", width=120, default_value=val,
                        )
                        dpg.add_spacer(width=8)

            # ── Mix Hints ──
            with dpg.tree_node(label="Mix Hints"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Pairs Well With:")
                    dpg.add_input_text(
                        tag=f"{tag_prefix}_pairs_with", width=300,
                        default_value=", ".join(stem.mix_hints.pairs_well_with) if stem else "",
                        hint="comma-separated stem IDs",
                    )
                with dpg.group(horizontal=True):
                    dpg.add_text("Conflicts With:")
                    dpg.add_input_text(
                        tag=f"{tag_prefix}_conflicts_with", width=300,
                        default_value=", ".join(stem.mix_hints.conflicts_with) if stem else "",
                        hint="comma-separated stem IDs",
                    )
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(
                        label="Solo Capable", tag=f"{tag_prefix}_solo_capable",
                        default_value=stem.mix_hints.solo_capable if stem else False,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_checkbox(
                        label="Intro Suitable", tag=f"{tag_prefix}_intro_suitable",
                        default_value=stem.mix_hints.intro_suitable if stem else False,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_checkbox(
                        label="Climax Suitable", tag=f"{tag_prefix}_climax_suitable",
                        default_value=stem.mix_hints.climax_suitable if stem else False,
                    )

            # ── Transition ──
            with dpg.tree_node(label="Transition"):
                with dpg.group(horizontal=True):
                    dpg.add_text("Fade In Beats:")
                    dpg.add_input_int(
                        tag=f"{tag_prefix}_fade_in_beats", width=80,
                        default_value=stem.transition_hints.fade_in_beats if stem else 8,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Fade Out Beats:")
                    dpg.add_input_int(
                        tag=f"{tag_prefix}_fade_out_beats", width=80,
                        default_value=stem.transition_hints.fade_out_beats if stem else 4,
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Entry Point:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_entry_point", items=ENTRY_POINTS, width=110,
                        default_value=stem.transition_hints.entry_point if stem else "downbeat",
                    )
                    dpg.add_spacer(width=8)
                    dpg.add_text("Exit Style:")
                    dpg.add_combo(
                        tag=f"{tag_prefix}_exit_style", items=EXIT_STYLES, width=120,
                        default_value=stem.transition_hints.exit_style if stem else "fade",
                    )

            # ── Listener Context ──
            with dpg.tree_node(label="Listener Context"):
                dpg.add_text("Best For:")
                with dpg.group(horizontal=True):
                    for phase in LISTENER_PHASES:
                        checked = stem and phase in stem.listener_context.best_for if stem else False
                        dpg.add_checkbox(
                            label=phase, tag=f"{tag_prefix}_best_{phase}",
                            default_value=checked,
                        )
                dpg.add_text("Avoid For:")
                with dpg.group(horizontal=True):
                    for phase in LISTENER_PHASES:
                        checked = stem and phase in stem.listener_context.avoid_for if stem else False
                        dpg.add_checkbox(
                            label=phase, tag=f"{tag_prefix}_avoid_{phase}",
                            default_value=checked,
                        )

            # Remove button
            dpg.add_spacer(height=4)
            rm_btn = dpg.add_button(
                label="Remove Stem", user_data=stem_id,
                callback=self._on_remove_stem,
            )
            dpg.bind_item_theme(rm_btn, self._danger_theme)

        self._stem_widgets[stem_id] = {
            "tag_prefix": tag_prefix,
            "filename": filename,
            "header_tag": header_tag,
        }

    # ── Collect data from widgets ─────────────────────────────────

    def _collect_stem_definition(self, stem_id: int) -> StemDefinition:
        p = self._stem_widgets[stem_id]["tag_prefix"]
        filename = self._stem_widgets[stem_id]["filename"]

        # Mood tags
        mood_tags = [t for t in MOOD_PRESETS if dpg.get_value(f"{p}_mood_{t}")]
        custom_raw = dpg.get_value(f"{p}_mood_custom").strip()
        if custom_raw:
            mood_tags.extend(t.strip() for t in custom_raw.split(",") if t.strip())

        return StemDefinition(
            id=dpg.get_value(f"{p}_id"),
            file=filename,
            musical=MusicalInfo(
                key=dpg.get_value(f"{p}_key"),
                bpm=dpg.get_value(f"{p}_bpm"),
                scale=dpg.get_value(f"{p}_scale"),
                time_signature=dpg.get_value(f"{p}_timesig"),
                duration_s=dpg.get_value(f"{p}_duration"),
                loopable=dpg.get_value(f"{p}_loopable"),
                key_confidence=dpg.get_value(f"{p}_key_conf"),
            ),
            role=RoleInfo(
                type=dpg.get_value(f"{p}_role_type"),
                layer=dpg.get_value(f"{p}_layer"),
                function=dpg.get_value(f"{p}_function"),
            ),
            energy=EnergyProfile(
                intensity=dpg.get_value(f"{p}_intensity"),
                drive=dpg.get_value(f"{p}_drive"),
                groove=dpg.get_value(f"{p}_groove"),
            ),
            mood=MoodProfile(
                tags=mood_tags,
                valence=dpg.get_value(f"{p}_valence"),
                arousal=dpg.get_value(f"{p}_arousal"),
            ),
            sonic=SonicProfile(
                brightness=dpg.get_value(f"{p}_brightness"),
                density=dpg.get_value(f"{p}_density"),
                space=dpg.get_value(f"{p}_space"),
                warmth=dpg.get_value(f"{p}_warmth"),
            ),
            mix_hints=MixHints(
                pairs_well_with=_split_csv(dpg.get_value(f"{p}_pairs_with")),
                conflicts_with=_split_csv(dpg.get_value(f"{p}_conflicts_with")),
                solo_capable=dpg.get_value(f"{p}_solo_capable"),
                intro_suitable=dpg.get_value(f"{p}_intro_suitable"),
                climax_suitable=dpg.get_value(f"{p}_climax_suitable"),
            ),
            transition_hints=TransitionHints(
                fade_in_beats=dpg.get_value(f"{p}_fade_in_beats"),
                fade_out_beats=dpg.get_value(f"{p}_fade_out_beats"),
                entry_point=dpg.get_value(f"{p}_entry_point"),
                exit_style=dpg.get_value(f"{p}_exit_style"),
            ),
            listener_context=ListenerContext(
                best_for=[ph for ph in LISTENER_PHASES if dpg.get_value(f"{p}_best_{ph}")],
                avoid_for=[ph for ph in LISTENER_PHASES if dpg.get_value(f"{p}_avoid_{ph}")],
            ),
        )

    def _collect_pack_definition(self) -> PackDefinition:
        pack_name = dpg.get_value("def_pack_name").strip()
        cross_raw = dpg.get_value("def_cross_pack").strip()

        stems = [
            self._collect_stem_definition(sid)
            for sid in sorted(self._stem_widgets.keys())
        ]

        return PackDefinition(
            pack=pack_name,
            genre=dpg.get_value("def_genre"),
            mood_summary=dpg.get_value("def_mood_summary"),
            key_center=dpg.get_value("def_key_center"),
            bpm_center=dpg.get_value("def_bpm_center"),
            energy_range=[dpg.get_value("def_energy_min"), dpg.get_value("def_energy_max")],
            best_for_phases=[ph for ph in LISTENER_PHASES if dpg.get_value(f"def_phase_{ph}")],
            stems=stems,
            cross_pack_compatible_with=_split_csv(cross_raw),
        )

    # ── Callbacks ─────────────────────────────────────────────────

    def _on_new_pack(self, sender=None, app_data=None):
        self._clear_all()
        dpg.set_value("def_status_label", "New pack created.")

    def _on_load_pack(self, sender, value):
        if not value:
            return
        defn_path = os.path.join(STEMS_DIR, value, "definitions.json")
        if not os.path.isfile(defn_path):
            dpg.set_value("def_status_label", f"No definitions.json in {value}")
            return
        try:
            pack = load_pack(defn_path)
        except Exception as e:
            dpg.set_value("def_status_label", f"Error: {e}")
            return

        self._clear_all()
        self._current_pack_name = pack.pack

        # Populate metadata
        dpg.set_value("def_pack_name", pack.pack)
        dpg.set_value("def_genre", pack.genre)
        dpg.set_value("def_mood_summary", pack.mood_summary)
        dpg.set_value("def_key_center", pack.key_center)
        dpg.set_value("def_bpm_center", pack.bpm_center)
        if len(pack.energy_range) >= 2:
            dpg.set_value("def_energy_min", pack.energy_range[0])
            dpg.set_value("def_energy_max", pack.energy_range[1])
        for phase in LISTENER_PHASES:
            dpg.set_value(f"def_phase_{phase}", phase in pack.best_for_phases)
        dpg.set_value("def_cross_pack", ", ".join(pack.cross_pack_compatible_with))

        # Populate stems
        for stem in pack.stems:
            sid = self._next_stem_id
            self._next_stem_id += 1
            self._add_stem_ui(sid, stem.file, stem=stem)
            # File already exists in pack dir — no pending copy needed

        dpg.set_value("def_status_label", f"Loaded: {pack.pack}")

    def _on_add_audio_file(self, sender=None, app_data=None):
        with dpg.file_dialog(
            label="Select Audio File",
            callback=self._do_add_audio_file,
            directory_selector=False,
            show=True,
            width=600,
            height=400,
        ):
            dpg.add_file_extension(".wav", color=(0, 255, 0, 255))
            dpg.add_file_extension(".aif", color=(0, 255, 0, 255))
            dpg.add_file_extension(".flac", color=(0, 255, 0, 255))

    def _do_add_audio_file(self, sender, app_data):
        if not app_data or "file_path_name" not in app_data:
            return
        file_path = app_data["file_path_name"]
        filename = os.path.basename(file_path)

        sid = self._next_stem_id
        self._next_stem_id += 1
        self._pending_files[str(sid)] = file_path
        self._add_stem_ui(sid, filename)

    def _on_remove_stem(self, sender, app_data, stem_id):
        info = self._stem_widgets.pop(stem_id, None)
        if info and dpg.does_item_exist(info["header_tag"]):
            dpg.delete_item(info["header_tag"])
        self._pending_files.pop(str(stem_id), None)

    def _on_save_pack(self, sender=None, app_data=None):
        pack_name = dpg.get_value("def_pack_name").strip()
        if not pack_name:
            dpg.set_value("def_status_label", "Error: Pack name is required.")
            return
        if not self._stem_widgets:
            dpg.set_value("def_status_label", "Error: Add at least one stem.")
            return

        pack_def = self._collect_pack_definition()
        pack_dir = os.path.join(STEMS_DIR, pack_name)
        os.makedirs(pack_dir, exist_ok=True)

        # Copy pending audio files
        for sid_key, src_path in self._pending_files.items():
            dst = os.path.join(pack_dir, os.path.basename(src_path))
            if os.path.abspath(src_path) != os.path.abspath(dst):
                shutil.copy2(src_path, dst)

        # Write definitions.json
        defn_path = os.path.join(pack_dir, "definitions.json")
        with open(defn_path, "w") as f:
            json.dump(pack_def.to_dict(), f, indent=2)

        self._pending_files.clear()
        self._current_pack_name = pack_name

        # Refresh the load combo
        dpg.configure_item("def_load_combo", items=self._discover_packs())

        dpg.set_value("def_status_label", f"Saved to stems/{pack_name}/definitions.json")

    # ── Helpers ───────────────────────────────────────────────────

    def _clear_all(self):
        """Reset all fields and remove all stem UIs."""
        # Remove stem widgets
        for info in self._stem_widgets.values():
            if dpg.does_item_exist(info["header_tag"]):
                dpg.delete_item(info["header_tag"])
        self._stem_widgets.clear()
        self._pending_files.clear()
        self._current_pack_name = None
        self._next_stem_id = 0

        # Reset metadata fields
        dpg.set_value("def_pack_name", "")
        dpg.set_value("def_genre", "")
        dpg.set_value("def_mood_summary", "")
        dpg.set_value("def_key_center", "none")
        dpg.set_value("def_bpm_center", 150.0)
        dpg.set_value("def_energy_min", 0.0)
        dpg.set_value("def_energy_max", 1.0)
        for phase in LISTENER_PHASES:
            dpg.set_value(f"def_phase_{phase}", False)
        dpg.set_value("def_cross_pack", "")
        dpg.set_value("def_status_label", "")

    @staticmethod
    def _discover_packs() -> List[str]:
        """Find existing pack directories that contain definitions.json."""
        packs = []
        if not os.path.isdir(STEMS_DIR):
            return packs
        for name in sorted(os.listdir(STEMS_DIR)):
            defn = os.path.join(STEMS_DIR, name, "definitions.json")
            if os.path.isfile(defn):
                packs.append(name)
        return packs


def _split_csv(text: str) -> List[str]:
    """Split a comma-separated string, stripping whitespace and empties."""
    return [t.strip() for t in text.split(",") if t.strip()]
