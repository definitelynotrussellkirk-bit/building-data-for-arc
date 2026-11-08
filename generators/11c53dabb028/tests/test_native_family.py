"""Native component isolation followed by retained negative tiling."""
import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'


def load(name):
    path = HERE / (name + '.py')
    assert path.is_file(), 'native family has not been implemented'
    spec = importlib.util.spec_from_file_location('component_tile_test_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def settings(frame='largest_component', v=2, h=2):
    return {'input_frame': frame, 'vertical_repeats': v, 'horizontal_repeats': h}


def test_retained_tile_kernel_accepts_solid_derived_component():
    proto = load('prototype')
    assert hasattr(proto, 'tile_output'), 'shared tile kernel has not been exposed'
    assert proto.tile_output([[2, 3]], vertical_repeats=2, horizontal_repeats=1) == [[0, 0], [0, 0]]
    with pytest.raises(ValueError):
        proto.solve([[2, 3]])


def test_isolate_before_invert_removes_enclosed_foreign_component():
    family = load('native_family')
    grid = [[1, 2, 2, 2, 2], [2, 0, 0, 0, 2], [2, 0, 7, 0, 2], [2, 0, 0, 0, 2], [2, 2, 2, 2, 2]]
    state = family.intermediate(grid, 'largest_component')
    assert state['grid'][2][2] == 0 and state['component_size'] == 16
    assert state['bbox'] == [0, 0, 4, 4]
    alt = family.apply(grid, settings(v=1, h=1))
    raw = family.apply(grid, settings('input', 1, 1))
    assert alt[2][2] == 1 and raw[2][2] == 0
    assert len(alt) == len(raw) == 5


def test_ties_choose_first_actual_row_major_cell_not_leftmost_bbox():
    family = load('native_family')
    grid = [[0, 0, 0, 3, 4], [0, 0, 0, 4, 0], [2, 2, 0, 0, 0], [2, 0, 0, 0, 0]]
    state = family.intermediate(grid, 'largest_component')
    assert state['bbox'] == [0, 3, 1, 4]
    assert state['grid'] == [[3, 4], [4, 0]]
    assert family.apply(grid, settings(v=1, h=1)) == [[0, 0], [0, 3]]


def test_components_ignore_color_but_use_four_neighbors():
    family = load('native_family')
    grid = [[1, 2, 0], [0, 0, 3], [4, 4, 3]]
    assert [len(c) for c in family.components(grid)] == [2, 4]
    assert len(family.components(grid, connectivity=8)) == 1
    assert max(map(len, family.components(grid, monochrome=True))) == 2


def test_first_color_is_taken_from_selected_crop():
    family = load('native_family')
    grid = [[8, 0, 0, 0, 0], [0, 0, 0, 4, 0], [0, 0, 2, 4, 0], [0, 0, 2, 0, 0]]
    trace = family.trace(grid, settings(v=1, h=1))
    assert trace['selected_color'] == 4
    assert trace['frame']['bbox'] == [1, 2, 3, 3]
    assert trace['output'] == [[4, 0], [0, 0], [0, 4]]


@pytest.mark.parametrize('v,h', [(1, 1), (1, 2), (2, 1), (2, 2)])
def test_retained_programs_and_canonical_exact(v, h):
    family = load('native_family')
    proto = load('prototype')
    assert family.program(settings('input', v, h)) == proto.program_for(v, h)
    grid = [[0, 3, 0], [4, 4, 0]]
    assert family.apply(grid, settings('input', v, h)) == proto.solve(grid, vertical_repeats=v, horizontal_repeats=h)
    if (v, h) == (2, 2):
        from arcpuzzles import Catalog
        assert {x['program_solution'] for x in Catalog('.').get('11c53dabb028')['variants']} == {family.program(settings('input'))}


@pytest.mark.parametrize('grid', [[], [[]], [[0]], [[1]], [[1, 2]], [[0, 0]], [[1], [0, 2]], [[True, 0]], [[1.0, 0]], [[10, 0]], [[-1, 0]], [[1] + [0] * 15], [[1, 0]] * 16, ((1, 0),)])
def test_raw_grammar_is_strict(grid):
    with pytest.raises((ValueError, TypeError)):
        load('native_family').apply(grid, settings())


@pytest.mark.parametrize('bad', [None, {}, {'input_frame': 'input'}, settings(v=True), settings(h=3), settings(frame='other'), {**settings(), 'extra': 1}])
def test_settings_are_closed_and_exact(bad):
    with pytest.raises((ValueError, TypeError)):
        load('native_family').program(bad)


@pytest.mark.parametrize('frame', ['input', 'largest_component'])
def test_tiny_solid_intermediate_and_freshness(frame):
    family = load('native_family')
    grid = [[5, 0]]
    actual = family.apply(grid, settings(frame))
    expected = [[0, 5, 0, 5], [0, 5, 0, 5]] if frame == 'input' else [[0, 0], [0, 0]]
    assert actual == expected and grid == [[5, 0]]


def test_full_size_outputs_and_complete_rules():
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.parser import parse
    family = load('native_family')
    grid = [[1] * 15 for _ in range(15)]
    grid[7][7] = 0
    for frame in family.FRAMES:
        assert len(family.apply(grid, settings(frame))) == 30
        assert len(family.apply(grid, settings(frame))[0]) == 30
        for rule in [family.program(settings(frame)), *family.rivals(settings(frame)).values()]:
            assert rule.startswith('(rule!')
            parse(rule)
            wrap_rule(rule)
