from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "49bfa2fd18b7"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _valid_fixture():
    grid = [[0] * 12 for _ in range(10)]
    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1)]:
        grid[row][col] = 6
    for row, col in [(1, 7), (2, 7), (3, 7), (3, 8)]:
        grid[row][col] = 6
    for row, col in [(7, 1), (7, 2), (7, 3)]:
        grid[row][col] = 6
    grid[8][9] = grid[8][10] = 5
    assert MODULE.self_check(grid) == []
    return grid


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").open():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _normalized_rule_hash(text: str) -> str:
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def test_rule_hash_and_task_local_authority_are_exactly_synchronized():
    canonical = _canonical_row()["program_solution"]
    authority = json.loads(
        (ROOT / "data/base/solutions/banks/d3d681cdb82a/M51__49bfa2fd18b7.json").read_text()
    )["racket_target"]
    assert authority["raw_code"] == canonical
    assert authority["target_code"] == canonical
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical) == "5ee6c4df3ad5"


def test_all_canonical_inputs_pass_structural_check():
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            assert MODULE.self_check(pair["input"]) == []


def test_exact_override_boundaries_are_observable():
    cases = [
        {"grid_h": 9},
        {"grid_h": 16},
        {"grid_w": 10},
        {"grid_w": 16},
        {"blob_count": 3},
        {"blob_count": 4},
        {"target_size": 4},
        {"target_size": 7},
        {"target_on_edge": False},
        {"target_on_edge": True},
        {"gray_orientation": "horizontal"},
        {"gray_orientation": "vertical"},
        {"grid_h": 9, "grid_w": 10, "blob_count": 4, "target_size": 7},
        {"grid_h": 16, "grid_w": 16, "blob_count": 3, "target_size": 4},
    ]
    for case in cases:
        grid = MODULE.generate(1729, 11, difficulty="hard", **case)
        observed = MODULE.observe_overrides(grid)
        assert MODULE.self_check(grid) == []
        for name, value in case.items():
            assert observed[name] == value


def test_structural_mutations_are_rejected():
    valid = _valid_fixture()
    mutations = {}

    two_blobs = copy.deepcopy(valid)
    for col in (1, 2, 3):
        two_blobs[7][col] = 0
    mutations["two_blob_aliases_second_largest_to_smallest"] = two_blobs

    one_gray = copy.deepcopy(valid)
    one_gray[8][10] = 0
    mutations["one_cell_distractor"] = one_gray

    solid_target = copy.deepcopy(valid)
    solid_target[3][7] = solid_target[3][8] = 0
    solid_target[1][8] = solid_target[2][8] = 6
    mutations["solid_rectangle_target"] = solid_target

    diagonal_touch = copy.deepcopy(valid)
    for col in (1, 2, 3):
        diagonal_touch[7][col] = 0
    for row, col in [(4, 9), (5, 9), (5, 10)]:
        diagonal_touch[row][col] = 6
    mutations["diagonally_touching_components"] = diagonal_touch

    wrong_distractor = copy.deepcopy(valid)
    wrong_distractor[8][9] = wrong_distractor[8][10] = 4
    mutations["wrong_distractor_color"] = wrong_distractor

    for name, grid in mutations.items():
        assert MODULE.self_check(grid), name


def test_replay_freshness_and_global_random_state():
    state = random.getstate()
    first = MODULE.generate(314159, 7, difficulty="medium")
    assert random.getstate() == state
    second = MODULE.generate(314159, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_three_demo_schedule_eliminates_common_shortcuts():
    # The generator's internal predicate is the exact schedule invariant used
    # by the semantic census. Every three consecutive indices cover phases 0..2.
    for seed in range(100):
        for start in range(3):
            grids = [MODULE.generate(seed, start + offset) for offset in range(3)]
            assert all(MODULE._pedagogy_ok(grid, (start + offset) % 3) for offset, grid in enumerate(grids))


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(0, 0, nonexistent_axis=1)
