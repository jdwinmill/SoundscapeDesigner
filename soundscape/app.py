"""Soundscape Designer — DearPyGui application.

Run with: python -m soundscape.app
"""

import glob
import os
from typing import Dict, List, Optional

import dearpygui.dearpygui as dpg
import numpy as np

from soundscape.config import SoundscapeConfig
from soundscape.definition_builder import DefinitionBuilder
from soundscape.mixer import Mixer
from soundscape.stem import Stem

STEMS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stems")

# Layout constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 850
PLOT_HEIGHT = 260
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

# UI palette
_BG_DARK = (15, 15, 20)
_BG_MID = (25, 25, 35)
_BG_CHILD = (22, 22, 30)
_ACCENT = (99, 102, 241)
_ACCENT_HOVER = (129, 140, 248)
_ACCENT_ACTIVE = (79, 70, 229)
_TEXT_DIM = (140, 140, 160)
_TEXT_BRIGHT = (240, 240, 245)
_SEPARATOR = (40, 40, 55)
_FRAME_BG = (30, 30, 42)
_FRAME_HOVER = (40, 40, 55)
_GRAB = (99, 102, 241)
_GRAB_ACTIVE = (129, 140, 248)
_HEADER_BG = (28, 28, 40)
_TABLE_ROW_ALT = (26, 26, 36)
_RED_BTN = (200, 60, 60)
_RED_BTN_HOVER = (220, 80, 80)
_TRANSPORT_BG = (18, 18, 26)


def _apply_global_theme():
    """Set up a modern, rounded, low-contrast theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Rounding
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 10)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 8)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 8)

            # Spacing & padding
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
            dpg.add_theme_style(dpg.mvStyleVar_ItemInnerSpacing, 6, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 20, 16)
            dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 18)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 10)

            # Colors — backgrounds
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, _BG_DARK)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _BG_CHILD)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, _BG_MID)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, _BG_MID)

            # Colors — frames / inputs
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, _FRAME_BG)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, _FRAME_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (55, 55, 75))

            # Colors — buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (35, 35, 50))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (48, 48, 68))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (58, 58, 80))

            # Colors — sliders / grabs
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, _GRAB)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, _GRAB_ACTIVE)

            # Colors — headers (table headers, collapsing headers)
            dpg.add_theme_color(dpg.mvThemeCol_Header, _HEADER_BG)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (45, 45, 62))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (55, 55, 72))

            # Colors — table
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, _TABLE_ROW_ALT)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, _SEPARATOR)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (40, 40, 55))

            # Colors — separators, borders
            dpg.add_theme_color(dpg.mvThemeCol_Separator, _SEPARATOR)
            dpg.add_theme_color(dpg.mvThemeCol_Border, (45, 45, 60))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))

            # Colors — text
            dpg.add_theme_color(dpg.mvThemeCol_Text, _TEXT_BRIGHT)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, _TEXT_DIM)

            # Colors — scrollbar
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (20, 20, 28))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (55, 55, 75))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (70, 70, 95))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (85, 85, 110))

            # Colors — checkmark / check box
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, _ACCENT)

            # Colors — plot
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, _ACCENT)

        # Plot-specific tweaks
        with dpg.theme_component(dpg.mvPlot):
            dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 12, 10)
            dpg.add_theme_color(
                dpg.mvPlotCol_PlotBg, (24, 24, 34), category=dpg.mvThemeCat_Plots
            )
            dpg.add_theme_color(
                dpg.mvPlotCol_FrameBg, _BG_CHILD, category=dpg.mvThemeCat_Plots
            )

    dpg.bind_theme(global_theme)


def _create_accent_button_theme():
    """Highlighted button theme for primary actions."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, _ACCENT)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _ACCENT_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, _ACCENT_ACTIVE)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255))
    return theme


def _create_danger_button_theme():
    """Red button theme for destructive actions."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, _RED_BTN)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, _RED_BTN_HOVER)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (230, 100, 100))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255))
    return theme


def _create_ghost_button_theme():
    """Subtle borderless button for secondary actions."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 255, 255, 20))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (255, 255, 255, 35))
    return theme


