"""Regressions for exact arithmetic-line sampling and teachable windows."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '2d2b102b7740'
ROOT = find_root(__file__)
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
if not SOURCE.exists():
    SOURCE = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
SPEC = importlib.util.spec_from_file_location('reviewed_line_generator', SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def blue_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('count', [2, 3, 4, 5])
def test_count_override_is_realized_in_every_band(band, count):
    grid = gen.generate(0, 0, difficulty=band, n_blues=count)
    assert len(blue_cells(grid)) == count
    assert gen.self_check(grid) == []


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_canonical_size_and_step_four_are_constructible(band):
    grid = gen.generate(0, 0, difficulty=band, grid_h=15, grid_w=15,
                        n_blues=3, step_dr=4, step_dc=4, anchor_corner=True)
    assert (len(grid), len(grid[0])) == (15, 15)
    assert blue_cells(grid) == [(0, 0), (4, 4), (8, 8)]


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('height,width', [(6, 8), (18, 20)])
def test_dimension_boundaries_do_not_change_with_difficulty(band, height, width):
    grid = gen.generate(7, 2, difficulty=band, grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


def test_impossible_step_is_rejected_instead_of_replaced():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty='easy', grid_h=6, grid_w=8,
                     n_blues=3, step_dr=3, step_dc=1)


@pytest.mark.parametrize('column_step', [0, -1, -4])
def test_nonpositive_horizontal_step_is_not_a_row_major_step(column_step):
    with pytest.raises(ValueError):
        gen.generate(0, 0, step_dr=0, step_dc=column_step, anchor_corner=True)


@pytest.mark.parametrize('overrides', [
    {'n_blues': True}, {'n_blues': 2.5}, {'step_dc': '2'},
    {'grid_h': 12.1}, {'anchor_corner': 'false'}, {'n_bluess': 3},
    {'texture': 'same_position'}, {'line_orientation': 'unknown'},
])
def test_bad_override_values_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize('bad', [[], [[]], [[0], [0, 1]], [[False] * 8 for _ in range(6)]])
def test_self_check_returns_reasons_for_malformed_grids(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_foreign_colors():
    grid = [[0] * 10 for _ in range(8)]
    grid[1][1] = grid[3][2] = 1
    grid[0][8] = 9
    assert gen.self_check(grid)


def test_lawful_horizontal_line_is_not_rejected_as_a_generic_impostor():
    grid = [[0] * 10 for _ in range(8)]
    grid[4][:4] = [1, 1, 1, 1]
    assert gen.self_check(grid) == []


def test_every_canonical_pair_remains_in_domain():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair['input']) == []
        assert gen.strict_canonical_like(pair['input']) == []


def test_exact_controls_can_be_read_back_from_the_actual_grid():
    grid = gen.generate(0, 0, grid_h=13, grid_w=15, n_blues=4,
                        step_dr=2, step_dc=-2, anchor_corner=True)
    observed = gen.observe_overrides(grid)
    assert {key: observed[key] for key in ('n_blues', 'step_dr', 'step_dc', 'anchor_corner')} == {
        'n_blues': 4, 'step_dr': 2, 'step_dc': -2, 'anchor_corner': True,
    }
    assert blue_cells(grid) == [(0, 14), (2, 12), (4, 10), (6, 8)]


def test_conflicting_aliases_are_not_silently_overridden():
    with pytest.raises(ValueError):
        gen.generate(0, 0, texture='horizontal', line_orientation='vertical')


@pytest.mark.parametrize('bias', ['spread', 'corner', 'center'])
def test_position_bias_cannot_silently_override_an_exact_corner(bias):
    with pytest.raises(ValueError):
        gen.generate(0, 0, anchor_corner=True, position_bias=bias)


def test_every_cyclic_window_retains_opposite_signs_at_a_shared_count():
    # A count-to-sign shortcut must be contradicted after every possible holdout.
    for band in ('easy', 'medium', 'hard'):
        for seed in (0, 17):
            for start in range(6):
                grids = [gen.generate(seed, start+i, difficulty=band) for i in range(6)]
                keys = [tuple(tuple(row) for row in grid) for grid in grids]
                assert len(set(keys)) == 6
                observations = [gen.observe_overrides(grid) for grid in grids]
                for query in range(6):
                    demos = [obs for i, obs in enumerate(observations) if i != query]
                    assert any({obs['step_dc'] > 0 for obs in demos if obs['n_blues'] == n} == {False, True}
                               for n in range(2, 6))
                for grid in grids:
                    assert gen.self_check(grid) == []


@pytest.mark.parametrize('bad_seed', [True, False, 1.0, 1.75, '1', -1])
def test_seed_must_be_a_nonnegative_literal_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize('bad_sample_index', [True, False, 1.0, 1.75, '1', -1])
def test_sample_index_must_be_a_nonnegative_literal_integer(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, bad_sample_index)
