"""Literal semantic and boundary tests for local transpose then selection."""
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


def family():
    path = HOME / 'workspace/parametric/native_family.py'
    assert path.is_file(), 'native transpose/select family has not been implemented'
    spec = importlib.util.spec_from_file_location('transpose_family_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def scene():
    grid = [[0] * 8 for _ in range(8)]
    for r, c in ((0,0),(1,0),(2,0),(2,1),(0,3),(1,3),(2,3),(2,4)):
        grid[r][c] = 2
    for r, c in ((4,0),(5,0),(6,0),(6,1),(6,2)):
        grid[r][c] = 3
    return grid


def wanted(selection):
    grid = [[0] * 8 for _ in range(8)]
    if selection != 'smallest':
        for r,c in [(0,c) for c in range(6)] + [(1,2),(1,5)]: grid[r][c] = 2
    if selection != 'largest':
        for r,c in ((4,0),(4,1),(4,2),(5,2),(6,2)): grid[r][c] = 3
    return grid


@pytest.mark.parametrize('selection', ['all','largest','smallest'])
def test_transpose_merges_change_rank_with_literal_answers(selection):
    f=family(); grid=scene()
    assert f.apply(grid, {'selection':selection}) == wanted(selection)
    assert grid == scene()


def test_input_components_remain_separate_but_output_merges():
    f=family()
    assert sorted(len(o['cells']) for o in f.components(scene())) == [4,4,5]
    assert sorted(len(o['cells']) for o in f.components(f.transformed(scene()))) == [5,8]


def test_all_tied_components_are_preserved_with_original_colors():
    f=family(); grid=[[0]*8 for _ in range(8)]
    for r,c,color in ((0,0,2),(1,0,2),(4,4,7),(5,4,7),(0,6,9)):
        grid[r][c]=color
    largest=f.apply(grid,{'selection':'largest'})
    assert {(r,c,v) for r,row in enumerate(largest) for c,v in enumerate(row) if v} == {
        (0,0,2),(0,1,2),(4,4,7),(4,5,7)}
    smallest=f.apply(grid,{'selection':'smallest'})
    assert {(r,c,v) for r,row in enumerate(smallest) for c,v in enumerate(row) if v} == {(0,6,9)}


def test_default_program_is_exact_selected_canonical():
    from arcpuzzles import Catalog
    f=family(); row=Catalog(HOME.parents[1]).get('7071285d78ce')
    assert {v['program_solution'] for v in row['variants']} == {f.program({'selection':'all'})}


@pytest.mark.parametrize('settings',[None,{},[],{'selection':True},{'selection':0},
    {'selection':'LARGEST'},{'selection':'all','extra':0}])
def test_settings_reject_undeclared_values_and_types(settings):
    with pytest.raises(ValueError): family().program(settings)


@pytest.mark.parametrize('mutation',['bool','float','ragged','too_small','too_large',
    'one_component','touching_colors','clipped','destination_overlap'])
def test_invalid_domain_is_rejected_before_label_claim(mutation):
    grid=scene()
    if mutation=='bool':grid[0][0]=True
    elif mutation=='float':grid[0][0]=2.0
    elif mutation=='ragged':grid[0].pop()
    elif mutation=='too_small':grid=grid[:7]
    elif mutation=='too_large':grid=[[0]*31 for _ in range(31)]
    elif mutation=='one_component':grid=[[0]*8 for _ in range(8)];grid[0][0]=2
    elif mutation=='touching_colors':grid[0][1]=4
    elif mutation=='clipped':
        grid=[[0]*8 for _ in range(8)];grid[0][0]=1
        grid[6][5]=2;grid[6][6]=2;grid[6][7]=2
    elif mutation=='destination_overlap':
        grid=[[0]*8 for _ in range(8)]
        grid[0][0]=2;grid[0][1]=2;grid[0][2]=2
        grid[2][0]=3
    with pytest.raises(ValueError):family().apply(grid,{'selection':'all'})


@pytest.mark.parametrize('selection',['all','largest','smallest'])
def test_protected_racket_matches_literal_rank_reversal(selection):
    from arcpuzzles.parametric_worker import _real_evaluator
    f=family();execute,identity,bridge=_real_evaluator(HOME.parents[1]/'shared/runtime')
    try:
        assert identity['backend']=='racket' and identity['protected'] is True
        assert execute(f.program({'selection':selection}),scene())==wanted(selection)
    finally:bridge.close()


def test_protected_wrong_order_reverses_the_two_rank_choices():
    from arcpuzzles.parametric_worker import _real_evaluator
    f=family();execute,_,bridge=_real_evaluator(HOME.parents[1]/'shared/runtime')
    try:
        assert execute(f.wrong_order_program({'selection':'largest'}),scene())==wanted('smallest')
        assert execute(f.wrong_order_program({'selection':'smallest'}),scene())==wanted('largest')
    finally:bridge.close()


def test_blank_rendering_preserves_lawful_source_destination_overlap():
    from arcpuzzles.parametric_worker import _real_evaluator
    f=family();grid=[[0]*8 for _ in range(8)]
    for r in range(4):grid[r][0]=2
    for r,c in ((0,3),(1,3),(2,3),(2,2)):grid[r][c]=3
    expected=[[0]*8 for _ in range(8)]
    expected[0][:4]=[2]*4
    for r,c in ((0,4),(1,2),(1,3),(1,4)):expected[r][c]=3
    assert f.apply(grid,{'selection':'all'})==expected
    execute,_,bridge=_real_evaluator(HOME.parents[1]/'shared/runtime')
    try:
        assert execute(f.program({'selection':'all'}),grid)==expected
        wrong=execute(f.rivals({'selection':'all'})['erase_and_paint_in_place'],grid)
        assert wrong[0][3]==0 and sum(v==2 for row in wrong for v in row)==3
    finally:bridge.close()
