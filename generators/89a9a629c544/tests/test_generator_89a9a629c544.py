from __future__ import annotations

import collections
from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "89a9a629c544"
ROOT = find_root(__file__)
generator, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def colors(grid):
    seen = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.append(value)
    return seen


def cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def flip_mask(mask, axis="ud"):
    rs = [r for r, _ in mask]
    cs = [c for _, c in mask]
    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
    if axis == "ud":
        return {(r1 + r2 - r, c) for r, c in mask}
    return {(r, c1 + c2 - c) for r, c in mask}


def independent_flip(grid, axis="ud"):
    result = [[0 for _ in row] for row in grid]
    occupied = set()
    for color in colors(grid):
        target = flip_mask(cells(grid, color), axis)
        assert not occupied & target, "independent target layers overlap"
        occupied |= target
        for r, c in target:
            result[r][c] = color
    return result


def sequential_flip(grid, axis="ud"):
    result = deepcopy(grid)
    for color in colors(grid):
        current = cells(result, color)
        if not current:
            continue
        target = flip_mask(current, axis)
        for r, row in enumerate(result):
            for c, value in enumerate(row):
                if value == color:
                    result[r][c] = 0
        for r, c in target:
            result[r][c] = color
    return result


def test_retained_collision_seed_preserves_every_layer_independently():
    grid = generator.generate(100_004, 4, difficulty="easy")
    assert generator.self_check(grid) == []
    expected = independent_flip(grid)
    actual = sequential_flip(grid)
    assert actual == expected
    assert collections.Counter(v for row in actual for v in row if v) == collections.Counter(
        v for row in grid for v in row if v
    )


def test_self_check_enforces_declared_semantic_invariants():
    monochrome = [[1, 0, 0], [0, 1, 0], [0, 0, 0]]
    symmetric = [[1, 1, 0], [0, 0, 0], [2, 2, 0]]
    collision = [[1, 1, 0], [1, 2, 0], [0, 0, 0]]

    assert any("two" in error or "colors" in error for error in generator.self_check(monochrome))
    assert any("asymmetric" in error for error in generator.self_check(symmetric))
    assert any("collision" in error or "independent" in error for error in generator.self_check(collision))


@pytest.mark.parametrize("difficulty", ["easy", None, "medium", "hard"])
def test_ordinary_draws_are_collision_safe_informative_and_deterministic(difficulty):
    for sample_index in range(250):
        seed = 710_000 + sample_index
        first = generator.generate(seed, sample_index * 19 + 7, difficulty=difficulty)
        second = generator.generate(seed, sample_index * 19 + 7, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert first[0] is not second[0]
        assert generator.self_check(first) == []
        assert len(colors(first)) >= 2
        assert sequential_flip(first) == independent_flip(first)


def test_layout_and_boundary_overrides_still_return_lawful_scenes():
    for index, layout in enumerate(generator.COLOR_LAYOUTS):
        grid = generator.generate(
            880 + index,
            index,
            grid_h=5,
            grid_w=5,
            n_colors=5,
            color_layout=layout,
            layer_density=0.7,
        )
        assert len(grid) == 5 and len(grid[0]) == 5
        assert generator.self_check(grid) == []
        assert sequential_flip(grid) == independent_flip(grid)


def test_python_rule_mirror_matches_every_labeled_canonical_pair_without_mutation():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