def _create_transport_theme():
    """Distinct background for the transport toolbar strip."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, _TRANSPORT_BG)
    return theme


def _section_header(label: str):
    """Draw a styled section header with a subtle separator."""
    dpg.add_spacer(height=10)
    dpg.add_separator()
    dpg.add_spacer(height=4)
    dpg.add_text(label, color=_ACCENT)
    dpg.add_spacer(height=6)


class SoundscapeApp:
    def __init__(self):
        self.mixer = Mixer()
        self.stems: List[Stem] = []
        self.stem_widgets: Dict[int, dict] = {}  # stem id -> widget tags
        self.playing = False
        self._next_stem_id = 0
        self._presets: Dict[str, str] = self._discover_presets()
        self._accent_theme = None
        self._danger_theme = None
        self._ghost_theme = None
        self._def_builder: Optional[DefinitionBuilder] = None

    @staticmethod
    def _discover_presets() -> Dict[str, str]:
        """Scan stems/ subdirectories for *_mix.json preset files."""
        presets: Dict[str, str] = {}
        pattern = os.path.join(STEMS_DIR, "**", "*_mix.json")
        for path in sorted(glob.glob(pattern, recursive=True)):
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

        # Load custom font
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "Inter-Regular.ttf")
        if os.path.isfile(font_path):
            with dpg.font_registry():
                default_font = dpg.add_font(font_path, 16)
                # Add Unicode glyph ranges for icons (arrows, play/stop, etc.)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default, parent=default_font)
                dpg.add_font_range(0x2190, 0x21FF, parent=default_font)  # Arrows
                dpg.add_font_range(0x25A0, 0x25FF, parent=default_font)  # Geometric shapes
                dpg.add_font_range(0x2700, 0x27BF, parent=default_font)  # Dingbats
            dpg.bind_font(default_font)

        _apply_global_theme()
        self._accent_theme = _create_accent_button_theme()
        self._danger_theme = _create_danger_button_theme()
        self._ghost_theme = _create_ghost_button_theme()
        self._transport_theme = _create_transport_theme()

        with dpg.window(tag="primary", label="Soundscape Designer"):
            with dpg.tab_bar(tag="main_tab_bar"):
                with dpg.tab(label="Designer", tag="designer_tab"):
                    self._build_transport()
                    dpg.bind_item_theme("transport_bar", self._transport_theme)
                    self._build_tempo()
                    self._build_stem_list()
                    self._build_plot()
                    self._build_config_bar()
                with dpg.tab(label="Stem Definitions", tag="def_tab"):
                    self._def_builder = DefinitionBuilder(
                        self._accent_theme, self._danger_theme,
                    )
                    self._def_builder.build("def_tab")

        self._register_keyboard_shortcuts()

        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary", True)
        dpg.start_dearpygui()
        dpg.destroy_context()

        # Cleanup audio on exit
        self.mixer.stop()

    # ── Transport ──────────────────────────────────────────────

    def _build_transport(self):
        with dpg.child_window(height=52, border=False, tag="transport_bar"):
            with dpg.group(horizontal=True):
                play_btn = dpg.add_button(
                    tag="play_btn",
                    label="\u25b6  Play",
                    callback=self._on_play_stop,
                )
                dpg.bind_item_theme(play_btn, self._accent_theme)
                with dpg.tooltip(play_btn):
                    dpg.add_text("Start / stop playback (Space)")

                dpg.add_button(
                    label="\u21ba  Restart",
                    callback=self._on_reset,
                )

                dpg.add_spacer(width=24)

                dpg.add_text("Master", color=_TEXT_DIM)
                tag_master = dpg.add_slider_float(
                    tag="master_vol_slider",
                    default_value=1.0,
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                    width=180,
                    callback=self._on_master_vol_change,
                )
                with dpg.tooltip(tag_master):
                    dpg.add_text("Global output level")

                dpg.add_spacer(width=24)

                # Preset selector in the transport bar — quick access
                dpg.add_text("Preset", color=_TEXT_DIM)
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

    # ── Tempo ──────────────────────────────────────────────────

    def _build_tempo(self):
        _section_header("Tempo")
        with dpg.group(horizontal=True):
            dpg.add_text("BPM", color=_TEXT_DIM)
            tag_bpm = dpg.add_slider_float(
                tag="bpm_slider",
                default_value=150.0,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=360,
                callback=self._on_bpm_change,
            )
            with dpg.tooltip(tag_bpm):
                dpg.add_text("Simulated running tempo — drag or use arrow keys")

            dpg.add_spacer(width=20)
            dpg.add_text("Base", color=_TEXT_DIM)
            tag_base = dpg.add_slider_float(
                tag="base_bpm_slider",
                default_value=150.0,
                min_value=BPM_MIN,
                max_value=BPM_MAX,
                format="%.1f",
                width=240,
                callback=self._on_base_bpm_change,
            )
            with dpg.tooltip(tag_base):
                dpg.add_text("Native tempo the audio stems were recorded at")

    # ── Stem list ──────────────────────────────────────────────

    def _build_stem_list(self):
        _section_header("Stems")
        with dpg.group(horizontal=True):
            dpg.add_text("", tag="stem_count_label", color=_TEXT_DIM)
            dpg.add_spacer(width=4)

            add_btn = dpg.add_button(label="+ Add Stem", callback=self._on_add_stem)
            dpg.bind_item_theme(add_btn, self._accent_theme)

            dpg.add_spacer(width=12)
            sort_asc = dpg.add_button(label="Sort BPM Asc", callback=self._on_sort_bpm_asc)
            dpg.bind_item_theme(sort_asc, self._ghost_theme)
            with dpg.tooltip(sort_asc):
                dpg.add_text("Sort stems by BPM low, ascending")

            sort_desc = dpg.add_button(label="Sort BPM Desc", callback=self._on_sort_bpm_desc)
            dpg.bind_item_theme(sort_desc, self._ghost_theme)
            with dpg.tooltip(sort_desc):
                dpg.add_text("Sort stems by BPM low, descending")

        dpg.add_spacer(height=4)
        dpg.add_child_window(
            tag="stem_list",
            height=300,
            border=False,
        )
        dpg.add_text(
            "No stems loaded — click '+ Add Stem' or pick a preset to get started.",
            tag="stem_empty_hint",
            parent="stem_list",
            color=_TEXT_DIM,
        )

    def _build_stem_table(self):
        """Create the stem table inside stem_list. Called once, rows added later."""
        if dpg.does_item_exist("stem_table"):
            dpg.delete_item("stem_table")

        with dpg.table(
            tag="stem_table",
            parent="stem_list",
            header_row=True,
            borders_innerH=False,
            borders_outerH=False,
            borders_innerV=False,
            borders_outerV=False,
            row_background=True,
            resizable=True,
        ):
            dpg.add_table_column(label="Name", width_fixed=True, init_width_or_weight=140)
            dpg.add_table_column(label="S", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="M", width_fixed=True, init_width_or_weight=30)
            dpg.add_table_column(label="Vol", width_fixed=True, init_width_or_weight=90)
            dpg.add_table_column(label="Speed", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Base BPM", width_fixed=True, init_width_or_weight=90)
            dpg.add_table_column(label="BPM Low", width_fixed=True, init_width_or_weight=90)
            dpg.add_table_column(label="BPM High", width_fixed=True, init_width_or_weight=90)
            dpg.add_table_column(label="Fade In", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="Fade Out", width_fixed=True, init_width_or_weight=80)
            dpg.add_table_column(label="", width_fixed=True, init_width_or_weight=120)

    # ── Plot ───────────────────────────────────────────────────

    def _build_plot(self):
        _section_header("Volume Curves")
        with dpg.plot(
            tag="curve_plot",
            label="",
            height=PLOT_HEIGHT,
            width=-1,
            no_title=True,
        ):
            dpg.add_plot_legend()
            dpg.add_plot_axis(dpg.mvXAxis, label="BPM", tag="x_axis")
            dpg.set_axis_limits("x_axis", BPM_MIN, BPM_MAX)
            dpg.add_plot_axis(dpg.mvYAxis, label="Volume", tag="y_axis")
            dpg.set_axis_limits("y_axis", 0.0, 1.1)

            dpg.add_vline_series(
                [150.0],
                tag="bpm_line",
                parent="y_axis",
            )
            dpg.add_plot_annotation(
                tag="bpm_annotation",
                default_value=(150.0, 1.05),
                label="150.0",
                color=(255, 255, 255, 180),
                offset=(0, -15),
            )

    # ── Config bar (bottom) ────────────────────────────────────

    def _build_config_bar(self):
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            export_btn = dpg.add_button(label="Export JSON", callback=self._on_export)
            with dpg.tooltip(export_btn):
                dpg.add_text("Save stem config for the iOS app (Ctrl+E)")

            load_btn = dpg.add_button(label="Load JSON", callback=self._on_import)
            with dpg.tooltip(load_btn):
                dpg.add_text("Load a previously saved config (Ctrl+L)")

    # ── Keyboard shortcuts ─────────────────────────────────────

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

    def _is_on_designer_tab(self) -> bool:
        """Return True if the Designer tab is currently active."""
        return dpg.get_value("main_tab_bar") == dpg.get_item_id("designer_tab")

    def _on_key_space(self):
        # Don't trigger play/stop when typing in an input or on the Definitions tab
        if not self._is_on_designer_tab():
            return
        active = dpg.get_item_type(dpg.get_active_window())
        if "input" in active.lower():
            return
        self._on_play_stop()

    def _on_key_e(self):
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            self._on_export()

    def _on_key_l(self):
        if dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl):
            self._on_import()

    # ── Callbacks ──────────────────────────────────────────────

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
            dpg.set_item_label("play_btn", "\u25b6  Play")
        else:
            self._sync_stems()
            self.mixer.start()
            self.playing = True
            dpg.set_item_label("play_btn", "\u25a0  Stop")

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

        self.stems.clear()
        self.stem_widgets.clear()

        dpg.set_value("base_bpm_slider", config.base_bpm)

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

            # Speed multiplier
            speed_slider = dpg.add_slider_float(
                default_value=stem.speed,
                min_value=0.25,
                max_value=4.0,
                format="%.2fx",
                width=-1,
                user_data=stem_id,
                callback=self._on_stem_speed,
            )
            with dpg.tooltip(speed_slider):
                dpg.add_text("Playback speed — 1.0x = normal, 2.0x = double speed")

            # Base BPM (per-stem)
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
                dpg.add_text("Native tempo — controls playback speed scaling")

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

            # Actions: compact arrow buttons + remove
            with dpg.group(horizontal=True):
                up_btn = dpg.add_button(
                    label=" \u25b2 ",
                    user_data=stem_id,
                    callback=self._on_move_up,
                )
                dpg.bind_item_theme(up_btn, self._ghost_theme)

                down_btn = dpg.add_button(
                    label=" \u25bc ",
                    user_data=stem_id,
                    callback=self._on_move_down,
                )
                dpg.bind_item_theme(down_btn, self._ghost_theme)

                remove_btn = dpg.add_button(
                    label=" \u2715 ",
                    user_data=stem_id,
                    callback=self._on_remove,
                )
                dpg.bind_item_theme(remove_btn, self._danger_theme)
                with dpg.tooltip(remove_btn):
                    dpg.add_text("Remove this stem")

        self.stem_widgets[stem_id] = {
            "row_tag": row_tag,
            "stem_index": stem_index,
        }

    def _rebuild_stem_table(self):
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

    def _on_stem_speed(self, sender, value, stem_id):
        idx = self.stem_widgets[stem_id]["stem_index"]
        self.stems[idx].speed = value
        self._sync_stems()

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
        n = len(self.stems)
        dpg.set_value("stem_count_label", f"{n} stem{'s' if n != 1 else ''}")
        if dpg.does_item_exist("stem_empty_hint"):
            dpg.configure_item("stem_empty_hint", show=(n == 0))

    def _sync_stems(self):
        self.mixer.set_stems(self.stems)

    def _update_plot(self):
        bpm = dpg.get_value("bpm_slider")

        dpg.set_value("bpm_line", [[bpm]])
        dpg.configure_item(
            "bpm_annotation",
            default_value=(bpm, 1.05),
            label=f"{bpm:.1f}",
        )

        for tag in list(dpg.get_item_children("y_axis", 1)):
            alias = dpg.get_item_alias(tag)
            if alias and alias.startswith("curve_"):
                dpg.delete_item(tag)

        bpm_range = np.linspace(BPM_MIN, BPM_MAX, 500)
        any_solo = any(s.solo for s in self.stems)

        for i, stem in enumerate(self.stems):
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
