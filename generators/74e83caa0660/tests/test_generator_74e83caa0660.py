"""Contract and geometry regressions for 74e83caa0660."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
GENERATOR = HOME / "generator.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generator_74e83caa0660_subject", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def g():
    return load_generator()


def colored_cells(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    return by_color


def orientation(cells):
    (r0, c0), (r1, c1) = sorted(cells)
    assert r1 - r0 == 2
    assert abs(c1 - c0) == 2
    return "main" if c1 > c0 else "anti"


def assert_pair_grammar(grid, expected_pairs):
    cells = colored_cells(grid)
    assert len(cells) == expected_pairs
    assert Counter(value for row in grid for value in row if value) == Counter(
        {color: 2 for color in cells}
    )
    boxes = []
    for pair in cells.values():
        assert len(pair) == 2
        (r0, c0), (r1, c1) = sorted(pair)
        assert r1 - r0 == 2 and abs(c1 - c0) == 2
        left = min(c0, c1)
        box = {(r, c) for r in range(r0, r0 + 3) for c in range(left, left + 3)}
        assert all(not (box & prior) for prior in boxes)
        boxes.append(box)


def test_n_pairs_override_is_exact_at_declared_boundaries(g):
    for difficulty in (None, "easy", "medium", "hard"):
        one = g.generate(17, 9, difficulty=difficulty, n_pairs=1)
        eight = g.generate(17, 9, difficulty=difficulty, n_pairs=8)
        assert_pair_grammar(one, 1)
        assert_pair_grammar(eight, 8)
        assert one != eight
        assert g.self_check(one, difficulty=difficulty) == []
        assert g.self_check(eight, difficulty=difficulty) == []


def test_declared_grid_and_texture_overrides_are_observable(g):
    main = g.generate(
        5, 2, grid_h=12, grid_w=18, n_pairs=6, texture="main_only"
    )
    anti = g.generate(
        5, 2, grid_h=12, grid_w=18, n_pairs=6, texture="anti_only"
    )
    mixed = g.generate(
        5, 2, grid_h=12, grid_w=18, n_pairs=6, texture="mixed"
    )
    assert (len(main), len(main[0])) == (12, 18)
    assert (len(anti), len(anti[0])) == (12, 18)
    assert_pair_grammar(main, 6)
    assert_pair_grammar(anti, 6)
    assert_pair_grammar(mixed, 6)
    assert {orientation(pair) for pair in colored_cells(main).values()} == {"main"}
    assert {orientation(pair) for pair in colored_cells(anti).values()} == {"anti"}
    assert {orientation(pair) for pair in colored_cells(mixed).values()} == {"main", "anti"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"n_pairs": 0},
        {"n_pairs": 9},
        {"n_pairs": True},
        {"n_pairs": 1.5},
        {"n_pairs": "2"},
        {"grid_h": True},
        {"grid_w": 4},
        {"texture": "unknown"},
        {"pairs": 2},
        {"palette_size": 3},
    ],
)
def test_invalid_or_undocumented_overrides_are_rejected(g, overrides):
    with pytest.raises((TypeError, ValueError)):
        g.generate(1, 0, **overrides)


def test_impossible_exact_canvas_count_combination_is_rejected(g):
    with pytest.raises(ValueError, match="supports at most"):
        g.generate(1, 0, grid_h=5, grid_w=5, n_pairs=8)


def test_single_pair_rejects_unobservable_mixed_texture(g):
    with pytest.raises(ValueError, match="mixed texture requires at least two pairs"):
        g.generate(1, 0, n_pairs=1, texture="mixed")


def test_self_check_enforces_full_pair_geometry_and_nonoverlap(g):
    valid = [[0] * 8 for _ in range(8)]
    valid[0][0] = valid[2][2] = 4
    valid[3][4] = valid[5][6] = 7
    assert g.self_check(valid) == []

    blank = [[0] * 8 for _ in range(8)]
    single = [row[:] for row in blank]
    single[2][2] = 4
    axis_aligned = [row[:] for row in blank]
    axis_aligned[2][1] = axis_aligned[2][3] = 4
    wrong_span = [row[:] for row in blank]
    wrong_span[1][1] = wrong_span[4][4] = 4
    overlapping = [row[:] for row in blank]
    overlapping[0][0] = overlapping[2][2] = 4
    overlapping[1][1] = overlapping[3][3] = 7

    for bad in (blank, single, axis_aligned, wrong_span, overlapping):
        assert g.self_check(bad)


def test_default_generation_is_total_and_geometry_valid(g):
    observed = set()
    for difficulty in (None, "easy", "medium", "hard"):
        for seed in range(8):
            grid = g.generate(seed, seed + 3, difficulty=difficulty)
            assert g.self_check(grid, difficulty=difficulty) == []
            pairs = len(colored_cells(grid))
            assert 1 <= pairs <= 8
            assert_pair_grammar(grid, pairs)
            observed.update(orientation(pair) for pair in colored_cells(grid).values())
    assert observed == {"main", "anti"}
