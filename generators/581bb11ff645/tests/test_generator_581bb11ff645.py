from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK = "581bb11ff645"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]


def canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK and row["source"] == "training":
            return row["train"] + row["test"]
    raise AssertionError("canonical row missing")


def independent_oracle(grid):
    height, width = len(grid), len(grid[0])
    groups = []
    start = None
    for col in range(width):
        has_red = any(grid[row][col] == 2 for row in range(height))
        if has_red and start is None:
            start = col
        elif not has_red and start is not None:
            groups.append((start, col - 1))
            start = None
    if start is not None:
        groups.append((start, width - 1))
    holes = [sum(grid[row][col] == 0 for row in range(height) for col in range(first, last + 1)) for first, last in groups]
    output = [[0] * width for _ in range(height)]
    for destination, source_index in zip(groups, sorted(range(len(groups)), key=lambda index: holes[index])):
        source = groups[source_index]
        for row in range(height):
            output[row][destination[0] : destination[0] + source[1] - source[0] + 1] = grid[row][source[0] : source[1] + 1]
    return output, tuple(groups), tuple(holes)


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
    expected, groups, holes = independent_oracle(grid)
    assert not analysis["errors"]
    assert analysis["scene_profile"] == profile
    assert analysis["output"] == expected
    assert analysis["facts"]["groups"] == groups
    assert analysis["facts"]["hole_counts"] == holes
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    changed = sum(before != after for input_row, output_row in zip(grid, expected) for before, after in zip(input_row, output_row))
    assert changed / (len(grid) * len(grid[0])) >= MODULE.MIN_SYNTHETIC_CHANGE_RATE


@pytest.mark.parametrize("count", [3, 4, 5])
@pytest.mark.parametrize("width", [2, 3, 4])
def test_count_and_width_profiles_are_literal(count, width):
    profile = f"groups{count}_width{width}"
    grid = MODULE.generate(53 + count + width, 3, difficulty="hard", scene_profile=profile)
    facts = MODULE._analysis(grid)["facts"]
    assert len(facts["groups"]) == count
    assert set(facts["group_widths"]) == {width}
    assert set(facts["hole_counts"]) == set(range(1, count + 1))


@pytest.mark.parametrize(
    "profile,expected",
    [
        ("reverse_ranks", (5, 4, 3, 2, 1)),
        ("adjacent_rank_swap", (2, 1, 3)),
        ("cyclic_ranks", (2, 3, 4, 1)),
    ],
)
def test_special_rank_orders_are_literal(profile, expected):
    grid = MODULE.generate(61 + len(profile), 4, difficulty="medium", scene_profile=profile)
    assert MODULE._analysis(grid)["facts"]["hole_counts"] == expected


def test_complete_group_patterns_move_into_fixed_slots():
    grid = MODULE.generate(67, 5, difficulty="hard", scene_profile="groups5_width4")
    facts = MODULE._analysis(grid)["facts"]
    output = MODULE.rule_mirror(grid)
    ranked_sources = [group for _, group in sorted(zip(facts["hole_counts"], facts["groups"]))]
    for destination, source in zip(facts["groups"], ranked_sources):
        for row in range(len(grid)):
            assert output[row][destination[0] : destination[1] + 1] == grid[row][source[0] : source[1] + 1]
    separator_columns = [col for col in range(len(grid[0])) if all(grid[row][col] == 0 for row in range(len(grid)))]
    assert all(all(output[row][col] == 0 for row in range(len(grid))) for col in separator_columns)


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(73, 6, difficulty="medium", scene_profile="cyclic_ranks")
    assert random.getstate() == state
    second = MODULE.generate(73, 6, difficulty="medium", scene_profile="cyclic_ranks")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 0
    assert MODULE.generate(73, 6, difficulty="medium", scene_profile="cyclic_ranks") == second


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 7 for _ in range(4)],
        [[0] * 7 for _ in range(31)],
        [[0] * 7 for _ in range(7)] + [[0] * 6],
        [[False] * 7 for _ in range(7)],
        [[1] * 7 for _ in range(7)],
    ],
)
def test_malformed_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


def test_wrong_groups_separators_widths_holes_and_identity_fail_closed():
    blank = [[0] * 11 for _ in range(7)]
    assert MODULE.self_check(blank)
    leading = MODULE.generate(81, 7, scene_profile="groups3_width3")
    leading = [[0] + row for row in leading]
    assert MODULE.self_check(leading)
    wide_gap = MODULE.generate(83, 8, scene_profile="groups3_width3")
    wide_gap = [row[:4] + [0] + row[4:] for row in wide_gap]
    assert MODULE.self_check(wide_gap)
    unequal = MODULE.generate(85, 9, scene_profile="groups3_width3")
    unequal = [row[:3] + row[4:] for row in unequal]
    assert MODULE.self_check(unequal)
    ascending = [[0] * 11 for _ in range(7)]
    for index, holes in enumerate((1, 2, 3)):
        start = index * 4
        for row in range(7):
            for col in range(start, start + 3):
                ascending[row][col] = 2
        for offset in range(holes):
            ascending[offset][start] = 0
    assert MODULE.self_check(ascending)


@pytest.mark.parametrize("kwargs", [{"scene_profile": "unknown"}, {"texture": "warm"}, {"difficulty": "expert"}])
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert set(MODULE.SCENE_PROFILES) == set(MODULE.AXES["scene_profile"]["valid"].split("|"))
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()
