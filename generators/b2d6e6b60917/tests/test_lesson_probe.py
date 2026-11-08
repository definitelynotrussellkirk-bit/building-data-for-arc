"""Regression tests for the retained lesson-level rival probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1] / "workspace"
PROBE_PATH = WORKSPACE / "lesson_probe.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("b2d6_lesson_probe", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_small_probe_is_source_bound_complete_and_rival_refuting():
    probe = load_probe()
    report = probe.build_report(lessons_per_band=6)
    assert report["task_id"] == "b2d6e6b60917"
    assert report["rule_hash"] == "73b1bc28244d"
    assert len(report["generator_sha256"]) == 64
    assert report["canonical"]["mirror_failures"] == []
    assert report["canonical"]["shortcuts_fitting_all_pairs"] == ["fixed_stride_4"]
    assert report["declarations"]["competitors"]
    assert report["declarations"]["witnesses"]
    for band in ("easy", "medium", "hard"):
        stats = report["bands"][band]
        assert stats["lessons"] == 6
        assert stats["pairs"] == 24
        assert stats["lesson_failures"] == []
        assert stats["surviving_competitors"] == {}
        assert set(stats["profiles"]) == {
            "canonical_3x3",
            "wide_2x4",
            "tall_4x2",
        }
        assert all(count > 0 for count in stats["witness_hits"].values())
        assert all(count > 0 for count in stats["rival_disagreements"].values())
