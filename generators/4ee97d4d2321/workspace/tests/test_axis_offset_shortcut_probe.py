from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest


PROBE_PATH = Path(__file__).resolve().parents[1] / "axis_offset_shortcut_probe.py"


def _load_probe():
    if not PROBE_PATH.is_file():
        pytest.fail(f"missing reusable probe: {PROBE_PATH.name}")
    spec = importlib.util.spec_from_file_location("axis_offset_shortcut_probe", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _independent_shortcut(grid):
    height, width = len(grid), len(grid[0])
    axis = next(
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    )
    offset = axis - (width - 1) // 2
    if offset == 0:
        selected_side = "both"
    elif abs(offset) == 1:
        selected_side = "left" if offset < 0 else "right"
    else:
        selected_side = "right" if offset < 0 else "left"

    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value in (0, 8):
                continue
            if selected_side == "left" and col > axis:
                continue
            if selected_side == "right" and col < axis:
                continue
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out


def test_probe_matches_independent_rival_and_certifies_repaired_schedule():
    probe = _load_probe()
    gen = probe.load_generator()

    for index in range(20):
        grid = gen.generate(991, index, difficulty="medium")
        assert probe.axis_offset_side_shortcut(grid) == _independent_shortcut(grid)

    report = probe.analyze(draws_per_band=20, seed=991)
    assert report["passed"] is True
    for band in ("easy", "medium", "hard"):
        result = report["bands"][band]
        assert result["distinct_joint_pairs"] == 20
        assert result["surviving_lesson_windows"] == []
    assert report["explicit_counterexample"]["shortcut_refuted"] is True
