"""Literal geometry and protected execution tests for the separate native family."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / 'workspace/parametric'
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('orbit_native_family_test', HOME / 'native_family.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

SHAPE = {(0, 0), (0, 1), (0, 2), (1, 0)}
SOURCES = {'above': (2, 7), 'right': (6, 10), 'below': (9, 7), 'left': (6, 3)}


def grid_for(side='right'):
    grid = [[0] * 16 for _ in range(14)]
    grid[7][8] = 9
    r0, c0 = SOURCES[side]
    for r, c in SHAPE:
        grid[r0+r][c0+c] = 2
    return grid


def expected(cells):
    grid = [[0] * 16 for _ in range(14)]
    grid[7][8] = 9
    for r, c in cells:
        grid[r][c] = 2
    return grid


FIXED = {(4,4),(4,5),(4,6),(5,4), (4,9),(4,10),(5,10),(6,10),
         (8,6),(9,4),(9,5),(9,6), (8,9),(9,9),(10,9),(10,10)}
FACING = {(3,5),(3,6),(4,6),(5,6), (3,11),(4,9),(4,10),(4,11),
          (8,5),(9,5),(10,5),(10,6), (8,9),(8,10),(8,11),(9,9)}


@pytest.mark.parametrize('side,turns', [('above',0),('right',1),('below',2),('left',3)])
def test_absolute_side_survives_cropping(side, turns):
    info = f.validate_grid(grid_for(side))
    assert info['side'] == side and info['local'] == SHAPE
    state = f.intermediate(grid_for(side), {'orientation_frame':'source_side'})
    assert state['turns'] == turns and state['anchor'] == (7,8)
    assert state['shape'] == ((2,3) if turns % 2 == 0 else (3,2))


def test_literal_fixed_offsets_use_original_dimensions():
    assert f.apply(grid_for(), {'orientation_frame':'fixed'}) == expected(FIXED)


def test_literal_side_frame_recomputes_dimensions_after_orientation():
    assert f.apply(grid_for(), {'orientation_frame':'source_side'}) == expected(FACING)


def test_input_is_not_mutated_and_source_is_erased():
    grid = grid_for('above'); before = [row[:] for row in grid]
    result = f.apply(grid, {'orientation_frame':'fixed'})
    assert grid == before and result[2][7] == 0 and result[7][8] == 9


def test_exact_canonical_default():
    assert f.program({'orientation_frame':'fixed'}).encode() == (HOME/'canonical.rkt').read_bytes()
    assert f.program({'orientation_frame':'source_side'}) != f.program({'orientation_frame':'fixed'})


@pytest.mark.parametrize('settings', [None, {}, {'orientation_frame':'bad'},
    {'orientation_frame':True}, {'orientation_frame':'fixed','extra':0}, ['fixed']])
def test_settings_are_explicit_and_strict(settings):
    with pytest.raises(ValueError): f.parse_settings(settings)


@pytest.mark.parametrize('damage', ['bool','ragged','two_anchors','two_colors','disconnected','diagonal_side','no_margin'])
def test_rejects_invalid_native_inputs(damage):
    grid = grid_for()
    if damage == 'bool': grid[0][0] = True
    elif damage == 'ragged': grid[0].pop()
    elif damage == 'two_anchors': grid[0][0] = 9
    elif damage == 'two_colors': grid[6][10] = 3
    elif damage == 'disconnected': grid[1][1] = 2
    elif damage == 'diagonal_side':
        grid = [[0]*16 for _ in range(14)]; grid[7][8] = 9
        for r,c in SHAPE: grid[1+r][1+c] = 2
    elif damage == 'no_margin':
        grid[7][8] = 0; grid[7][13] = 9
    with pytest.raises(ValueError): f.validate_grid(grid)


def test_minimum_and_largest_template_geometry_are_admitted():
    small = [[0]*6 for _ in range(6)];small[3][3]=9
    for r,c in ((0,2),(1,2),(1,3)):small[r][c]=1
    assert f.validate_grid(small)['side']=='above'
    large = [[0]*30 for _ in range(30)];large[15][15]=9
    for r in range(14):
        for c in range(14):
            if r in (0,13) or c in (0,13) or (r<5 and c<7):large[r][c+2]=8
    assert f.validate_grid(large)['color']==8
    for mode in f.MODES:
        output=f.apply(large,{'orientation_frame':mode})
        assert len(output)==len(output[0])==30
        assert all(any(v for v in row) for row in (output[0],output[-1]))


@pytest.fixture(scope='module')
def protected():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    yield apply
    bridge.close()


@pytest.mark.parametrize('mode', ['fixed','source_side'])
@pytest.mark.parametrize('side', ['above','right','below','left'])
def test_literal_rectangles_match_protected_racket(protected, mode, side):
    setting={'orientation_frame':mode};grid=grid_for(side)
    assert protected(f.program(setting), grid) == f.apply(grid, setting)


@pytest.mark.parametrize('mode', ['fixed','source_side'])
def test_filled_bbox_is_an_executed_wrong_intermediate(protected, mode):
    setting={'orientation_frame':mode};grid=grid_for()
    prediction=protected(f.variant_program(setting,filled=True), grid)
    assert prediction != f.apply(grid,setting)


def test_side_rotation_and_fresh_dimensions_both_affect_output(protected):
    setting={'orientation_frame':'source_side'};grid=grid_for()
    output=f.apply(grid,setting)
    assert protected(f.variant_program(setting,forced_turns=0),grid) != output
    assert protected(f.variant_program(setting,stale_dimensions=True),grid) != output
