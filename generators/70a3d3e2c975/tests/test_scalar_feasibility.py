"""Feasible partial controls must constrain dimensions that remain unpinned."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest


TASK_ID = "70a3d3e2c975"
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "puzzle_generators" / "base.py").is_file():
        sys.path.insert(0, str(runtime))
        default_path = ancestor / "generators" / TASK_ID / "generator.py"
        break
    if (ancestor / "puzzle_generators" / "base.py").is_file():
        sys.path.insert(0, str(ancestor))
        default_path = ancestor / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
        break
else:
    raise RuntimeError("could not locate the generator's own runtime")

generator_path = Path(os.environ.get("GENERATOR_UNDER_TEST", default_path))
spec = importlib.util.spec_from_file_location("scalar_feasibility_generator", generator_path)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


@pytest.mark.parametrize("overrides", [
    pytest.param({"marks": 15}, id="marks-15-free-geometry"),
    pytest.param({"marks": 20}, id="marks-20-free-geometry"),
    pytest.param({"half_w": 2, "marks": 20}, id="marks-20-free-height"),
    pytest.param({"grid_h": 5, "marks": 20}, id="marks-20-free-width"),
    pytest.param({"texture": "full_left", "marks": 12}, id="full-left-free-geometry"),
    pytest.param({"texture": "full_left", "half_w": 2, "marks": 12}, id="full-left-free-height"),
    pytest.param({"texture": "full_left", "grid_h": 6, "marks": 12}, id="full-left-free-width"),
])
def test_feasible_partial_controls_choose_sufficient_free_geometry(overrides):
    grid = gen.generate(2, 1, **overrides)
    height, half_width = len(grid), len(grid[0]) // 2
    assert gen.self_check(grid) == []
    assert sum(value in range(1, 9) for row in grid for value in row[:half_width]) == overrides["marks"]
    if "grid_h" in overrides:
        assert height == overrides["grid_h"]
    if "half_w" in overrides:
        assert half_width == overrides["half_w"]


def test_infeasible_fully_pinned_geometry_still_reports_joint_conflict():
    with pytest.raises(ValueError) as caught:
        gen.generate(2, 1, grid_h=5, half_w=2, marks=20)
    assert set(caught.value.incompatible_axes) == {"grid_h", "half_w", "marks"}
