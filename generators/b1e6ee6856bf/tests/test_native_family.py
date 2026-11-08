"""Native skyline semantics, exact canonical source, and strict grammar."""
import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'


@pytest.fixture(scope='module')
def family():
    path = HERE / 'native_family.py'
    assert path.is_file(), 'native family has not been implemented'
    spec = importlib.util.spec_from_file_location('skyline_family_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_skyline_mode_consumes_survivors_not_raw_counts(family):
    grid = [[1, 0, 1, 2], [2, 1, 2, 0], [2, 2, 2, 2]]
    assert family.apply(grid, 'all') == [[1, 0, 1, 2], [0, 1, 0, 0], [0, 0, 0, 0]]
    assert family.apply(grid, 'modal_color') == [[1, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 0]]
    trace = family.trace(grid, 'modal_color')
    assert trace['histogram'] == {1: 3, 2: 1}
    assert trace['selected_colors'] == [1]


def test_tied_modes_all_survive_in_place(family):
    grid = [[1, 0, 2, 0, 3], [4, 1, 4, 2, 4], [5, 5, 5, 5, 5]]
    assert family.apply(grid, 'modal_color') == [[1, 0, 2, 0, 0], [0, 1, 0, 2, 0], [0, 0, 0, 0, 0]]


def test_plurality_below_half_and_repeated_minority(family):
    grid = [[1, 1, 1, 2, 2, 3, 3, 4], [9] * 8]
    assert family.apply(grid, 'modal_color') == [[1, 1, 1, 0, 0, 0, 0, 0], [0] * 8]


@pytest.mark.parametrize('grid', [[[0]], [[7]], [[0, 0, 0]], [[1], [0], [2]], [[0] * 30 for _ in range(30)]])
@pytest.mark.parametrize('mode', ['all', 'modal_color'])
def test_degenerate_but_lawful_and_fresh_output(family, grid, mode):
    before = [row[:] for row in grid]
    out = family.apply(grid, mode)
    assert len(out) == len(grid) and len(out[0]) == len(grid[0])
    assert grid == before and out is not grid
    assert all(a is not b for a, b in zip(out, grid))


@pytest.mark.parametrize('grid', [[], [[]], [[1], [1, 2]], ((1,),), [[True]], [[1.0]], [[-1]], [[10]], [[1] * 31], [[1]] * 31, [None]])
def test_invalid_grids_rejected(family, grid):
    with pytest.raises((TypeError, ValueError)):
        family.apply(grid, 'all')


@pytest.mark.parametrize('settings', [None, {}, {'survivor_filter': 'other'}, {'survivor_filter': True}, {'survivor_filter': 'all', 'extra': 1}, [('survivor_filter', 'all')]])
def test_settings_exact_and_closed(family, settings):
    with pytest.raises((TypeError, ValueError)):
        family.program(settings)


def test_canonical_program_exact(family):
    from arcpuzzles import Catalog
    programs = {v['program_solution'] for v in Catalog('.').get('b1e6ee6856bf')['variants']}
    assert programs == {family.program({'survivor_filter': 'all'})}
    assert (HERE / 'canonical.rkt').read_text() == next(iter(programs))


def test_variants_and_rivals_are_complete_rules(family):
    from puzzle_generators.rule_wrap import wrap_rule
    for mode in family.MODES:
        settings = {'survivor_filter': mode}
        assert family.parse_settings(settings) == mode
        for program in [family.program(settings), *family.rivals(settings).values()]:
            assert program.startswith('(rule!')
            wrap_rule(program)


def test_many_colors_and_dense_thirty(family):
    grid = [[(r * 3 + c) % 9 + 1 for c in range(30)] for r in range(30)]
    out = family.apply(grid, 'all')
    assert out[0] == grid[0] and all(row == [0] * 30 for row in out[1:])
    modal = family.apply(grid, 'modal_color')
    assert modal[0] == [value if value in (1, 2, 3) else 0 for value in grid[0]]
