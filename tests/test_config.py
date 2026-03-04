import json
import os

import pytest

from soundscape.config import SoundscapeConfig
from soundscape.stem import Stem


class TestExport:
    def test_export_basic(self, tmp_path):
        stems = [
            Stem(
                bpm_low=100,
                bpm_high=140,
                fade_in=5,
                fade_out=10,
                volume=0.8,
                file_path="/audio/march.wav",
            ),
        ]
        config = SoundscapeConfig(base_bpm=150.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        assert data["baseBPM"] == 150.0
        assert len(data["stems"]) == 1
        s = data["stems"][0]
        assert s["file"] == "march.wav"
        assert s["bpmRange"] == [100, 140]
        assert s["fadeIn"] == 5
        assert s["fadeOut"] == 10
        assert s["volume"] == 0.8

    def test_export_relative_paths(self, tmp_path):
        stems = [
            Stem(bpm_low=80, bpm_high=120, file_path="/some/deep/path/beat.wav"),
        ]
        config = SoundscapeConfig(base_bpm=120.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        # Should only have the filename, not the full path
        assert data["stems"][0]["file"] == "beat.wav"

    def test_export_multiple_stems(self, tmp_path):
        stems = [
            Stem(bpm_low=100, bpm_high=140, file_path="/a/one.wav"),
            Stem(bpm_low=140, bpm_high=180, file_path="/b/two.wav"),
        ]
        config = SoundscapeConfig(base_bpm=160.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        assert len(data["stems"]) == 2
        assert data["stems"][0]["file"] == "one.wav"
        assert data["stems"][1]["file"] == "two.wav"

    def test_export_no_file_path(self, tmp_path):
        """Stems without a file path use empty string."""
        stems = [Stem(bpm_low=100, bpm_high=140)]
        config = SoundscapeConfig(base_bpm=150.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        assert data["stems"][0]["file"] == ""


class TestImport:
    def test_import_roundtrip(self, tmp_path):
        original_stems = [
            Stem(
                bpm_low=100,
                bpm_high=140,
                fade_in=5,
                fade_out=10,
                volume=0.8,
                file_path="/audio/march.wav",
            ),
        ]
        config = SoundscapeConfig(base_bpm=150.0, stems=original_stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        loaded = SoundscapeConfig.load(str(out_path))
        assert loaded.base_bpm == 150.0
        assert len(loaded.stems) == 1
        s = loaded.stems[0]
        assert s.bpm_low == 100
        assert s.bpm_high == 140
        assert s.fade_in == 5
        assert s.fade_out == 10
        assert s.volume == 0.8

    def test_import_missing_optional_fields(self, tmp_path):
        """Missing fadeIn/fadeOut/volume should use defaults."""
        data = {
            "baseBPM": 150.0,
            "stems": [{"file": "test.wav", "bpmRange": [100, 140]}],
        }
        path = tmp_path / "minimal.json"
        path.write_text(json.dumps(data))

        config = SoundscapeConfig.load(str(path))
        s = config.stems[0]
        assert s.fade_in == 5.0
        assert s.fade_out == 5.0
        assert s.volume == 1.0

    def test_import_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json at all {{{")

        with pytest.raises(json.JSONDecodeError):
            SoundscapeConfig.load(str(path))

    def test_import_missing_required_fields(self, tmp_path):
        data = {"stems": [{"file": "test.wav"}]}  # missing baseBPM and bpmRange
        path = tmp_path / "incomplete.json"
        path.write_text(json.dumps(data))

        with pytest.raises(KeyError):
            SoundscapeConfig.load(str(path))


class TestPerStemBaseBPM:
    def test_export_includes_per_stem_base_bpm_when_different(self, tmp_path):
        """Stems with base_bpm != global baseBPM should export their own baseBPM."""
        stems = [
            Stem(bpm_low=100, bpm_high=140, base_bpm=120.0, file_path="/a/march.wav"),
            Stem(bpm_low=150, bpm_high=200, base_bpm=150.0, file_path="/a/fast.wav"),
        ]
        config = SoundscapeConfig(base_bpm=150.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        # First stem differs from global — should have baseBPM
        assert data["stems"][0]["baseBPM"] == 120.0
        # Second stem matches global — should not have baseBPM
        assert "baseBPM" not in data["stems"][1]

    def test_export_omits_per_stem_base_bpm_when_same(self, tmp_path):
        """Stems matching the global baseBPM should not include baseBPM in JSON."""
        stems = [Stem(bpm_low=100, bpm_high=140, base_bpm=150.0, file_path="/a.wav")]
        config = SoundscapeConfig(base_bpm=150.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        data = json.loads(out_path.read_text())
        assert "baseBPM" not in data["stems"][0]

    def test_import_per_stem_base_bpm(self, tmp_path):
        """Stems with per-stem baseBPM should load it correctly."""
        data = {
            "baseBPM": 150.0,
            "stems": [
                {"file": "march.wav", "bpmRange": [100, 140], "baseBPM": 120.0},
                {"file": "fast.wav", "bpmRange": [150, 200]},
            ],
        }
        path = tmp_path / "config.json"
        path.write_text(json.dumps(data))

        config = SoundscapeConfig.load(str(path))
        assert config.stems[0].base_bpm == 120.0
        # Second stem should fall back to global baseBPM
        assert config.stems[1].base_bpm == 150.0

    def test_roundtrip_per_stem_base_bpm(self, tmp_path):
        """Per-stem baseBPM should survive export/import roundtrip."""
        stems = [
            Stem(bpm_low=100, bpm_high=140, base_bpm=120.0, file_path="/a/march.wav"),
            Stem(bpm_low=150, bpm_high=200, base_bpm=160.0, file_path="/a/techno.wav"),
        ]
        config = SoundscapeConfig(base_bpm=150.0, stems=stems)
        out_path = tmp_path / "config.json"
        config.export(str(out_path))

        loaded = SoundscapeConfig.load(str(out_path))
        assert loaded.stems[0].base_bpm == 120.0
        assert loaded.stems[1].base_bpm == 160.0
