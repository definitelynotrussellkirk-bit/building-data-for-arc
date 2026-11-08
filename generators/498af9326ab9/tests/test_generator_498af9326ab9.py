from __future__ import annotations

import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK = "498af9326ab9"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def _canonical_row():
    with canonical_path(ROOT).open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK)


def _pairs():
    row = _canonical_row()
    test = row["test"]
    return row["train"] + ([test] if isinstance(test, dict) else test)


def _frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_matches_canonical_program():
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(rule.encode()).hexdigest()[:12] == "067c9281e33e"


def test_public_profiles_replay_every_canonical_pair_exactly():
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
        for seed in range(4000)
    }
    assert seen == set(MODULE.SCENE_PROFILES)


def test_union_membership_is_exact_distance_sum_equality():
    for seed in range(500):
        grid = MODULE.generate(seed, seed * 19)
        facts = MODULE._analysis(grid)["facts"]
        expected = {
            cell
            for cell, distance in facts["from_start"].items()
            if grid[cell[0]][cell[1]] == 0
            and cell in facts["from_goal"]
            and distance + facts["from_goal"][cell] == facts["optimal_distance"]
        }
        assert set(facts["union"]) == expected
        output = MODULE.rule_mirror(grid)
        assert {(row, col) for row, values in enumerate(output) for col, value in enumerate(values) if value == 8} == expected


def test_open_rectangle_marks_all_monotone_shortest_path_cells():
    grid = MODULE.generate(4, 5, scene_profile="open_rectangle")
    facts = MODULE._analysis(grid)["facts"]
    row0, row1 = sorted((facts["start"][0], facts["goal"][0]))
    col0, col1 = sorted((facts["start"][1], facts["goal"][1]))
    rectangle_zeros = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
        if grid[row][col] == 0
    }
    assert set(facts["union"]) == rectangle_zeros


@pytest.mark.parametrize("profile", ["horizontal_line", "vertical_line"])
def test_aligned_markers_produce_one_straight_shortest_path(profile):
    facts = MODULE._analysis(MODULE.generate(9, 10, scene_profile=profile))["facts"]
    if profile == "horizontal_line":
        assert len({row for row, _ in facts["union"]}) == 1
    else:
        assert len({col for _, col in facts["union"]}) == 1
    assert len(facts["union"]) == facts["optimal_distance"] - 1


def test_symmetric_horizontal_block_includes_top_and_bottom_detours():
    facts = MODULE._analysis(MODULE.generate(17, 18, scene_profile="symmetric_block_horizontal"))["facts"]
    row0, _, row1, _ = facts["wall_bbox"]
    rows = {row for row, _ in facts["union"]}
    assert min(rows) < row0 and max(rows) > row1


@pytest.mark.parametrize(
    ("profile", "side"),
    [("top_shorter_block", "top"), ("bottom_shorter_block", "bottom")],
)
def test_asymmetric_horizontal_block_uses_only_shorter_side(profile, side):
    facts = MODULE._analysis(MODULE.generate(23, 24, scene_profile=profile))["facts"]
    row0, _, row1, _ = facts["wall_bbox"]
    rows = {row for row, _ in facts["union"]}
    assert (min(rows) < row0) == (side == "top")
    assert (max(rows) > row1) == (side == "bottom")


def test_symmetric_vertical_block_includes_left_and_right_detours():
    facts = MODULE._analysis(MODULE.generate(31, 32, scene_profile="symmetric_block_vertical"))["facts"]
    _, col0, _, col1 = facts["wall_bbox"]
    cols = {col for _, col in facts["union"]}
    assert min(cols) < col0 and max(cols) > col1


@pytest.mark.parametrize(
    ("profile", "side"),
    [("left_shorter_block", "left"), ("right_shorter_block", "right")],
)
def test_asymmetric_vertical_block_uses_only_shorter_side(profile, side):
    facts = MODULE._analysis(MODULE.generate(41, 42, scene_profile=profile))["facts"]
    _, col0, _, col1 = facts["wall_bbox"]
    cols = {col for _, col in facts["union"]}
    assert (min(cols) < col0) == (side == "left")
    assert (max(cols) > col1) == (side == "right")


def test_twin_gates_puts_both_equal_gaps_on_shortest_path_union():
    grid = MODULE.generate(51, 52, scene_profile="twin_gates")
    facts = MODULE._analysis(grid)["facts"]
    barrier = facts["wall_bbox"][1]
    gates = {(row, barrier) for row in range(len(grid)) if grid[row][barrier] == 0}
    assert len(gates) == 2
    assert gates <= set(facts["union"])


def test_only_union_zeros_change_and_walls_and_markers_are_immutable():
    for seed in range(300):
        grid = MODULE.generate(80_000 + seed, seed)
        facts = MODULE._analysis(grid)["facts"]
        output = MODULE.rule_mirror(grid)
        union = set(facts["union"])
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                assert output[row][col] == (8 if (row, col) in union else grid[row][col])


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(987654)
    before = random.getstate()
    first = MODULE.generate(111, 222, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(111, 222, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 5
    assert MODULE.generate(111, 222, difficulty="hard") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0, 1], [0]],
        [[True] + [0] * 4 for _ in range(5)],
        [[9] + [0] * 4 for _ in range(5)],
        [[0] * 31 for _ in range(5)],
        [[0] * 5 for _ in range(4)],
        [[0] * 7 for _ in range(7)],
        [[1, 1, 0, 0, 0, 2, 0]] + [[0] * 7 for _ in range(6)],
    ],
)
def test_self_check_rejects_malformed_or_ruleless_impostors(grid):
    assert MODULE.self_check(grid)


def test_self_check_rejects_unreachable_markers():
    grid = [[0] * 7 for _ in range(7)]
    grid[1][1], grid[5][5] = 1, 2
    for row in range(7):
        grid[row][3] = 5
    assert MODULE.self_check(grid)


def test_unknown_difficulty_profile_and_axis_fail_closed():
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, scene_profile="not_real")
    with pytest.raises(ValueError):
        MODULE.generate(0, 0, grid_h=9)


def test_public_returns_are_fresh():
    first = MODULE.generate(1, 2, scene_profile="public_1")
    frozen = _frozen(first)
    first[0][0] = 5
    assert _frozen(MODULE.generate(1, 2, scene_profile="public_1")) == frozen


def test_axis_contract_is_literal_minimal_and_complete():
    assert set(MODULE.AXES) == {"scene_profile"}
    valid = set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert valid == set(MODULE.SCENE_PROFILES)
    assert not MODULE.HELPFUL_TEXTURES and not MODULE.DEGENERATE_TEXTURES
