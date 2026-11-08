import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1];REPO=HOME.parents[1]
spec=importlib.util.spec_from_file_location('rooms_family_test',HOME/'workspace/parametric/native_family.py')
F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)


def add_frame(g,color,box,horizontal=(),vertical=()):
    t,l,b,r=box
    for c in range(l,r+1):g[t][c]=g[b][c]=color
    for y in range(t,b+1):g[y][l]=g[y][r]=color
    for y,a,z in horizontal:
        for c in range(a,z+1):g[y][c]=color
    for c,a,z in vertical:
        for y in range(a,z+1):g[y][c]=color


def fixture():
    g=[[0]*23 for _ in range(18)]
    add_frame(g,1,(2,1,10,9),horizontal=[(6,1,5)],vertical=[(5,2,10)])
    add_frame(g,3,(8,11,15,21),vertical=[(16,8,15)])
    for r,c in ((0,0),(17,22),(4,18),(12,3),(4,5),(2,4),(8,15)):g[r][c]=8
    return g


@pytest.mark.parametrize('order,expected',[
    ('ascending',[[3,3,8],[1,1,1]]),('descending',[[1,1,1],[3,3,8]])])
def test_partial_t_junction_and_damage(order,expected):
    g=fixture();before=copy.deepcopy(g)
    assert F.solve(g,{'sort_order':order})==expected
    assert g==before
    info=F.analyze(g)
    assert info['noise_color']==8
    assert {x['color']:x['rooms'] for x in info['objects']}=={1:3,3:2}


def test_all_original_labels():
    p=json.loads((REPO/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['89565ca0']
    gold=json.loads((REPO/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['89565ca0']
    for pair in p['train']:assert F.solve(pair['input'],F.DEFAULT)==pair['output']
    for pair,out in zip(p['test'],gold):assert F.solve(pair['input'],F.DEFAULT)==out


@pytest.mark.parametrize('same_left',[False,True])
def test_spatial_ties_keep_direction_under_descending(same_left):
    g=[[0]*30 for _ in range(19)]
    if same_left:
        add_frame(g,7,(1,1,7,7));add_frame(g,2,(10,1,17,7))
    else:
        add_frame(g,7,(10,1,17,7));add_frame(g,2,(1,10,7,16))
    add_frame(g,4,(4,19,15,28),vertical=[(24,4,15)])
    for r,c in ((0,0),(18,29),(2,23),(9,11),(16,21)):g[r][c]=8
    assert F.solve(g,{'sort_order':'ascending'})==[[7,8],[2,8],[4,4]]
    assert F.solve(g,{'sort_order':'descending'})==[[4,4],[7,8],[2,8]]


def test_foreign_wall_inside_box_is_not_borrowed():
    g=[[0]*25 for _ in range(20)]
    add_frame(g,1,(2,2,15,20))
    add_frame(g,3,(6,8,18,23),horizontal=[(12,8,23)])
    for r,c in ((0,0),(19,24),(4,23),(17,4),(3,2)):g[r][c]=8
    assert F.solve(g,F.DEFAULT)==[[1,8],[3,3]]


@pytest.mark.parametrize('grid',[[],[[]],[[True]],[[1.0]],[[10]],[[1],[1,2]],((1,2),(3,4)),[[0]*31]*2])
def test_strict_grid_types_and_sizes(grid):
    with pytest.raises((ValueError,TypeError)):F.solve(grid,F.DEFAULT)


@pytest.mark.parametrize('settings',[None,{},[],{'sort_order':True},{'sort_order':'ASCENDING'},{'sort_order':'ascending','extra':1}])
def test_strict_settings(settings):
    with pytest.raises((ValueError,TypeError)):F.program(settings)


def test_erased_wall_is_rejected_by_continuity():
    g=fixture();g[2][6]=0
    with pytest.raises(ValueError):F.solve(g,F.DEFAULT)


def test_no_unique_noise_is_rejected():
    g=fixture()
    for row in g:
        for c,v in enumerate(row):
            if v==8:row[c]=0
    with pytest.raises(ValueError):F.solve(g,F.DEFAULT)


def test_default_exact_bytes_and_programs_parse():
    from arc_repl.parser import parse_all
    assert F.program(F.DEFAULT)==(HOME/'reference.rkt').read_text()
    for order in ('ascending','descending'):
        assert len(parse_all(F.program({'sort_order':order})))==1
        for rival in F.rival_programs({'sort_order':order}).values():assert len(parse_all(rival))==1
