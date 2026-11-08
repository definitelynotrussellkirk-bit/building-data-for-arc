from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "554712910457"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row["train"] + row["test"]
    raise AssertionError("canonical row missing")


def independent_oracle(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    green = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    output = copy.deepcopy(grid)
    red_fill, green_fill, ties = set(), set(), set()
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                continue
            d2 = abs(row - red[0]) + abs(col - red[1])
            d3 = abs(row - green[0]) + abs(col - green[1])
            if d2 < d3:
                output[row][col] = 2
                red_fill.add((row, col))
            elif d3 < d2:
                output[row][col] = 3
                green_fill.add((row, col))
            else:
                ties.add((row, col))
    return output, red_fill, green_fill, ties


@pytest.mark.parametrize("index,profile", list(enumerate(MODULE.PUBLIC_PROFILES)))
def test_exact_public_replay(index, profile):
    pair = canonical_pairs()[index]
    grid = MODULE.generate(100 + index, index, scene_profile=profile)
    assert grid == pair["input"]
    assert MODULE.rule_mirror(grid) == pair["output"]
    assert MODULE.canonical_profile_signature(grid) == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_every_general_profile_in_every_band(profile, band):
    grid = MODULE.generate(30_000 + len(profile), 13, difficulty=band, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, red_fill, green_fill, ties = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert red_fill and green_fill
    assert set(analysis["facts"]["ties"]) == ties
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("profile", ["horizontal_even_tie", "vertical_even_tie"])
def test_even_aligned_seeds_create_complete_bisector(profile):
    grid = MODULE.generate(41, 2, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    red, green = facts["red"], facts["green"]
    ties = set(facts["ties"])
    if profile.startswith("horizontal"):
        midpoint = (red[1] + green[1]) // 2
        expected = {(row, midpoint) for row in range(len(grid)) if grid[row][midpoint] == 0}
    else:
        midpoint = (red[0] + green[0]) // 2
        expected = {(midpoint, col) for col in range(len(grid[0])) if grid[midpoint][col] == 0}
    assert ties == expected and ties


@pytest.mark.parametrize("profile", ["horizontal_odd_no_tie", "vertical_odd_no_tie"])
def test_odd_aligned_seeds_have_no_tie_cells(profile):
    grid = MODULE.generate(43, 3, difficulty="hard", scene_profile=profile)
    assert not MODULE._analysis(grid)["facts"]["ties"]
    assert all(value != 0 for row in MODULE.rule_mirror(grid) for value in row if value in (0, 2, 3))


@pytest.mark.parametrize("profile", ["down_right_equal", "down_right_unequal", "down_left_equal", "down_left_unequal", "up_right_equal", "up_left_equal"])
def test_diagonal_profiles_retain_nonempty_tie_boundaries(profile):
    grid = MODULE.generate(47, 5, difficulty="medium", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["ties"]
    assert all(facts["output"][r][c] == 0 for r, c in facts["ties"])


def test_every_nonzero_cell_is_preserved_and_decoys_do_not_block_fill():
    grid = MODULE.generate(51, 7, difficulty="hard", scene_profile="down_right_unequal")
    output = MODULE.rule_mirror(grid)
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["decoys"]) >= 3
    assert len({grid[r][c] for r, c in facts["decoys"]}) >= 2
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                assert output[row][col] == value


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(887)
    state = random.getstate()
    first = MODULE.generate(61, 8, difficulty="medium", scene_profile="up_left_equal")
    assert random.getstate() == state
    second = MODULE.generate(61, 8, difficulty="medium", scene_profile="up_left_equal")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 4
    assert MODULE.generate(61, 8, difficulty="medium", scene_profile="up_left_equal") == second


@pytest.mark.parametrize("grid", [[], [[]], [[0] * 8 for _ in range(5)], [[0] * 7 for _ in range(31)], [[0] * 8 for _ in range(8)] + [[0] * 7], [[False] * 8 for _ in range(8)], [[4] * 8 for _ in range(8)]])
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_missing_markers_and_inadequate_decoys_fail_closed():
    missing = [[0] * 10 for _ in range(8)]
    assert MODULE.self_check(missing)
    sparse = [[0] * 10 for _ in range(8)]
    sparse[1][1], sparse[6][8], sparse[0][0] = 2, 3, 5
    assert MODULE.self_check(sparse)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "varied"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
