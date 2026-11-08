from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "55ba26e599d3"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and row["source"] == "training":
            return row["train"] + row["test"]
    raise AssertionError("canonical row missing")


def independent_oracle(grid):
    endpoints = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    (r1, c1), (r2, c2) = endpoints
    dr, dc = r2 - r1, c2 - c1
    steps = max(abs(dr), abs(dc))
    path = [(round(r1 + i * dr / steps), round(c1 + i * dc / steps)) for i in range(steps + 1)]
    output = copy.deepcopy(grid)
    for row, col in path:
        if grid[row][col] == 0:
            output[row][col] = 2
        elif grid[row][col] == 1:
            output[row][col] = 3
    return output, tuple(endpoints), tuple(path)


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
    grid = MODULE.generate(40_000 + len(profile), 17, difficulty=band, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    expected, endpoints, path = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert analysis["facts"]["endpoints"] == endpoints
    assert analysis["facts"]["path"] == path
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    changed = sum(before != after for input_row, output_row in zip(grid, expected) for before, after in zip(input_row, output_row))
    assert changed / (len(grid) * len(grid[0])) >= MODULE.MIN_SYNTHETIC_CHANGE_RATE


@pytest.mark.parametrize("profile", MODULE.GENERAL_PROFILES)
def test_profile_geometry_is_recoverable(profile):
    grid = MODULE.generate(53 + len(profile), 3, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    height, width = len(grid), len(grid[0])
    first, second = facts["endpoints"]
    on_border = lambda point: point[0] in (0, height - 1) or point[1] in (0, width - 1)
    if profile.startswith("border_"):
        assert on_border(first) and on_border(second)
    else:
        assert not on_border(first) and not on_border(second)
    assert MODULE._geometry_profile(grid, facts["endpoints"]) == profile


def test_round_half_steps_use_ties_to_even_coordinates():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][0] = grid[2][4] = 2
    grid[1][2] = 1
    analysis = MODULE._analysis(grid)
    assert not analysis["errors"]
    assert analysis["facts"]["path"] == ((0, 0), (0, 1), (1, 2), (2, 3), (2, 4))
    assert analysis["output"][0][1] == analysis["output"][2][3] == 2
    assert analysis["output"][1][2] == 3


def test_only_dda_path_changes_and_both_mappings_are_witnessed():
    grid = MODULE.generate(61, 4, difficulty="hard", scene_profile="border_steep_down_left")
    analysis = MODULE._analysis(grid)
    path = set(analysis["facts"]["path"])
    changes = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != analysis["output"][r][c]}
    assert changes == path - set(analysis["facts"]["endpoints"])
    assert {analysis["output"][r][c] for r, c in changes} == {2, 3}
    assert all(analysis["output"][r][c] == value for r, row in enumerate(grid) for c, value in enumerate(row) if (r, c) not in path)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="interior_down_left")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="interior_down_left")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 2
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="interior_down_left") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[0] * 5 for _ in range(31)],
        [[0] * 5 for _ in range(5)] + [[0] * 4],
        [[False] * 5 for _ in range(5)],
        [[3] * 5 for _ in range(5)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_wrong_endpoint_count_missing_mapping_and_undeclared_geometry_fail_closed():
    one = [[0] * 7 for _ in range(7)]
    one[0][0] = 2
    assert MODULE.self_check(one)
    three = copy.deepcopy(one)
    three[3][3] = three[6][6] = 2
    assert MODULE.self_check(three)
    no_blue_path = [[0] * 7 for _ in range(7)]
    no_blue_path[0][0] = no_blue_path[6][6] = 2
    assert MODULE.self_check(no_blue_path)
    mixed_boundary = [[0] * 7 for _ in range(7)]
    mixed_boundary[0][0] = mixed_boundary[5][5] = 2
    mixed_boundary[1][1] = 1
    assert MODULE.self_check(mixed_boundary)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "diagonal"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
