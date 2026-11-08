from __future__ import annotations

import importlib
import random
from collections import Counter

import pytest


TASK = "7c7796f15a18"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def independent_components(grid):
    height, width = len(grid), len(grid[0])
    seen, result = set(), []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            seen.add((start_row, start_col))
            cells, frontier = {(start_row, start_col)}, [(start_row, start_col)]
            while frontier:
                row, col = frontier.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbour = row + dr, col + dc
                    if 0 <= neighbour[0] < height and 0 <= neighbour[1] < width and neighbour not in seen and grid[neighbour[0]][neighbour[1]] == color:
                        seen.add(neighbour)
                        cells.add(neighbour)
                        frontier.append(neighbour)
            result.append((color, cells))
    return result


def independent_oracle(grid):
    output = [row[:] for row in grid]
    for _, cells in independent_components(grid):
        color = len(cells) if len(cells) <= 4 else 6
        for row, col in cells:
            output[row][col] = color
    return output


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", MODULE.SCENE_PROFILES)
def test_every_profile_in_every_band(profile, difficulty):
    grid = MODULE.generate(10_000 + len(profile), 7, difficulty=difficulty, scene_profile=profile)
    analysis = MODULE._analysis(grid)
    assert analysis["errors"] == []
    assert analysis["scene_profile"] == profile
    assert MODULE.observe_overrides(grid) == {"scene_profile": profile}
    assert MODULE.rule_mirror(grid) == independent_oracle(grid)
    sizes = set(analysis["facts"]["sizes"])
    assert {1, 2, 3, 4} <= sizes and any(size >= 5 for size in sizes)


def test_mixed_palette_proves_input_color_is_irrelevant():
    grid = MODULE.generate(21, 2, scene_profile="mixed_palette")
    analysis = MODULE._analysis(grid)
    assert analysis["facts"]["input_color_count"] == 4
    output = MODULE.rule_mirror(grid)
    assert {value for row in output for value in row if value} == {1, 2, 3, 4, 6}


def test_diagonal_same_color_objects_remain_separate():
    grid = MODULE.generate(31, 3, scene_profile="diagonal_touch")
    facts = MODULE._analysis(grid)["facts"]
    assert facts["diagonal_contacts"] >= 1
    assert facts["sizes"] == (1, 2, 3, 4, 5)


def test_every_large_size_maps_to_six():
    grid = MODULE.generate(41, 4, scene_profile="large_bucket")
    output = MODULE.rule_mirror(grid)
    for _, cells in independent_components(grid):
        expected = len(cells) if len(cells) <= 4 else 6
        assert {output[row][col] for row, col in cells} == {expected}
    assert {5, 6, 7, 8} <= set(MODULE._analysis(grid)["facts"]["sizes"])


def test_same_size_components_share_output_color_across_input_colors():
    grid = MODULE.generate(51, 5, scene_profile="mixed_palette")
    output = MODULE.rule_mirror(grid)
    buckets = {}
    for input_color, cells in independent_components(grid):
        size = len(cells)
        row, col = next(iter(cells))
        buckets.setdefault(size, set()).add((input_color, output[row][col]))
    for size, witnesses in buckets.items():
        assert {out for _, out in witnesses} == {size if size <= 4 else 6}


def test_determinism_fresh_returns_and_global_rng_independence():
    random.seed(991)
    state = random.getstate()
    first = MODULE.generate(61, 6, difficulty="hard", scene_profile="dense_contest")
    assert random.getstate() == state
    second = MODULE.generate(61, 6, difficulty="hard", scene_profile="dense_contest")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert MODULE.generate(61, 6, difficulty="hard", scene_profile="dense_contest") == second


def test_default_prior_reaches_every_profile_and_is_diverse():
    for difficulty in ("easy", "medium", "hard"):
        grids = [MODULE.generate(70_000 + seed, seed, difficulty=difficulty) for seed in range(700)]
        profiles = [MODULE._analysis(grid)["scene_profile"] for grid in grids]
        outputs = [MODULE.rule_mirror(grid) for grid in grids]
        assert set(profiles) == set(MODULE.SCENE_PROFILES)
        assert len({tuple(map(tuple, grid)) for grid in grids}) == 700
        assert len({tuple(map(tuple, output)) for output in outputs}) == 700
        assert all(not MODULE.self_check(grid) for grid in grids)


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 5 for _ in range(4)],
        [[False] * 5 for _ in range(5)],
        [[10] * 5 for _ in range(5)],
        [[0] * 5 for _ in range(5)],
        [[5] * 5 for _ in range(5)],
    ],
)
def test_malformed_or_semantically_incomplete_grids_fail_closed(grid):
    assert MODULE.self_check(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"texture": "single_object"},
        {"grid_h": 12},
        {"n_objects": 12},
        {"difficulty": "expert"},
    ],
)
def test_unknown_controls_fail_closed(kwargs):
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, **kwargs)


def test_axis_contract_is_literal_and_minimal():
    assert set(MODULE.AXES) == {"scene_profile"}
    assert tuple(MODULE.AXES["scene_profile"]["valid"].split("|")) == MODULE.SCENE_PROFILES
    assert MODULE.HELPFUL_TEXTURES == MODULE.DEGENERATE_TEXTURES == ()


def test_size_bucket_counts_are_observable():
    grid = MODULE.generate(81, 8, scene_profile="same_color_separate")
    assert MODULE._analysis(grid)["facts"]["size_counts"] == Counter({1: 2, 2: 2, 3: 2, 4: 2, 5: 2})


def test_rule_hash_matches_authored_base_authority():
    assert MODULE.RULE_HASH == "760ae845bd82"
