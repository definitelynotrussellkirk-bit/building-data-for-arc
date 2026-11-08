"""Behavioral regressions for the sampler's public, pixel-observable contract."""
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "a950d6dbe2e0"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_symmetry_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def measured(grid):
    cells = [v for row in grid for v in row if v]
    return len(grid), len(grid[0]), len(cells), len(set(cells))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("h,w,n,k", [
    (4, 4, 2, 2), (6, 14, 12, 5), (8, 10, 20, 9),
    (30, 30, 64, 9), (4, 30, 30, 2), (30, 4, 30, 9),
])
def test_exact_joint_controls_are_realized_in_pixels(band, h, w, n, k):
    grid = gen.generate(712, 5, difficulty=band, grid_h=h, grid_w=w,
                        n_cells=n, n_distinct_colors=k)
    assert measured(grid) == (h, w, n, k)
    assert not gen.self_check(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("axes", [{"n_cells": 64}, {"n_distinct_colors": 9},
                                  {"grid_h": 4}, {"grid_w": 30}])
def test_single_controls_remain_feasible_in_every_band(band, axes):
    grid = gen.generate(37, 0, difficulty=band, **axes)
    h, w, n, k = measured(grid)
    observation = dict(grid_h=h, grid_w=w, n_cells=n, n_distinct_colors=k)
    assert all(observation[name] == value for name, value in axes.items())
    assert not gen.self_check(grid)


@pytest.mark.parametrize("axes", [
    {"misspelled_cells": 3}, {"grid_h": 7}, {"grid_w": 32},
    {"grid_h": True}, {"grid_w": 8.5}, {"n_cells": "5"},
    {"n_cells": 1}, {"n_distinct_colors": 1},
    {"n_cells": 4, "n_distinct_colors": 5},
    {"grid_h": 4, "grid_w": 4, "n_cells": 5},
    {"grid_h": 4, "grid_w": 4, "n_distinct_colors": 5},
])
def test_invalid_or_impossible_controls_fail_loudly(axes):
    with pytest.raises(ValueError):
        gen.generate(12, 0, **axes)


@pytest.mark.parametrize("grid", [
    [], [[]], [[0, 0], [0]], [[0] * 8 for _ in range(8)],
    [[False, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[10, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
    [[1, 2, 0, 0], [0, 0, 0, 0], [0, 0, 4, 0], [0, 0, 0, 0]],
    [[1, 1, 0, 0], [1, 1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
])
def test_validator_rejects_malformed_and_out_of_domain_inputs(grid):
    assert gen.self_check(grid)


def test_validator_accepts_all_canonical_inputs():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    assert all(not gen.self_check(pair["input"]) for pair in pairs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_contains_all_canonical_sizes_and_rectangles(band):
    shapes = {measured(gen.generate(seed, seed, difficulty=band))[:2]
              for seed in range(90)}
    assert {(8, 8), (10, 10), (12, 12)} <= shapes
    assert any(h < w for h, w in shapes)
    assert any(h > w for h, w in shapes)


def test_determinism_and_no_returned_grid_aliasing():
    first = gen.generate(876, 9, difficulty="hard")
    expected = [row[:] for row in first]
    first[0][0] = 99
    assert gen.generate(876, 9, difficulty="hard") == expected


def test_returned_grids_have_only_upper_left_seeds():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            grid = gen.generate(96, index, difficulty=band)
            h, w, n, k = measured(grid)
            assert 2 <= k <= min(n, 9)
            assert all(v == 0 for r, row in enumerate(grid) for c, v in enumerate(row)
                       if r >= h // 2 or c >= w // 2)


def reflected_by_concatenation(grid):
    """Independent geometric test oracle; production labels still use Racket."""
    upper = [row[:len(row) // 2] + row[:len(row) // 2][::-1]
             for row in grid[:len(grid) // 2]]
    return upper + [row[:] for row in upper[::-1]]


def test_declared_shortcuts_really_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_distinguishes_declared_rivals(band):
    # 12 seeds x all 3 residues x 4 rotations = 144 complete lessons per band.
    # This is a deterministic construction check; the separate production
    # lesson census supplies the Racket labels and accepted-pair provenance.
    for seed in range(12):
        for start in range(3):
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            pairs = [{"input": grid, "output": reflected_by_concatenation(grid)} for grid in grids]
            assert sum(len(g) != len(g[0]) for g in grids) >= 2
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(p["input"]) != p["output"] for p in demos), name


def test_observer_reports_all_exact_axes_from_pixels():
    for index in range(12):
        grid = gen.generate(312, index)
        values = measured(grid)
        expected = dict(zip(("grid_h", "grid_w", "n_cells", "n_distinct_colors"), values))
        assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize("axis", ["palette_kind", "palette_size", "texture", "density", "position_bias"])
def test_retired_inert_controls_are_not_silently_accepted(axis):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{axis: "legacy"})


def test_impossible_joint_control_names_the_incompatible_axes():
    with pytest.raises(ValueError) as caught:
        gen.generate(1, 2, grid_h=4, grid_w=4, n_cells=5)
    assert set(caught.value.incompatible_axes) == {"grid_h", "grid_w", "n_cells"}


def test_validator_remains_broader_than_the_default_teaching_schedule():
    grid = gen.generate(0, 1, grid_h=4, grid_w=4, n_cells=4, n_distinct_colors=2)
    assert gen.strict_canonical_like(grid) == []
