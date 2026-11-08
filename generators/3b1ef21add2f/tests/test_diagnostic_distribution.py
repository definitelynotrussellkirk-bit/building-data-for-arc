"""Default lesson coverage and the independently discovered red 2-core rival."""
from copy import deepcopy

import pytest

from oracle_3b1ef21add2f import (
    diagnostic_features, red_components, red_windows, solve, window_cells,
)


def _rich_features(grid):
    """Keep the five semantic contrasts while allowing cyclic red distractors."""
    features = diagnostic_features(grid)
    del features["red_tetromino_without_square"]
    covered = window_cells(grid)
    features["large_red_without_square"] = any(
        len(component) >= 4 and not component & covered
        for component in red_components(grid))
    return features


def _red_two_core(grid):
    """Wrong rule: recolor the 4-neighbor red graph's maximal degree-2 core.

    Repeated pruning is necessary: removing a leaf can expose another leaf.
    This helper uses only original pixels, with no generator or graph helpers.
    """
    core = {(row, col) for row, values in enumerate(grid)
            for col, value in enumerate(values) if value == 2}
    while True:
        leaves = set()
        for row, col in core:
            degree = sum(neighbor in core for neighbor in (
                (row - 1, col), (row + 1, col),
                (row, col - 1), (row, col + 1)))
            if degree < 2:
                leaves.add((row, col))
        if not leaves:
            break
        core.difference_update(leaves)
    return [[3 if (row, col) in core else value
             for col, value in enumerate(values)]
            for row, values in enumerate(grid)]


@pytest.mark.parametrize("grid, expected", [
    ([[2, 2, 2], [2, 0, 2], [2, 2, 2]],
     [[3, 3, 3], [3, 0, 3], [3, 3, 3]]),
    ([[2, 2, 2, 2], [2, 2, 0, 0]],
     [[3, 3, 2, 2], [3, 3, 0, 0]]),
    ([[2, 2], [0, 2], [0, 2]], [[2, 2], [0, 2], [0, 2]]),
    ([[4, 4, 3], [4, 4, 2]], [[4, 4, 3], [4, 4, 2]]),
], ids=["hollow-ring-survives", "recursive-tail-pruning",
        "red-tree-disappears", "other-colors-preserved"])
def test_independent_two_core_rival_has_literal_graph_behavior(grid, expected):
    before = deepcopy(grid)
    output = _red_two_core(grid)
    assert output == expected
    assert grid == before
    assert output is not grid
    assert all(new is not old for new, old in zip(output, grid))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start_residue", [0, 1, 2])
def test_period_three_schedule_preserves_every_four_draw_lesson(
        generator, difficulty, start_residue):
    for seed in (0, 1, 17, 101):
        for base in (0, 3, 99):
            start = base + start_residue
            observed_rich = []
            observed_anchors = []
            for index in range(start, start + 4):
                grid = generator.generate(seed, index, difficulty=difficulty)
                call = (seed, index, difficulty)
                features = _rich_features(grid)
                covered = window_cells(grid)
                simple = bool(red_windows(grid)) and not features["overlap"] and any(
                    len(part) == 4 and part <= covered for part in red_components(grid))
                rich = all(features.values())
                observed_anchors.append(simple)
                observed_rich.append(rich)
                if index % 3 == 0:
                    assert simple, (call, features)
                else:
                    assert rich, (call, features)
                assert 7 <= len(grid) <= 16
                assert 7 <= len(grid[0]) <= 16
                assert len(red_windows(grid)) <= 8
                assert generator.self_check(grid) == []
                output = solve(grid)
                assert any(old == new == 2 for row_a, row_b in zip(grid, output)
                           for old, new in zip(row_a, row_b))
            assert sum(observed_anchors) >= 1, (seed, start, difficulty)
            assert sum(observed_rich) >= 2, (seed, start, difficulty)
            for held_out in range(4):
                assert any(rich for index, rich in enumerate(observed_rich)
                           if index != held_out), (seed, start, difficulty, held_out)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_rich_scene_actually_refutes_independent_two_core(generator, difficulty):
    for seed in (0, 1, 17, 101):
        for base in (0, 3, 99):
            for offset in (1, 2):
                index = base + offset
                grid = generator.generate(seed, index, difficulty=difficulty)
                before = deepcopy(grid)
                expected = solve(grid)
                rival = _red_two_core(grid)
                assert rival != expected, (seed, index, difficulty)
                # The intended new evidence is surviving cyclic red structure
                # outside every red square, not an unrelated color difference.
                assert any(old == correct == 2 and predicted == 3
                           for row_a, row_b, row_c in zip(grid, expected, rival)
                           for old, correct, predicted in zip(row_a, row_b, row_c))
                assert grid == before


def test_default_seed_and_index_variation_is_not_a_single_fixed_fixture(generator):
    signatures = set()
    for seed in range(16):
        for index in range(4):
            grid = generator.generate(seed, index)
            signatures.add(tuple(map(tuple, grid)))
    assert len(signatures) >= 32
