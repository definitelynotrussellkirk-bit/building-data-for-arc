from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "a5df658a2503"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def test_canonical_inputs_and_outputs_match_structural_rule() -> None:
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        grid = pair["input"]
        original = copy.deepcopy(grid)
        assert MODULE.self_check(grid) == []
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert grid == original


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_boundary_overrides_are_realized(difficulty: str) -> None:
    for pair_count in (2, 3):
        grid = MODULE.generate(
            901,
            17,
            difficulty=difficulty,
            grid_h=7,
            grid_w=7,
            pair_count=pair_count,
        )
        assert (len(grid), len(grid[0])) == (7, 7)
        assert MODULE.observe_overrides(grid)["pair_count"] == pair_count
        assert MODULE.self_check(grid) == []


def test_self_check_rejects_four_targeted_impostors() -> None:
    grid = MODULE.generate(321, 0, difficulty="medium", pair_count=2)
    active = MODULE._fillable_pairs(grid)
    assert len(active) == 2
    assert MODULE.self_check(grid) == []

    missing_endpoint = copy.deepcopy(grid)
    r, c = active[0].a
    missing_endpoint[r][c] = 0
    assert MODULE.self_check(missing_endpoint)

    blocked_active_midpoint = copy.deepcopy(grid)
    mr, mc = active[0].midpoint
    blocked_active_midpoint[mr][mc] = 9 if active[0].color != 9 else 8
    assert MODULE.self_check(blocked_active_midpoint)

    distance_three_active = copy.deepcopy(grid)
    target = active[0]
    distance_three_active[target.b[0]][target.b[1]] = 0
    placed = False
    for dr in (-3, 3):
        for dc in (-3, 3):
            rr, cc = target.a[0] + dr, target.a[1] + dc
            if (
                0 <= rr < len(grid)
                and 0 <= cc < len(grid[0])
                and distance_three_active[rr][cc] == 0
            ):
                distance_three_active[rr][cc] = target.color
                placed = True
                break
        if placed:
            break
    if not placed:
        pytest.skip("chosen grid has no free distance-three relocation")
    assert MODULE.self_check(distance_three_active)

    one_orientation = copy.deepcopy(grid)
    remove = active[0]
    for r, c in (remove.a, remove.b):
        one_orientation[r][c] = 0
    assert MODULE.self_check(one_orientation)


def test_generation_is_deterministic_fresh_and_rng_pure() -> None:
    random.seed(887766)
    state_before = random.getstate()
    first = MODULE.generate(55, 8, difficulty="hard")
    state_after = random.getstate()
    second = MODULE.generate(55, 8, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9
    replay = MODULE.generate(55, 8, difficulty="hard")
    assert replay == second


def test_both_diagonal_branches_fire_and_only_midpoints_change() -> None:
    grid = MODULE.generate(77, 12, difficulty="easy", pair_count=2)
    pairs = MODULE._fillable_pairs(grid)
    assert {pair.orientation for pair in pairs} == {"down_right", "down_left"}

    output = MODULE.rule_mirror(grid)
    changed = {
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != output[r][c]
    }
    assert changed == {pair.midpoint for pair in pairs}
    for pair in pairs:
        r, c = pair.midpoint
        assert output[r][c] == pair.color


def test_three_step_schedule_contains_nonfiring_near_misses() -> None:
    modes = []
    for sample_index in range(3):
        grid = MODULE.generate(812, sample_index, difficulty="medium")
        output = MODULE.rule_mirror(grid)
        modes.append(MODULE.decoy_mode(sample_index))
        assert MODULE.self_check(grid) == []
        assert len(MODULE._fillable_pairs(grid)) in (2, 3)
        assert sum(value != 0 for row in grid for value in row) > 2 * len(
            MODULE._fillable_pairs(grid)
        )
        assert output != grid
    assert modes == list(MODULE.DECOY_MODES)

CANONICAL_MORPHOLOGY_PROFILES = {
    (6, 9, 4),
    (7, 7, 4),
    (8, 8, 4),
}


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_schedule_rehearses_canonical_morphology_in_every_band(
    difficulty: str,
) -> None:
    """Every third ordinary sample is a canonical-scale/palette anchor."""
    for sample_index in range(0, 12, 3):
        grid = MODULE.generate(1701, sample_index, difficulty=difficulty)
        profile = (
            len(grid),
            len(grid[0]),
            len({value for row in grid for value in row}),
        )
        assert profile in CANONICAL_MORPHOLOGY_PROFILES
        assert MODULE.self_check(grid) == []
