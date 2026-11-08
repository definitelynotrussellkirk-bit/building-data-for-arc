"""Regression tests for authority identity and occlusion counterfactuals."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

TASK_ID = "2f0a4d589c58"
TEST_PATH = Path(__file__).resolve()
TASK_ROOT = TEST_PATH.parents[1]
REPO_ROOT = TEST_PATH.parents[3]
GENERATOR_PATH = TASK_ROOT / "generator.py"
BASE_PATH = (
    REPO_ROOT
    / "shared/data/base/solutions/training/ba97ae07__2f0a4d589c58.json"
)
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
PAIR_AXES = (
    "grid_h",
    "grid_w",
    "horizontal_thickness",
    "vertical_thickness",
    "horizontal_position",
    "vertical_position",
    "horizontal_color",
    "vertical_color_offset",
)


def _load_generator():
    runtime = REPO_ROOT / "shared/runtime"
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location(
        "counterfactual_schedule_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_program() -> str:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return str(row["program_solution"])
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _only_overlap_differs(
    left: list[list[int]], right: list[list[int]], info: dict[str, Any]
) -> bool:
    changed = {
        (row, col)
        for row in range(len(left))
        for col in range(len(left[0]))
        if left[row][col] != right[row][col]
    }
    overlap = {
        (row, col)
        for row in info["horizontal_rows"]
        for col in info["vertical_cols"]
    }
    return changed == overlap


def test_selected_racket_target_is_exact_canonical_text():
    selected = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert selected["racket_target"]["target_code"] == _canonical_program()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_adjacent_schedule_members_are_minimal_occluder_counterfactuals(difficulty):
    for pair_group in range(18):
        seed = 730_000 + pair_group
        left = GEN.generate(seed, pair_group * 2, difficulty=difficulty)
        right = GEN.generate(seed, pair_group * 2 + 1, difficulty=difficulty)
        left_observed = GEN.observe_overrides(left)
        right_observed = GEN.observe_overrides(right)

        assert {
            name: left_observed[name] for name in PAIR_AXES
        } == {
            name: right_observed[name] for name in PAIR_AXES
        }
        assert {
            left_observed["occluder"], right_observed["occluder"]
        } == {"horizontal", "vertical"}
        assert _only_overlap_differs(left, right, GEN._analyze(left))


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_three_demo_window_refutes_geometry_only_occluder_competitor(difficulty):
    competitor = GEN.LESSON_COMPETITORS["geometry_only_occluder"]
    for start in range(48):
        demos = []
        for offset in range(3):
            grid = GEN.generate(810_000 + start, start + offset, difficulty=difficulty)
            demos.append((grid, GEN.rule_mirror(grid)))
        assert any(competitor(grid) != truth for grid, truth in demos)
