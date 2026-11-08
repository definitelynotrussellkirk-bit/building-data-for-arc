"""Focused regression tests for advertised override endpoints."""
from __future__ import annotations

from reviewer_support import find_root, load_selected_generator

TASK_ID = "85d3a8e1aa7f"
ROOT = find_root(__file__)
gen, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _base(**overrides):
    controls = {
        "grid_n": 15,
        "key_color": 1,
        "quadrant_choice": "top_left",
        "key_position_kind": "scattered",
        "n_key_cells": 4,
        "n_distractors": 3,
        "distractor_palette_size": 2,
    }
    controls.update(overrides)
    return gen.generate(0, 0, **controls)


def _colors(grid):
    return {cell for row in grid for cell in row}


def test_advertised_n_key_cells_upper_endpoint_is_honored():
    grid = _base(n_key_cells=15, n_distractors=0)
    assert sum(cell == 1 for row in grid for cell in row) == 16  # 15 + center
    assert _colors(grid) == {1, 7}
    assert gen.self_check(grid) == []


def test_advertised_zero_distractors_endpoint_is_honored():
    grid = _base(n_distractors=0)
    assert _colors(grid) == {1, 7}
    assert gen.self_check(grid) == []


def test_advertised_single_distractor_color_endpoint_is_honored():
    grid = _base(distractor_palette_size=1)
    distractor_colors = _colors(grid) - {1, 7}
    assert len(distractor_colors) == 1
    assert gen.self_check(grid) == []
