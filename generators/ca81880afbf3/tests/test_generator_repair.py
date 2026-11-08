"""Regressions for the repaired square-vs-rectangle base generator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "ca81880afbf3"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("reviewed_ca81880afbf3_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)


def _frame_bboxes(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5}
    boxes = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in remaining:
                    remaining.remove(q)
                    cells.add(q)
                    stack.append(q)
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        boxes.append((min(rs), min(cs), max(rs)-min(rs)+1, max(cs)-min(cs)+1))
    return sorted(boxes)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_ordinary_generation_is_always_in_domain(band):
    for seed in (0, 1, 17):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert gen.self_check(grid) == []


@pytest.mark.parametrize("bias", ["scattered", "row_aligned", "col_aligned", "diagonal"])
def test_exact_controls_are_realized_and_each_bias_is_operational(bias):
    grid = gen.generate(
        19, 3, difficulty="easy", grid_h=16, grid_w=20,
        n_square=2, n_rect=2, square_size=3, rect_h=3, rect_w=5,
        position_bias=bias,
    )
    assert (len(grid), len(grid[0])) == (16, 20)
    boxes = _frame_bboxes(grid)
    assert sorted((height, width) for _, _, height, width in boxes) == [
        (3, 3), (3, 3), (3, 5), (3, 5)
    ]
    assert gen.self_check(grid) == []


def test_four_helpful_biases_produce_four_distinct_exact_layouts():
    grids = {
        bias: gen.generate(
            31, 2, grid_h=16, grid_w=20, n_square=2, n_rect=2,
            square_size=3, rect_h=3, rect_w=5, position_bias=bias,
        )
        for bias in gen.POSITION_BIASES
    }
    assert len({tuple(map(tuple, grid)) for grid in grids.values()}) == 4


@pytest.mark.parametrize("height,width", [(5, 9), (16, 20)])
def test_declared_dimension_boundaries_are_exact_when_constructible(height, width):
    grid = gen.generate(
        7, 1, difficulty="hard", grid_h=height, grid_w=width,
        square_size=3, rect_h=3, rect_w=4,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


def test_impossible_exact_geometry_is_rejected_not_clipped_or_dropped():
    with pytest.raises(ValueError):
        gen.generate(
            0, 0, grid_h=5, grid_w=9, n_square=2, n_rect=2,
            square_size=6, rect_h=5, rect_w=7,
        )


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", -1])
def test_seed_is_a_nonnegative_literal_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_is_a_nonnegative_literal_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad_index)


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "unknown"])
def test_difficulty_is_strict(bad_difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize("overrides", [
    {"grid_h": "5"}, {"grid_w": 10.0}, {"n_square": True},
    {"n_rect": 1.75}, {"square_size": "4"}, {"rect_h": 3.0},
    {"rect_w": False}, {"position_bias": "unknown"},
    {"texture": "unknown"}, {"unknown_axis": 1},
])
def test_bad_override_values_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_conflicting_texture_alias_and_position_bias_are_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, texture="row_aligned", position_bias="diagonal")


def test_every_canonical_input_remains_in_domain():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair["input"]) == []


def test_rule_hash_is_pinned_to_active_canonical_authority():
    assert gen.RULE_HASH == "b9bced028d0a"


@pytest.mark.parametrize("grid", [
    [[5] * 9 for _ in range(5)],
    [[0] * 9 for _ in range(5)],
    [[5] + [0] * 8] + [[0] * 9 for _ in range(4)],
    [[5, 5] + [0] * 7, [5, 5] + [0] * 7] + [[0] * 9 for _ in range(3)],
])
def test_self_check_rejects_minimal_impostors(grid):
    assert gen.self_check(grid)


def test_authoring_only_single_family_degenerates_do_not_pass_ordinary_self_check():
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, grid_h=8, grid_w=12, texture=texture)
        assert gen.self_check(grid)


def test_exact_numeric_controls_can_be_observed_from_generated_grid():
    expected = {
        "grid_h": 16,
        "grid_w": 20,
        "n_square": 2,
        "n_rect": 2,
        "square_size": 3,
        "rect_h": 4,
        "rect_w": 6,
    }
    grid = gen.generate(
        73,
        5,
        position_bias="scattered",
        **expected,
    )

    assert gen.observe_overrides(grid) == expected
