from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest


TASK_ID = "3c66fa1a10c7"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs = [pair["input"] for pair in row["train"]]
                pairs.append(row["test"]["input"])
                return [
                    [[int(cell) for cell in string_row] for string_row in grid]
                    for grid in pairs
                ]
    raise AssertionError("canonical task missing")


def test_all_canonical_inputs_are_accepted():
    for grid in _canonical_inputs():
        assert MODULE.self_check(grid) == []


def test_default_draws_are_valid_deterministic_and_fresh():
    seen_codes = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = MODULE.generate(seed, seed * 13 + 5, difficulty=band)
            assert MODULE.self_check(grid) == []
            assert grid == MODULE.generate(seed, seed * 13 + 5, difficulty=band)
            replay = MODULE.generate(seed, seed * 13 + 5, difficulty=band)
            replay[0][0] = 9
            assert MODULE.generate(seed, seed * 13 + 5, difficulty=band)[0][0] in (1, 2, 3)
            seen_codes.add(grid[0][0])
    assert seen_codes == {1, 2, 3}


@pytest.mark.parametrize("body_h", [3, 7])
@pytest.mark.parametrize("panel_w", [3, 7])
@pytest.mark.parametrize("code", [1, 3])
@pytest.mark.parametrize("panel_color", [4, 9])
@pytest.mark.parametrize("signal_cells", [3, 8])
def test_boundary_overrides_are_observable(
    body_h, panel_w, code, panel_color, signal_cells
):
    requested = {
        "body_h": body_h,
        "panel_w": panel_w,
        "code": code,
        "panel_color": panel_color,
        "signal_cells": signal_cells,
    }
    grid = MODULE.generate(11, 29, difficulty="hard", **requested)
    assert MODULE.self_check(grid) == []
    assert MODULE.observe_overrides(grid) == requested


def test_invalid_overrides_fail_loudly():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, panel_color=5)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, code=4)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, body_h=2)
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, texture="warm")


def test_adversarial_impostors_are_rejected():
    grid = MODULE.generate(3, 7, body_h=3, panel_w=3, signal_cells=3)

    bad_top = copy.deepcopy(grid)
    bad_top[0][2] = 8
    assert MODULE.self_check(bad_top)

    multi_color = copy.deepcopy(grid)
    for r in range(1, len(multi_color)):
        changed = False
        for c in range(3):
            if multi_color[r][c] != 0:
                multi_color[r][c] = 6 if multi_color[r][c] != 6 else 4
                changed = True
                break
        if changed:
            break
    assert MODULE.self_check(multi_color)

    no_overlap = copy.deepcopy(grid)
    div = 3
    for r in range(1, len(no_overlap)):
        for c in range(div):
            if no_overlap[r][c] and no_overlap[r][div + 1 + c]:
                no_overlap[r][div + 1 + c] = 0
    assert any("overlap" in err for err in MODULE.self_check(no_overlap))

    no_singleton = copy.deepcopy(grid)
    for r in range(1, len(no_singleton)):
        for c in range(div):
            left = no_singleton[r][c]
            right = no_singleton[r][div + 1 + c]
            if bool(left) != bool(right):
                color = left or right
                no_singleton[r][c] = color
                no_singleton[r][div + 1 + c] = color
    assert any("one-sided" in err for err in MODULE.self_check(no_singleton))
