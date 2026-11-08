"""Regression tests against profile-conditioned positional shortcuts."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "position_curriculum_generator_00f0de29a65c", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _quadrant(grid, component):
    row1, col1, row2, col2 = component["bbox"]
    row_mid = (row1 + row2) / 2
    col_mid = (col1 + col2) / 2
    return (
        "top" if row_mid < len(grid) / 2 else "bottom",
        "left" if col_mid < len(grid[0]) / 2 else "right",
    )


def _profile_position_shortcut(grid):
    """The imported repair's residual shortcut: profile -> fixed location."""
    analysis = GEN._analysis(grid)
    if analysis["texture"] == "unique_min":
        bottom_left = [
            shape
            for shape in analysis["shapes"]
            if _quadrant(grid, shape) == ("bottom", "left")
        ]
        selected = bottom_left[0] if bottom_left else analysis["shapes"][0]
    else:
        selected = analysis["shapes"][0]
    marker_color = analysis["singles"][0]["color"]
    return GEN._render_component(grid, selected, recolor_to=marker_color)


def test_unique_minimum_target_visits_all_four_quadrants():
    observed = set()
    for block in range(32):
        sample_index = 4 * block  # unique_min slot in every curriculum cycle
        grid = GEN.generate(1_200_000 + block, sample_index, difficulty="medium")
        analysis = GEN._analysis(grid)
        assert analysis["texture"] == "unique_min"
        observed.add(_quadrant(grid, analysis["target"]))
    assert observed == {
        ("top", "left"),
        ("top", "right"),
        ("bottom", "left"),
        ("bottom", "right"),
    }


def test_old_profile_position_shortcut_is_declared_and_refuted():
    assert "profile_position" in GEN.LESSON_COMPETITORS
    mismatches = 0
    for sample_index in range(80):
        grid = GEN.generate(1_300_000, sample_index, difficulty="hard")
        mismatches += _profile_position_shortcut(grid) != GEN.rule_mirror(grid)
    assert mismatches >= 20


def test_every_cyclic_four_demo_window_refutes_all_declared_competitors():
    for start in range(4):
        pairs = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
            grid = GEN.generate(1_400_000 + start, sample_index, difficulty="easy")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []
