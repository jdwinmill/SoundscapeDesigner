"""Soundscape Designer — DearPyGui application.

Run with: python -m soundscape.app
"""

import glob
import os
from typing import Dict, List, Optional

import dearpygui.dearpygui as dpg
import numpy as np

from soundscape.config import SoundscapeConfig
from soundscape.mixer import Mixer
from soundscape.stem import Stem

STEMS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stems")

# Layout constants
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 800
PLOT_HEIGHT = 250
BPM_MIN = 60.0
BPM_MAX = 240.0

STEM_COLORS = [
    (66, 135, 245),
    (245, 166, 66),
    (66, 245, 96),
    (245, 66, 66),
    (180, 66, 245),
    (66, 245, 230),
    (245, 245, 66),
    (245, 66, 180),
]


class SoundscapeApp:
    def __init__(self):
        self.mixer = Mixer()
        self.stems: List[Stem] = []
        self.stem_widgets: Dict[int, dict] = {}  # stem id -> widget tags
        self.playing = False
        self._next_stem_id = 0
        self._presets: Dict[str, str] = self._discover_presets()

    @staticmethod
    def _discover_presets() -> Dict[str, str]:
        """Scan stems/ subdirectories for *_mix.json preset files."""
        presets: Dict[str, str] = {}
        pattern = os.path.join(STEMS_DIR, "**", "*_mix.json")
        for path in sorted(glob.glob(pattern, recursive=True)):
            # Use filename (without _mix.json) as the display label
            filename = os.path.basename(path)
            label = filename.replace("_mix.json", "").replace("_", " ").title()
            presets[label] = path
        return presets

    def run(self):
        dpg.create_context()
        dpg.create_viewport(
            title="Soundscape Designer",
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
        )

        with dpg.window(tag="primary", label="Soundscape Designer"):
            self._build_top_controls()
            dpg.add_spacer(height=8)
            self._build_stem_list()
            dpg.add_spacer(height=8)
            self._build_plot()

        self._register_keyboard_shortcuts()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

        # Cleanup audio on exit
        self.mixer.stop()

    def _build_top_controls(self):
        # -- Transport --
        dpg.add_text("Transport")
        with dpg.group(horizontal=True):
            play_btn = dpg.add_button(
                tag="play_btn",
                label="Play",
                callback=self._on_play_stop,
            )
            with dpg.tooltip(play_btn):
                dpg.add_text("Start/stop playback (Space)")

            reset_btn = dpg.add_button(
                label="Restart",
                callback=self._on_reset,
            )
            with dpg.tooltip(reset_btn):
                dpg.add_text("Restart all stems from the beginning")

            dpg.add_spacer(width=24)
            dpg.add_text("Master:")
            tag_master = dpg.add_slider_float(
                tag="master_vol_slider",
                default_value=1.0,
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
                width=160,
                callback=self._on_master_vol_change,
            )
            with dpg.tooltip(tag_master):
                dpg.add_text("Global output level")

        dpg.add_spacer(height=4)

        # -- Tempo --
        dpg.add_text("Tempo")
        with dpg.group(horizontal=True):
            dpg.add_text("Current BPM:")
            tag_bpm = dpg.add_slider_float(
                tag="bpm_slider",
                default_value=150.0,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=300,
                callback=self._on_bpm_change,
            )
            with dpg.tooltip(tag_bpm):
                dpg.add_text("Simulated running tempo — drag or use arrow keys")

            dpg.add_spacer(width=16)
            dpg.add_text("Base BPM:")
            tag_base = dpg.add_slider_float(
                tag="base_bpm_slider",
                default_value=150.0,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=200,
                callback=self._on_base_bpm_change,
            )
            with dpg.tooltip(tag_base):
                dpg.add_text("Native tempo the audio stems were recorded at")

        dpg.add_spacer(height=4)

        # -- File I/O --
        dpg.add_text("Config")
        with dpg.group(horizontal=True):
            export_btn = dpg.add_button(label="Export JSON", callback=self._on_export)
            with dpg.tooltip(export_btn):
                dpg.add_text("Save stem config for the iOS app (Ctrl+E)")

            load_btn = dpg.add_button(label="Load JSON", callback=self._on_import)
            with dpg.tooltip(load_btn):
                dpg.add_text("Load a previously saved config (Ctrl+L)")

            dpg.add_spacer(width=24)
            dpg.add_text("Preset:")
            preset_names = list(self._presets.keys())
            if preset_names:
                preset_combo = dpg.add_combo(
                    tag="preset_combo",
                    items=preset_names,
                    default_value="",
                    width=180,
                    callback=self._on_preset_select,
                )
                with dpg.tooltip(preset_combo):
                    dpg.add_text("Load a bundled soundscape preset")

    def _build_stem_list(self):
        with dpg.group(horizontal=True):
            dpg.add_text("Stems")
            dpg.add_text("(0)", tag="stem_count_label")
            dpg.add_spacer(width=8)
            dpg.add_button(label="+ Add Stem", callback=self._on_add_stem)
            dpg.add_spacer(width=8)
            sort_asc = dpg.add_button(label="Sort BPM Asc", callback=self._on_sort_bpm_asc)
            with dpg.tooltip(sort_asc):
                dpg.add_text("Sort stems by BPM low, ascending")
            sort_desc = dpg.add_button(label="Sort BPM Desc", callback=self._on_sort_bpm_desc)
            with dpg.tooltip(sort_desc):
                dpg.add_text("Sort stems by BPM low, descending")
        dpg.add_child_window(
            tag="stem_list",
            height=280,
            border=True,
        )
        dpg.add_text(
            "No stems loaded. Click '+ Add Stem' to load an audio file.",
            tag="stem_empty_hint",
            parent="stem_list",
            color=(160, 160, 160),
        )

    def _build_stem_table(self):
        """Create the stem table inside stem_list. Called once, rows added later."""
        if dpg.does_item_exist("stem_table"):
            dpg.delete_item("stem_table")

        with dpg.table(
            tag="stem_table",
            parent="stem_list",
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            resizable=True,
        ):
            dpg.add_table_column(label="Name", width_fixed=True, init_width_or_weight=140)
            dpg.add_table_column(label="S", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="M", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="Volume", width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label="Base BPM", width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label="BPM Low", width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label="BPM High", width_fixed=True, init_width_or_weight=100)
            dpg.add_table_column(label="Fade In", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Fade Out", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Actions", width_fixed=True, init_width_or_weight=180)

    def _build_plot(self):
        with dpg.plot(
            tag="curve_plot",
            label="Volume Curves",
            height=PLOT_HEIGHT,
            width=-1,
        ):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="BPM", tag="x_axis")
            dpg.set_axis_limits("x_axis", BPM_MIN, BPM_MAX)
            dpg.add_plot_axis(dpg.mvYAxis, label="Volume", tag="y_axis")
            dpg.set_axis_limits("y_axis", 0.0, 1.1)

            # Vertical line for current BPM
            dpg.add_vline_series(
                [150.0],
                tag="bpm_line",
                parent="y_axis",
            )

            # BPM readout annotation
            dpg.add_plot_annotation(
                tag="bpm_annotation",
                default_value=(150.0, 1.05),
                label="150.0",
                color=(255, 255, 255, 200),
                offset=(0, -15),
            )

    def _register_keyboard_shortcuts(self):
        with dpg.handler_registry():
            dpg.add_key_press_handler(
                dpg.mvKey_Spacebar,
                callback=self._on_key_space,
            )
            dpg.add_key_press_handler(
                dpg.mvKey_E,
                callback=self._on_key_e,
            )
            dpg.add_key_press_handler(
                dpg.mvKey_L,
                callback=self._on_key_l,
            )

    def _on_key_space(self):
        # Don't trigger if a text input is focused
        focused = dpg.get_active_window()
        self._on_play_stop()

    def _on_key_e(self):
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            self._on_export()

    def _on_key_l(self):
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            self._on_import()

    def _on_preset_select(self, sender, value):
        path = self._presets.get(value)
        if path:
            self._load_config_from_path(path)

    def _on_bpm_change(self, sender, value):
        self.mixer.set_bpm(value)
        self._update_plot()

    def _on_base_bpm_change(self, sender, value):
        for stem in self.stems:
            stem.base_bpm = value
        self._rebuild_stem_table()
        self._sync_stems()

    def _on_master_vol_change(self, sender, value):
        self.mixer.set_master_volume(value)

    def _on_play_stop(self, sender=None, app_data=None):
        if self.playing:
            self.mixer.stop()
            self.playing = False
            dpg.set_item_label("play_btn", "Play")
        else:
            self._sync_stems()
            self.mixer.start()
            self.playing = True
            dpg.set_item_label("play_btn", "Stop")

    def _on_reset(self):
        self.mixer.reset_positions()

    def _on_export(self, sender=None, app_data=None):
        with dpg.file_dialog(
            label="Export Soundscape Config",
            default_filename="soundscape.json",
            callback=self._do_export,
            directory_selector=False,
            show=True,
            width=600,
            height=400,
        ):
            dpg.add_file_extension(".json", color=(0, 255, 0, 255))

    def _do_export(self, sender, app_data):
        if not app_data or "file_path_name" not in app_data:
            return
        path = app_data["file_path_name"]
        base_bpm = dpg.get_value("base_bpm_slider")
        config = SoundscapeConfig(base_bpm=base_bpm, stems=self.stems)
        config.export(path)

    def _on_import(self, sender=None, app_data=None):
        with dpg.file_dialog(
            label="Load Soundscape Config",
            callback=self._do_import,
            directory_selector=False,
            show=True,
            width=600,
            height=400,
        ):
            dpg.add_file_extension(".json", color=(0, 255, 0, 255))

    def _do_import(self, sender, app_data):
        if not app_data or "file_path_name" not in app_data:
            return
        self._load_config_from_path(app_data["file_path_name"])

    def _load_config_from_path(self, path: str):
        json_dir = os.path.dirname(os.path.abspath(path))
        try:
            config = SoundscapeConfig.load(path)
        except Exception as e:
            print(f"Error loading config {path}: {e}")
            return

        # Clear existing stems and widgets
        self.stems.clear()
        self.stem_widgets.clear()

        # Set base BPM from config
        dpg.set_value("base_bpm_slider", config.base_bpm)

        # Rebuild stems from config, resolving audio files relative to the JSON
        for stem in config.stems:
            stem.base_bpm = config.base_bpm
            if stem.file_path and stem.audio_data is None:
                audio_path = os.path.join(json_dir, stem.file_path)
                if os.path.isfile(audio_path):
                    try:
                        loaded = Stem.from_file(
                            audio_path,
                            bpm_low=stem.bpm_low,
                            bpm_high=stem.bpm_high,
                            base_bpm=stem.base_bpm,
                            fade_in=stem.fade_in,
                            fade_out=stem.fade_out,
                            volume=stem.volume,
                        )
                        stem.file_path = audio_path
                        stem.audio_data = loaded.audio_data
                        stem.sample_rate = loaded.sample_rate
                    except Exception as e:
                        print(f"Could not load audio for {stem.file_path}: {e}")
            self.stems.append(stem)

        self._rebuild_stem_table()
        self._update_stem_count()
        self._sync_stems()
        self._update_plot()

    def _on_add_stem(self):
        with dpg.file_dialog(
            label="Select Audio File",
            callback=self._do_add_stem,
            directory_selector=False,
            show=True,
            width=600,
            height=400,
        ):
            dpg.add_file_extension(".wav", color=(0, 255, 0, 255))
            dpg.add_file_extension(".aif", color=(0, 255, 0, 255))
            dpg.add_file_extension(".flac", color=(0, 255, 0, 255))

    def _do_add_stem(self, sender, app_data):
        if not app_data or "file_path_name" not in app_data:
            return

        file_path = app_data["file_path_name"]
        base_bpm = dpg.get_value("base_bpm_slider")

        try:
            stem = Stem.from_file(
                file_path,
                bpm_low=120.0,
                bpm_high=160.0,
                base_bpm=base_bpm,
            )
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return

        self.stems.append(stem)
        stem_id = self._next_stem_id
        self._next_stem_id += 1
        self._ensure_stem_table()
        self._add_stem_row(stem, stem_id)
        self._update_stem_count()
        self._sync_stems()
        self._update_plot()

    def _ensure_stem_table(self):
        """Create the table if it doesn't exist yet."""
        if not dpg.does_item_exist("stem_table"):
            self._build_stem_table()

    def _add_stem_row(self, stem: Stem, stem_id: int, stem_index: int = -1):
        row_tag = f"stem_row_{stem_id}"
        has_audio = stem.audio_data is not None
        name = os.path.basename(stem.file_path) if stem.file_path else "???"
        if not has_audio:
            name += " (no audio)"

        if stem_index < 0:
            stem_index = len(self.stems) - 1
        color = STEM_COLORS[stem_index % len(STEM_COLORS)]

        with dpg.table_row(parent="stem_table", tag=row_tag):
            # Name (color-coded to match plot curve)
            dpg.add_text(name, color=(*color, 255))

            # Solo
            solo_cb = dpg.add_checkbox(
                default_value=stem.solo,
                user_data=stem_id,
                callback=self._on_solo,
            )
            with dpg.tooltip(solo_cb):
                dpg.add_text("Solo — hear only this stem")

            # Mute
            mute_cb = dpg.add_checkbox(
                default_value=stem.muted,
                user_data=stem_id,
                callback=self._on_mute,
            )
            with dpg.tooltip(mute_cb):
                dpg.add_text("Mute — silence this stem")

            # Volume
            dpg.add_slider_float(
                default_value=stem.volume,
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
                width=-1,
                user_data=stem_id,
                callback=self._on_stem_vol,
            )

            # Base BPM (per-stem native tempo)
            base_bpm_slider = dpg.add_slider_float(
                default_value=stem.base_bpm,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=-1,
                user_data=stem_id,
                callback=self._on_stem_base_bpm,
            )
            with dpg.tooltip(base_bpm_slider):
                dpg.add_text("Native tempo this stem was recorded at — controls playback speed scaling")

            # BPM Low
            dpg.add_slider_float(
                default_value=stem.bpm_low,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=-1,
                user_data=stem_id,
                callback=self._on_bpm_low,
            )

            # BPM High
            dpg.add_slider_float(
                default_value=stem.bpm_high,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=-1,
                user_data=stem_id,
                callback=self._on_bpm_high,
            )

            # Fade In
            dpg.add_slider_float(
                default_value=stem.fade_in,
                min_value=0.0,
                max_value=30.0,
                format="%.1f",
                width=-1,
                user_data=stem_id,
                callback=self._on_fade_in,
            )

            # Fade Out
            dpg.add_slider_float(
                default_value=stem.fade_out,
                min_value=0.0,
                max_value=30.0,
                format="%.1f",
                width=-1,
                user_data=stem_id,
                callback=self._on_fade_out,
            )

            # Actions: Up, Down, Remove
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Up",
                    user_data=stem_id,
                    callback=self._on_move_up,
                )
                dpg.add_button(
                    label="Down",
                    user_data=stem_id,
                    callback=self._on_move_down,
                )
                remove_btn = dpg.add_button(
                    label="Remove",
                    user_data=stem_id,
                    callback=self._on_remove,
                )
                with dpg.tooltip(remove_btn):
                    dpg.add_text("Remove this stem")

        self.stem_widgets[stem_id] = {
            "row_tag": row_tag,
            "stem_index": stem_index,
        }

    def _rebuild_stem_table(self):
        """Tear down and recreate the entire stem table from self.stems."""
        self.stem_widgets.clear()
        self._build_stem_table()

        for i, stem in enumerate(self.stems):
            stem_id = self._next_stem_id
            self._next_stem_id += 1
            self._add_stem_row(stem, stem_id, stem_index=i)

    def _on_solo(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].solo = value
        self._sync_stems()
        self._update_plot()

    def _on_mute(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].muted = value
        self._sync_stems()
        self._update_plot()

    def _on_stem_base_bpm(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].base_bpm = value
        self._sync_stems()

    def _on_stem_vol(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].volume = value
        self._sync_stems()
        self._update_plot()

    def _on_bpm_low(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].bpm_low = value
        self._sync_stems()
        self._update_plot()

    def _on_bpm_high(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].bpm_high = value
        self._sync_stems()
        self._update_plot()

    def _on_fade_in(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].fade_in = value
        self._sync_stems()
        self._update_plot()

    def _on_fade_out(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].fade_out = value
        self._sync_stems()
        self._update_plot()

    def _on_move_up(self, sender, app_data, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        if idx <= 0:
            return
        self.stems[idx - 1], self.stems[idx] = self.stems[idx], self.stems[idx - 1]
        self._rebuild_stem_table()
        self._sync_stems()
        self._update_plot()

    def _on_move_down(self, sender, app_data, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        if idx >= len(self.stems) - 1:
            return
        self.stems[idx], self.stems[idx + 1] = self.stems[idx + 1], self.stems[idx]
        self._rebuild_stem_table()
        self._sync_stems()
        self._update_plot()

    def _on_sort_bpm_asc(self):
        self.stems.sort(key=lambda s: s.bpm_low)
        self._rebuild_stem_table()
        self._sync_stems()
        self._update_plot()

    def _on_sort_bpm_desc(self):
        self.stems.sort(key=lambda s: s.bpm_low, reverse=True)
        self._rebuild_stem_table()
        self._sync_stems()
        self._update_plot()

    def _on_remove(self, sender, app_data, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems.pop(idx)
        self._rebuild_stem_table()
        self._update_stem_count()
        self._sync_stems()
        self._update_plot()

    def _update_stem_count(self):
        """Update the stem count label and empty-state hint visibility."""
        n = len(self.stems)
        dpg.set_value("stem_count_label", f"({n})")
        if dpg.does_item_exist("stem_empty_hint"):
            dpg.configure_item("stem_empty_hint", show=(n == 0))

    def _sync_stems(self):
        """Push current stems list to the mixer."""
        self.mixer.set_stems(self.stems)

    def _update_plot(self):
        """Redraw all volume curves and the BPM indicator line."""
        bpm = dpg.get_value("bpm_slider")

        # Update BPM vertical line
        dpg.set_value("bpm_line", [[bpm]])

        # Update BPM annotation
        dpg.configure_item(
            "bpm_annotation",
            default_value=(bpm, 1.05),
            label=f"{bpm:.1f}",
        )

        # Remove old curve series
        for tag in list(dpg.get_item_children("y_axis", 1)):
            alias = dpg.get_item_alias(tag)
            if alias and alias.startswith("curve_"):
                dpg.delete_item(tag)

        # Draw each stem's curve with legend labels
        bpm_range = np.linspace(BPM_MIN, BPM_MAX, 500)
        any_solo = any(s.solo for s in self.stems)

        for i, stem in enumerate(self.stems):
            # When any stem is soloed, non-solo stems show zero
            if any_solo and not stem.solo:
                vols = [0.0] * len(bpm_range)
            else:
                vols = [stem.volume_at_bpm(b) for b in bpm_range]
            color = STEM_COLORS[i % len(STEM_COLORS)]
            label = os.path.basename(stem.file_path) if stem.file_path else f"Stem {i+1}"
            dpg.add_line_series(
                bpm_range.tolist(),
                vols,
                parent="y_axis",
                tag=f"curve_{i}",
                label=label,
            )
            dpg.bind_item_theme(f"curve_{i}", self._get_line_theme(color))

    def _get_line_theme(self, color):
        tag = f"theme_{color[0]}_{color[1]}_{color[2]}"
        if not dpg.does_item_exist(tag):
            with dpg.theme(tag=tag):
                with dpg.theme_component(dpg.mvLineSeries):
                    dpg.add_theme_color(
                        dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots
                    )
        return tag


def main():
    app = SoundscapeApp()
    app.run()


if __name__ == "__main__":
    main()
