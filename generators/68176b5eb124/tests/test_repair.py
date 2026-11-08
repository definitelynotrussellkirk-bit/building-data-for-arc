"""Focused semantic regressions; imports the selected task without staging copies."""
import importlib.util
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('plus_generator', ROOT / 'generators/68176b5eb124/generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
ARMS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def centers(g):
    return [(r, c) for r in range(1, len(g)-1) for c in range(1, len(g[0])-1)
            if g[r][c] == 0 and g[r-1][c] != 0 and
            all(g[r+dr][c+dc] == g[r-1][c] for dr, dc in ARMS)]


@pytest.mark.parametrize('mask', range(1, 16))
def test_only_complete_four_arm_patterns_pass_ordinary_domain(mask):
    grid = [[0]*5 for _ in range(5)]
    for i, (dr, dc) in enumerate(ARMS):
        if mask & (1 << i):
            grid[2+dr][2+dc] = 4
    assert bool(gen.self_check(grid)) == (mask != 15)


def test_ordinary_generation_teaches_near_miss_with_positive():
    for seed in range(20):
        grid = gen.generate(seed, 0, grid_h=8, grid_w=8, n_pluses=1)
        assert len(centers(grid)) == 1
        # More than the four positive arms must provide a negative motif.
        assert sum(v != 0 for row in grid for v in row) > 4
        assert not gen.self_check(grid)


def test_exact_count_rejects_impossible_layout_instead_of_truncating():
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=5, grid_w=5, n_pluses=6)


@pytest.mark.parametrize('bad', [True, 7.5, '7', 4, 15])
def test_dimension_controls_are_strict_and_use_documented_range(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, grid_h=bad)


@pytest.mark.parametrize('texture', gen.DEGENERATE_TEXTURES)
def test_degenerate_metadata_does_not_admit_empty_grid(texture):
    assert gen.self_check([[0]*8 for _ in range(8)], meta={'texture': texture})


def test_mixed_colors_do_not_create_positive_center():
    grid = [[0]*5 for _ in range(5)]
    for color, (dr, dc) in zip((4, 4, 4, 5), ARMS):
        grid[2+dr][2+dc] = color
    assert gen.self_check(grid)


@pytest.mark.parametrize('texture', gen.DEGENERATE_TEXTURES)
def test_named_identity_modes_are_valid_and_honor_dimensions(texture):
    grid = gen.generate(8, 1, texture=texture, grid_h=5, grid_w=14)
    assert (len(grid), len(grid[0])) == (5, 14)
    assert not centers(grid)
    assert not gen.self_check(grid, meta={'texture': texture})


def test_unknown_override_is_not_silently_ignored():
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, n_pluse=2)


@pytest.mark.parametrize('grid', [None, 1, True, 'grid', [1], [True], ['12345'], [[]], [[0]*5, [0]*4]])
def test_malformed_grids_return_rejections_without_raising(grid):
    assert gen.self_check(grid)


def test_axis_metadata_and_realized_counts_match_shared_override_contract():
    sys.path.insert(0, str(ROOT / 'shared/tools'))
    import check_generator_override_contract as contract
    report = {axis.name: axis for axis in contract.axis_domain_report(gen.AXES)}
    assert report['n_pluses'].status == 'probeable'
    assert report['n_distinct_colors'].status == 'probeable'
    assert not any(axis.status in {'unparsable', 'never_probed', 'malformed'} for axis in report.values())
    assert report['position_bias'].status == 'singleton'
    assert report['position_bias'].values == ['grid_aligned']
    required = contract._required_observer_axes(gen.AXES)
    assert required == {'n_pluses', 'n_distinct_colors'}
    case = {'grid_h': 14, 'grid_w': 14, 'n_pluses': 6, 'n_distinct_colors': 2}
    grid = gen.generate(18, 0, **case)
    grid[13][13] = 9  # An unrelated color must not inflate target-arm colors.
    assert gen.observe_overrides(grid) == case
    assert contract._observed_override_errors(gen, grid, case, 'roundtrip', required) == []
    errors = contract._observed_override_errors(gen, grid, {'n_pluses': 5}, 'wrong count', required)
    assert errors and 'observed 6' in errors[0]
