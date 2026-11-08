"""Regression coverage for the retained shortcut/lesson probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path


TASK_HOME = Path(__file__).resolve().parents[1]
PROBE_PATH = TASK_HOME / "workspace" / "probe_bbox_curriculum.py"


def _load_probe():
    spec = importlib.util.spec_from_file_location("bbox_curriculum_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_replays_declared_rivals_and_all_cyclic_windows():
    probe = _load_probe()
    report = probe.collect(seed_count=2, samples_per_seed=8)
    assert report["canonical_pairs"] == 5
    assert report["canonical_shortcut_matches"] == {"global_color_bbox": 5}
    assert report["draws"] == 48
    assert report["unique_inputs"] >= 40
    assert report["lesson_windows"] == 30
    assert report["lesson_failures"] == []
    assert report["rival_survivor_windows"] == []
    for band in ("easy", "medium", "hard"):
        assert set(report["profiles_per_band"][band]) == {
            "canonical_rectangle", "irregular_enclosure",
            "shared_color_pair", "closure_contrast",
        }
        assert report["bbox_counterexamples_per_band"][band] > 0
