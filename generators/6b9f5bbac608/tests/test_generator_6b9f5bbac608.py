from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "6b9f5bbac608"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.6b9f5bbac608.generator"
)
REPO = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (REPO / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _normal(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _bbox_center_output(grid):
    analysis = MODULE._analyze_grid(grid)
    assert not analysis["errors"]
    output = [[0] * len(grid[0]) for _ in grid]
    for component, center in zip(analysis["components"], analysis["centers"]):
        output[center[0]][center[1]] = component["color"]
    return output


def test_rule_hash_and_all_canonical_inputs() -> None:
    row = _canonical_row()
    actual_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert MODULE.RULE_HASH == actual_hash
    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 3
    for pair in pairs:
        grid = _normal(pair["input"])
        assert MODULE.self_check(grid) == []
        assert _bbox_center_output(grid) == _normal(pair["output"])


def test_exact_axes_at_boundaries_and_profiles() -> None:
    cases = [
        dict(grid_h=8, grid_w=8, n_blobs=2, palette_kind="warm", center_profile="occupied", size_profile="small"),
        dict(grid_h=14, grid_w=14, n_blobs=4, palette_kind="cool", center_profile="vacant", size_profile="large"),
        dict(grid_h=11, grid_w=12, n_blobs=3, palette_kind="mixed", center_profile="mixed", size_profile="mixed"),
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MODULE.generate(100 + index, 20 + index, difficulty=band, **overrides)
            assert MODULE.self_check(grid) == []
            assert MODULE.observe_overrides(grid) == overrides


def test_three_sequential_demos_cover_center_and_size_profiles() -> None:
    for start in range(6):
        observed = [
            MODULE.observe_overrides(MODULE.generate(17, start + offset, difficulty="medium"))
            for offset in range(3)
        ]
        assert {item["center_profile"] for item in observed} == {
            "occupied", "vacant", "mixed"
        }
        assert {item["size_profile"] for item in observed} == {
            "small", "large", "mixed"
        }


def test_determinism_fresh_returns_and_global_rng() -> None:
    random.seed(981273)
    before = random.getstate()
    first = MODULE.generate(44, 9, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(44, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == MODULE.generate(44, 9, difficulty="hard")
    assert second != MODULE.generate(45, 9, difficulty="hard")
    assert second != MODULE.generate(44, 10, difficulty="hard")


def test_targeted_impostors_are_rejected() -> None:
    blank = [[0] * 11 for _ in range(8)]

    all_singletons = copy.deepcopy(blank)
    all_singletons[2][3] = 4
    all_singletons[5][7] = 6
    all_singletons[6][1] = 3

    split_same_color = copy.deepcopy(blank)
    for column in (1, 2, 3):
        split_same_color[1][column] = 4
    for column in (7, 8, 9):
        split_same_color[6][column] = 4
    for row in (3, 4, 5):
        split_same_color[row][5] = 6


    two_cell_object = copy.deepcopy(blank)
    two_cell_object[1][1] = 4
    two_cell_object[1][2] = 4
    for row in (4, 5, 6):
        two_cell_object[row][7] = 6

    unsupported_shape = copy.deepcopy(blank)
    for row in (1, 2):
        for column in (1, 2):
            unsupported_shape[row][column] = 4
    for row in (4, 5, 6):
        unsupported_shape[row][7] = 6


    impostors = {
        "all_background": blank,
        "all_singletons": all_singletons,
        "split_same_color": split_same_color,
        "two_cell_object": two_cell_object,
        "unsupported_shape": unsupported_shape,
    }
    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name


def test_invalid_overrides_reject_loudly() -> None:
    with pytest.raises(TypeError):
        MODULE.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, grid_h=7)
    with pytest.raises(ValueError):
        MODULE.generate(1, 1, palette_kind="default")
