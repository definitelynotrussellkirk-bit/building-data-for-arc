"""Observable exact controls and positive-domain regressions."""
from copy import deepcopy
from itertools import product
import random
import types

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
SOURCE = next(path for path in (
    ROOT / 'generators/49898d244b5f/generator.py',
    ROOT / 'puzzle_generators/per_puzzle/49898d244b5f/generator.py',
) if path.is_file())
GEN = types.ModuleType('generator_contract_subject')
GEN.__file__ = str(SOURCE)
exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), GEN.__dict__)


def counts(grid):
    singles = sum(sum(row[c] != 0 for row in grid) == 1 for c in range(len(grid[0])))
    palette = len({value for row in grid for value in row if value != 0})
    return singles, palette


@pytest.mark.parametrize('band,axis,value', list(product(('easy', 'medium', 'hard'), ('grid_h', 'grid_w'), (3, 18))))
def test_dimension_extremes_are_exact_in_every_band(band, axis, value):
    grid = GEN.generate(0, 0, difficulty=band, **{axis: value})
    assert (len(grid) if axis == 'grid_h' else len(grid[0])) == value
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize('band', ('easy', 'medium', 'hard'))
def test_maximum_columns_standalone_is_supported(band):
    grid = GEN.generate(0, 1, difficulty=band, columns=12)
    assert counts(grid)[0] == 12


@pytest.mark.parametrize('axis,value', list(product(('palette_size', 'n_distinct_colors'), (1, 9))))
def test_exact_distinct_color_aliases(axis, value):
    for band in ('easy', 'medium', 'hard'):
        grid = GEN.generate(0, 1, difficulty=band, **{axis: value})
        assert counts(grid)[1] == value


def test_consistent_aliases_and_full_capacity_corner():
    grid = GEN.generate(5, 1, grid_h=3, grid_w=3, columns=1,
                        palette_size=7, n_distinct_colors=7,
                        palette_kind='warm', texture='warm')
    assert (len(grid), len(grid[0]), counts(grid)) == (3, 3, (1, 7))
    assert GEN.self_check(grid) == []
    grid = GEN.generate(5, 1, grid_h=3, grid_w=3, columns=3, palette_size=3)
    assert counts(grid) == (3, 3)


@pytest.mark.parametrize('overrides,expected_axes', [
    ({'palette_size': 1, 'n_distinct_colors': 2}, {'palette_size', 'n_distinct_colors'}),
    ({'palette_kind': 'warm', 'texture': 'cool'}, {'palette_kind', 'texture'}),
    ({'grid_w': 3, 'columns': 4}, {'grid_w', 'columns'}),
    ({'grid_h': 3, 'grid_w': 3, 'palette_size': 9}, {'grid_h', 'grid_w', 'palette_size'}),
    ({'grid_w': 3, 'columns': 3, 'palette_size': 4}, {'grid_w', 'columns', 'palette_size'}),
])
def test_impossible_joint_controls_fail_with_explicit_axis_evidence(overrides, expected_axes):
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, **overrides)
    assert set(getattr(caught.value, 'incompatible_axes', ())) == expected_axes


@pytest.mark.parametrize('overrides', [
    {'unknown_axis': 1}, {'density': 'dense'}, {'position_bias': 'left'},
    {'palette_kind': 'missing'}, {'texture': 'missing'}, {'palette_size': 0},
    {'grid_h': True}, {'grid_w': 3.0}, {'columns': '3'},
    {'palette_size': False}, {'n_distinct_colors': 2.5},
])
def test_invalid_controls_are_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize('grid', [
    None, [], [[]], [[1]], [[1, 0, 0], [0, 0]],
    [[10, 0, 0], [0, 0, 0], [0, 0, 0]],
    [[-1, 0, 0], [0, 0, 0], [0, 0, 0]],
    [[1.5, 0, 0], [0, 0, 0], [0, 0, 0]],
    [[True, 0, 0], [0, 0, 0], [0, 0, 0]],
    [[0] * 19 for _ in range(3)],
])
def test_validator_rejects_malformed_or_non_arc_inputs_without_raising(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_palette_modes_change_real_draws_and_alias_agrees():
    for count in (1, 9):
        results = []
        for kind in GEN.PALETTE_KINDS:
            grid = GEN.generate(19, 1, palette_size=count, palette_kind=kind)
            assert grid == GEN.generate(19, 1, palette_size=count, texture=kind)
            results.append(grid)
        assert len({repr(grid) for grid in results}) > 1


@pytest.mark.parametrize('name', ('no_seeds', 'all_columns_have_multiple', 'columns_already_full'))
def test_explicit_negative_fixtures_are_outside_positive_domain(name):
    grid = GEN.generate(1, 0, texture=name, grid_h=3, grid_w=4)
    assert (len(grid), len(grid[0])) == (3, 4)
    assert GEN.self_check(grid)
    assert GEN.expected_output(grid) == [[0] * 4 for _ in range(3)]


def test_replay_is_deterministic_isolated_and_returns_fresh_rows():
    before = random.getstate()
    first = GEN.generate(19, 2, difficulty='hard')
    snapshot = deepcopy(first)
    assert len({id(row) for row in first}) == len(first)
    GEN.generate(713, 999, difficulty='easy', palette_kind='cool')
    assert GEN.generate(19, 2, difficulty='hard') == snapshot
    first[0][0] = 999
    assert GEN.generate(19, 2, difficulty='hard') == snapshot
    assert random.getstate() == before


def test_each_four_pair_window_has_teaching_support_for_every_query_position():
    rivals = getattr(GEN, 'LESSON_COMPETITORS', None)
    assert isinstance(rivals, dict) and rivals
    for band, seed, start in product(('easy', 'medium', 'hard'), (0, 419), range(4)):
        pairs = [{'input': GEN.generate(seed, start + i, difficulty=band)} for i in range(4)]
        for pair in pairs:
            pair['output'] = GEN.expected_output(pair['input'])
        for query_index in range(4):
            query = pairs[query_index]
            demos = pairs[:query_index] + pairs[query_index + 1:]
            assert GEN.lesson_identifiable(demos, query) == [], (band, seed, start, query_index)
            for name, rival in rivals.items():
                fits = all(rival(p['input']) == p['output'] for p in demos)
                assert not (fits and rival(query['input']) != query['output']), name


def test_canonical_profiles_occur_in_every_default_band_window():
    for band, seed in product(('easy', 'medium', 'hard'), (0, 419)):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(20)]
        profiles = {(len(g), len(g[0]), len({v for row in g for v in row})) for g in grids}
        assert profiles & {(7, 7, 3), (8, 8, 3)}
        assert all(GEN.self_check(grid) == [] for grid in grids)


def test_two_default_profile_examples_per_four_draws_keep_teaching_witnesses():
    for band, seed, start in product(('easy', 'medium', 'hard'), (0, 419), range(4)):
        grids = [GEN.generate(seed, start + index, difficulty=band) for index in range(4)]
        profiles = [(len(g), len(g[0]), len({v for row in g for v in row})) for g in grids]
        assert sum(profile in {(7, 7, 3), (8, 8, 3)} for profile in profiles) >= 2
        # Increasing familiar shapes must not remove the three distinguishing
        # monochromatic rejected-column scenes from the same four-draw window.
        def has_distinguishing_column(grid):
            for column in range(len(grid[0])):
                values = [row[column] for row in grid if row[column] != 0]
                if len(values) >= 2 and len(set(values)) == 1:
                    return True
            return False
        assert sum(map(has_distinguishing_column, grids)) >= 3
