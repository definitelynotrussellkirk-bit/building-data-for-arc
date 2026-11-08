from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASK = "2d2455d1008d"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _pairs():
    row = _canonical_row()
    return row["train"] + [row["test"]]


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12]


def test_every_public_profile_replays_its_canonical_pair_exactly():
    pairs = _pairs()
    assert len(pairs) == len(MODULE.PUBLIC_PROFILES) == 5
    for profile, pair in zip(MODULE.PUBLIC_PROFILES, pairs):
        grid = MODULE.generate(0, 0, scene_profile=profile)
        assert grid == pair["input"]
        assert MODULE.rule_mirror(grid) == pair["output"]
        assert MODULE.canonical_profile_signature(grid) == profile
        assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_every_general_profile_is_valid_and_recoverable_in_every_band():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for profile_index, profile in enumerate(MODULE.GENERAL_PROFILES):
            for seed in range(30):
                grid = MODULE.generate(
                    100_000 * band_index + 1_000 * profile_index + seed,
                    seed * 31,
                    difficulty=band,
                    scene_profile=profile,
                )
                analysis = MODULE._analysis(grid)
                assert not analysis["errors"]
                assert analysis["scene_profile"] == profile
                assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


def test_default_generation_reaches_every_declared_profile():
    seen = {
        MODULE.observe_overrides(MODULE.generate(seed, seed * 37))["scene_profile"]
        for seed in range(6000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_one_distinct_repeated_marker_color_fills_only_zeros():
    grid = [
        [4, 4, 4, 4, 4],
        [4, 2, 0, 2, 4],
        [4, 0, 4, 0, 4],
        [4, 0, 0, 0, 4],
        [4, 4, 4, 4, 4],
    ]
    assert MODULE.rule_mirror(grid) == [
        [4, 4, 4, 4, 4],
        [4, 2, 2, 2, 4],
        [4, 2, 4, 2, 4],
        [4, 2, 2, 2, 4],
        [4, 4, 4, 4, 4],
    ]


def test_empty_and_multicolor_frames_are_unchanged_while_eligible_frame_fills():
    grid = [[0] * 14 for _ in range(5)]
    for col0 in (0, 5, 10):
        for row, col in MODULE._border(0, col0, 3, col0 + 3):
            grid[row][col] = 4
    grid[1][6] = 1
    grid[2][7] = 2
    grid[1][11] = 3
    output = MODULE.rule_mirror(grid)
    assert output[1][1] == output[2][2] == 0
    assert output[1][6] == 1 and output[2][7] == 2
    assert output[1][11] == output[1][12] == output[2][11] == output[2][12] == 3


def test_incomplete_yellow_shape_and_external_objects_are_preserved():
    grid = [[0] * 11 for _ in range(8)]
    interior = MODULE._draw_frame(grid, 1, 1, 5, 5)
    grid[2][2] = 6
    for col in range(7, 11):
        grid[1][col] = 4
    for row in range(1, 5):
        grid[row][7] = 4
    grid[7][10] = 8
    before_decoy = tuple(tuple(row[7:]) for row in grid[:5])
    output = MODULE.rule_mirror(grid)
    assert all(output[row][col] == 6 for row, col in interior)
    assert tuple(tuple(row[7:]) for row in output[:5]) == before_decoy
    assert output[7][10] == 8


def test_output_is_fresh_and_input_is_not_mutated():
    grid = MODULE.generate(777, 888, scene_profile="yellow_interior_obstacle")
    before = _frozen(grid)
    output = MODULE.rule_mirror(grid)
    assert _frozen(grid) == before
    assert output is not grid and output[0] is not grid[0]
    assert any(value == 4 for row in output for value in row)


def test_generated_rule_always_changes_only_zero_interior_cells():
    for seed in range(300):
        grid = MODULE.generate(seed, seed * 19)
        output = MODULE.rule_mirror(grid)
        frames, _ = MODULE._frame_records(grid)
        licensed = {
            cell
            for frame in frames
            if len(frame["marker_colors"]) == 1
            for cell in frame["interior"]
            if grid[cell[0]][cell[1]] == 0
        }
        changed = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] != output[row][col]
        }
        assert changed == licensed


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[10, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[0] * 31 for _ in range(3)],
        [[0] * 5 for _ in range(5)],
        [[4] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(2)] + [[0, 0, 4, 4, 0], [0, 0, 4, 4, 0]] + [[0] * 5],
        [[0, 0, 0], [0, 7, 0], [0, 0, 0]],
        [[0, 0, 0, 0], [0, 4, 4, 0], [0, 4, 4, 0], [0, 0, 0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_undeclared_impostors(grid):
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=10)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 9
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen
