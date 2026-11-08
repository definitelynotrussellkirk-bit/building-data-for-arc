from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as portable_canonical_pairs
from reviewer_support import find_root


TASK = "49f2e1c9f51a"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = find_root(__file__)


def canonical_pairs():
    return portable_canonical_pairs(TASK, root=ROOT, variant=0, labeled_only=True)


def line_cells(row0, col0, row1, col1):
    if row0 == row1:
        return [(row0, col) for col in range(min(col0, col1), max(col0, col1) + 1)]
    assert col0 == col1
    return [(row, col0) for row in range(min(row0, row1), max(row0, row1) + 1)]


def independent_oracle(grid):
    threes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    twos = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    r3a, r3b = min(r for r, _ in threes), max(r for r, _ in threes)
    c3a, c3b = min(c for _, c in threes), max(c for _, c in threes)
    r2a, r2b = min(r for r, _ in twos), max(r for r, _ in twos)
    c2a, c2b = min(c for _, c in twos), max(c for _, c in twos)
    horizontal = r3a == r3b
    dc = (1 if c2a + c2b >= c3a + c3b else -1) if horizontal else 0
    dr = 0 if horizontal else (1 if r2a + r2b > r3a + r3b else -1)
    start = (r3a, c3b if dc == 1 else c3a) if horizontal else (r3b if dr == 1 else r3a, c3a)
    target = (r2a, c2b if dc == 1 else c2a) if horizontal else (r2a if dr == 1 else r2b, c2a)
    row, col = start
    while 0 <= row + dr < len(grid) and 0 <= col + dc < len(grid[0]) and grid[row + dr][col + dc] == 0:
        row, col = row + dr, col + dc
    corner = row, col
    turn = (target[0], corner[1]) if horizontal else (corner[0], target[1])
    path = set(line_cells(*start, *corner) + line_cells(*corner, *turn) + line_cells(*turn, *target))
    output = copy.deepcopy(grid)
    for row, col in path:
        output[row][col] = 3
    for row, col in twos:
        output[row][col] = 2
    return output, path


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
    grid = MODULE.generate(12_000 + len(profile), 7, difficulty=band, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, _ = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}


@pytest.mark.parametrize("profile", [p for p in MODULE.GENERAL_PROFILES if p.endswith("blocked_cross")])
def test_blocked_profiles_stop_before_eight_and_cross_other_eights(profile):
    grid = MODULE.generate(23, 4, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["stop_value"] == 8
    assert facts["overwritten_eights"]
    stop = facts["stop_cell"]
    assert facts["output"][stop[0]][stop[1]] == 8
    assert all(facts["output"][r][c] == 3 for r, c in facts["overwritten_eights"])


@pytest.mark.parametrize("profile", [p for p in MODULE.GENERAL_PROFILES if p.endswith("border")])
def test_border_profiles_reach_edge_before_turning(profile):
    grid = MODULE.generate(29, 2, difficulty="medium", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["stop_cell"] is None
    row, col = facts["corner1"]
    assert row in (0, len(grid) - 1) or col in (0, len(grid[0]) - 1)
    assert facts["overwritten_eights"]


@pytest.mark.parametrize("profile", ["horizontal_aligned_target", "vertical_aligned_target"])
def test_aligned_target_itself_stops_initial_extension(profile):
    grid = MODULE.generate(31, 3, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert facts["stop_value"] == 2
    assert set(facts["twos"]) <= {(r, c) for r, row in enumerate(facts["output"]) for c, value in enumerate(row) if value == 2}


def test_only_path_cells_change_and_red_is_restored():
    grid = MODULE.generate(41, 5, difficulty="hard", scene_profile="horizontal_left_blocked_cross")
    expected, path = independent_oracle(grid)
    actual = MODULE.rule_mirror(grid)
    changed = {(r, c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != actual[r][c]}
    assert actual == expected
    assert changed <= path
    for row, col in MODULE._analysis(grid)["facts"]["twos"]:
        assert actual[row][col] == 2


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    before = random.getstate()
    first = MODULE.generate(77, 9, difficulty="medium", scene_profile="vertical_up_blocked_cross")
    assert random.getstate() == before
    second = MODULE.generate(77, 9, difficulty="medium", scene_profile="vertical_up_blocked_cross")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(77, 9, difficulty="medium", scene_profile="vertical_up_blocked_cross") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 8 for _ in range(8)],
        [[0] * 8 for _ in range(7)],
        [[0] * 8 for _ in range(31)],
        [[0] * 8 for _ in range(8)] + [[0] * 7],
        [[False] * 8 for _ in range(8)],
        [[9] * 8 for _ in range(8)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_missing_noise_and_bad_segments_fail_closed():
    no_noise = [[0] * 10 for _ in range(10)]
    no_noise[2][1:3] = [3, 3]
    no_noise[7][7:9] = [2, 2]
    assert MODULE.self_check(no_noise)
    bent = copy.deepcopy(no_noise)
    bent[2][2], bent[3][1] = 0, 3
    bent[0][0] = 8
    assert MODULE.self_check(bent)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "blocked"},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
