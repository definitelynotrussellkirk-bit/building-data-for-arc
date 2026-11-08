"""Independent fixtures for framed-picture alignment, including official gold."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
SPEC = importlib.util.spec_from_file_location('fc7_family_test', HOME / 'workspace/parametric/native_family.py')
F = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(F)

MAPS = ((0,1,2,3),(1,2,3,0),(2,3,0,1),(3,0,1,2),
        (0,3,2,1),(2,1,0,3),(3,2,1,0),(1,0,3,2))
PICTURE = [[1,1,0,1],[1,6,6,1],[8,1,1,7]]


def fixture(inner=(0,3), outer=(1,2), picture=None):
    picture = copy.deepcopy(PICTURE if picture is None else picture)
    ph,pw=len(picture),len(picture[0]); h,w=ph+8,pw+8
    g=[[0]*w for _ in range(h)]
    for side in range(4):
        col=2 if side==outer[0] else 3 if side==outer[1] else 5
        for k in range(1,(w if side%2==0 else h)-1):
            r,c=((0,k),(k,w-1),(h-1,k),(k,0))[side];g[r][c]=col
    r0,c0=4,4
    for r,row in enumerate(picture):g[r0+r][c0:c0+pw]=row
    for color,side in zip((2,3),inner):
        if side==0:g[r0-1][c0:c0+pw]=[color]*pw
        elif side==2:g[r0+ph][c0:c0+pw]=[color]*pw
        elif side==1:
            for r in range(r0,r0+ph):g[r][c0+pw]=color
        else:
            for r in range(r0,r0+ph):g[r][c0-1]=color
    return g


def oracle_transform(p,k):
    h,w=len(p),len(p[0])
    if k==0:return [row[:] for row in p]
    if k==1:return [[p[h-1-c][r] for c in range(h)] for r in range(w)]
    if k==2:return [[p[h-1-r][w-1-c] for c in range(w)] for r in range(h)]
    if k==3:return [[p[c][w-1-r] for c in range(h)] for r in range(w)]
    if k==4:return [[p[r][w-1-c] for c in range(w)] for r in range(h)]
    if k==5:return [[p[h-1-r][c] for c in range(w)] for r in range(h)]
    if k==6:return [[p[c][r] for c in range(h)] for r in range(w)]
    return [[p[h-1-c][w-1-r] for c in range(h)] for r in range(w)]


@pytest.mark.parametrize('pairing',['match','swap'])
def test_all_ordered_adjacent_frames(pairing):
    for a in range(4):
        for b in ((a-1)%4,(a+1)%4):
            for x in range(4):
                for y in ((x-1)%4,(x+1)%4):
                    targets=(x,y) if pairing=='match' else (y,x)
                    k=next(k for k,m in enumerate(MAPS) if (m[a],m[b])==targets)
                    g=fixture((a,b),(x,y));before=copy.deepcopy(g)
                    assert F.solve(g,{'marker_pairing':pairing})==oracle_transform(PICTURE,k)
                    assert g==before


def test_all_official_labels():
    challenge=json.loads((REPO/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['fc7cae8d']
    gold=json.loads((REPO/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['fc7cae8d']
    for pair in challenge['train']:
        assert F.solve(pair['input'],{'marker_pairing':'match'})==pair['output']
    for pair,answer in zip(challenge['test'],gold):
        assert F.solve(pair['input'],{'marker_pairing':'match'})==answer


def test_corner_spill_and_zero_notches_are_preserved():
    g=fixture((0,3),(1,2));g[1][-1]=3
    out=F.solve(g,{'marker_pairing':'match'})
    assert out==oracle_transform(PICTURE,7)
    assert sum(row.count(0) for row in out)==1


@pytest.mark.parametrize('grid',[[],[[]],[[True]],[[1.0]],[[10]],[[1],[1,2]],((1,2),(3,4)),[[0]*31]*2])
def test_strict_grid_types_and_sizes(grid):
    with pytest.raises((TypeError,ValueError)):F.solve(grid,{'marker_pairing':'match'})


@pytest.mark.parametrize('settings',[None,{},[],{'marker_pairing':True},{'marker_pairing':'MATCH'},
    {'marker_pairing':'match','extra':1}])
def test_strict_settings(settings):
    with pytest.raises((TypeError,ValueError)):F.program(settings)


def test_no_interior_and_two_interior_components_are_rejected():
    with pytest.raises(ValueError):F.solve([[0]*12 for _ in range(11)],{'marker_pairing':'match'})
    g=fixture();g[2][2]=9
    with pytest.raises(ValueError):F.solve(g,{'marker_pairing':'match'})


def test_markers_are_complete_adjacent_and_reserved():
    g=fixture();g[3][5]=0
    with pytest.raises(ValueError):F.solve(g,{'marker_pairing':'match'})
    g=fixture();g[5][5]=2
    with pytest.raises(ValueError):F.solve(g,{'marker_pairing':'match'})


def test_canonical_exact_bytes_and_single_program_expression():
    from arc_repl.parser import parse_all
    source=(HOME/'reference.rkt').read_text()
    assert F.program({'marker_pairing':'match'})==source
    assert F.program({'marker_pairing':'swap'})!=source
    for setting in ('match','swap'):
        expression=parse_all(F.program({'marker_pairing':setting}))
        assert len(expression)==1
        for rival in F.rival_programs({'marker_pairing':setting}).values():
            assert len(parse_all(rival))==1
