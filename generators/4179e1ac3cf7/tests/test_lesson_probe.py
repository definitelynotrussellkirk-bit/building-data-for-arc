"""Unit tests for the retained source-bound lesson probe."""
from __future__ import annotations

import importlib.util
from pathlib import Path

PROBE = Path(__file__).resolve().parents[1] / "workspace" / "lesson_probe.py"


def _load():
    spec = importlib.util.spec_from_file_location("lesson_probe_4179e1ac3cf7", PROBE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_has_requested_lessons_per_band_without_overlapping_windows():
    probe = _load()
    plan = probe.lesson_plan(100, n_demos=4, n_queries=1)
    assert len(plan) == 300
    for band in probe.BANDS:
        rows = [row for row in plan if row["band"] == band]
        assert len(rows) == 100
        assert len({row["seed"] for row in rows}) == 100
        windows = [
            set(range(row["sample_index"], row["sample_index"] + 5))
            for row in rows
        ]
        assert all(not a.intersection(b) for i, a in enumerate(windows) for b in windows[i + 1 :])


def test_grid_hash_is_stable_and_shape_sensitive():
    probe = _load()
    grid = [[0, 1], [3, 0]]
    assert probe.grid_hash(grid) == probe.grid_hash([[0, 1], [3, 0]])
    assert probe.grid_hash(grid) != probe.grid_hash([[0, 1, 3, 0]])
