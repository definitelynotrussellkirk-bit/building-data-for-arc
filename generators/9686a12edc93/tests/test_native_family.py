"""Literal crossing, rejection-chain and protected-rule checks."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / 'workspace/parametric'
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('clearance_native_tests', HOME/'native_family.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def crossing(vertical=7, horizontal=2):
    return [[0,vertical,0],[horizontal,0,horizontal],[0,vertical,0]]


def chain():
    grid = [[0]*10 for _ in range(9)]
    for color, cells in {1:[(3,1),(3,7)],2:[(1,4),(7,4)],3:[(6,2),(6,8)]}.items():
        for r,c in cells: grid[r][c] = color
    return grid


def blocked():
    grid = [[0]*7 for _ in range(7)]
    for r,c in [(3,0),(3,6)]: grid[r][c] = 2
    grid[3][2] = 9  # Singleton remains an occupancy blocker but is erased from output.
    grid[5][1] = grid[5][2] = 6  # Adjacent endpoints have an empty interior.
    grid[0][0] = grid[1][1] = 4  # Unaligned pair.
    grid[0][6] = grid[1][6] = grid[2][6] = 8  # Non-pair.
    return grid


def test_exact_default_and_numeric_overwrite_order():
    setting={'clearance_stage':'input'}
    assert f.program(setting).encode() == (HOME/'canonical.rkt').read_bytes()
    assert f.apply(crossing(),setting) == [[0,7,0],[2,7,2],[0,7,0]]


def test_newly_painted_cells_block_only_later_paths():
    assert f.apply(crossing(),{'clearance_stage':'painted'}) == [[0,0,0],[2,2,2],[0,0,0]]
    assert f.apply(crossing(2,7),{'clearance_stage':'painted'}) == [[0,2,0],[0,2,0],[0,2,0]]


def test_rejected_middle_path_never_blocks_third_path():
    grid=chain(); out=[[0]*10 for _ in range(9)]
    for c in range(1,8): out[3][c]=1
    for c in range(2,9): out[6][c]=3
    assert f.apply(grid,{'clearance_stage':'painted'}) == out
    trace=f.trace(grid,{'clearance_stage':'painted'})
    assert [(step['color'],step['accepted']) for step in trace['steps']] == [(1,True),(2,False),(3,True)]
    assert trace['steps'][1]['blockers'] == [[3,4]]
    assert trace['steps'][2]['blockers'] == []


@pytest.mark.parametrize('mode',['input','painted'])
def test_invalid_colors_stay_as_blockers_but_are_not_copied(mode):
    out=[[0]*7 for _ in range(7)];out[5][1]=out[5][2]=6
    assert f.apply(blocked(),{'clearance_stage':mode}) == out


def test_input_and_result_are_independent():
    grid=chain();before=[row[:] for row in grid]
    out=f.apply(grid,{'clearance_stage':'painted'});out[0][0]=9
    assert grid==before
    assert f.apply(grid,{'clearance_stage':'painted'})[0][0]==0


@pytest.mark.parametrize('shape',[(3,3),(3,30),(30,3),(30,30)])
@pytest.mark.parametrize('mode',['input','painted'])
def test_empty_and_all_invalid_inputs_are_total(shape,mode):
    h,w=shape;grid=[[0]*w for _ in range(h)]
    assert f.apply(grid,{'clearance_stage':mode})==grid
    grid[0][0]=1
    assert f.apply(grid,{'clearance_stage':mode})==[[0]*w for _ in range(h)]


@pytest.mark.parametrize('settings',[None,{},[],{'clearance_stage':'bad'},
    {'clearance_stage':True},{'clearance_stage':'input','extra':1}])
def test_settings_fail_closed(settings):
    with pytest.raises(ValueError):f.parse_settings(settings)


@pytest.mark.parametrize('grid',[[],[[0]],[[0]*3]*2,[[0]*31]*3,[[0]*3]*31,
    [[0,0,0],[0,0],[0,0,0]],((0,0,0),)*3,[[False,0,0],[0,0,0],[0,0,0]],
    [[10,0,0],[0,0,0],[0,0,0]],[[1.0,0,0],[0,0,0],[0,0,0]]])
def test_grid_grammar_is_strict(grid):
    with pytest.raises(ValueError):f.validate_grid(grid)


@pytest.fixture(scope='module')
def protected():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    yield apply
    bridge.close()


@pytest.mark.parametrize('mode',['input','painted'])
@pytest.mark.parametrize('grid',[crossing(),crossing(2,7),chain(),blocked(),[[0]*3 for _ in range(3)]])
def test_literal_cases_match_protected_racket(protected,mode,grid):
    setting={'clearance_stage':mode}
    assert protected(f.program(setting),grid)==f.apply(grid,setting)


def test_wrong_intermediates_change_protected_labels(protected):
    setting={'clearance_stage':'painted'}
    intended=f.apply(chain(),setting)
    assert protected(f.variant_program(setting,update_rejected=True),chain())!=intended
    assert protected(f.variant_program(setting,clearance='input'),chain())!=intended
    fixed={'clearance_stage':'input'}
    assert protected(f.variant_program(fixed,clearance='ignore'),blocked())!=f.apply(blocked(),fixed)


def test_reading_and_numeric_order_disagree_on_explicit_crossing(protected):
    for mode in f.MODES:
        setting={'clearance_stage':mode}
        assert protected(f.variant_program(setting,order='reading'),crossing())!=f.apply(crossing(),setting)


def test_older_accepted_path_remains_in_clearance_memory(protected):
    grid=chain();grid[1][2]=grid[4][2]=4
    setting={'clearance_stage':'painted'}
    trace=f.trace(grid,setting)
    assert [(step['color'],step['accepted']) for step in trace['steps']]==[(1,True),(2,False),(3,True),(4,False)]
    assert trace['steps'][-1]['blockers']==[[3,2]]
    prediction=protected(f.variant_program(setting,memory='last'),grid)
    assert prediction!=trace['output']
    assert prediction[2][2]==4 and trace['output'][2][2]==0


def test_private_memory_control_is_strict():
    with pytest.raises(ValueError):f.variant_program({'clearance_stage':'painted'},memory=True)


@pytest.mark.parametrize('kwargs',[{'order':'unknown'},{'clearance':'unknown'},
    {'update_rejected':1},{'keep_input':1},{'endpoints':1},{'paint_color':False},
    {'eligibility':'unknown'},{'minimum_span':True}])
def test_private_rival_controls_are_strict(kwargs):
    with pytest.raises(ValueError):f.variant_program({'clearance_stage':'input'},**kwargs)
