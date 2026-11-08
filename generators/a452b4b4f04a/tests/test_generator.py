"""Run explicitly: python -m pytest generators/a452b4b4f04a/tests -q."""
from copy import deepcopy
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HOME/'workspace'))
from probe_support import (load_generator, canonical, pairs, points,
                           independent_output, observed, on_boundary)
gen=load_generator()


@pytest.mark.parametrize('pair',pairs(),ids=['train0','train1','train2','train3','test0'])
def test_canonical_inputs_are_accepted(pair):
    assert gen.self_check(pair['input']) == []
    assert independent_output(pair['input']) == pair['output']


def test_canonical_rule_hash_is_pinned():
    expected=hashlib.sha256(' '.join(canonical()['program_solution'].split()).encode()).hexdigest()[:12]
    assert getattr(gen,'RULE_HASH',None) == expected


@pytest.mark.parametrize('band',[None,'easy','medium','hard'])
def test_exact_control_cartesian_boundaries(band):
    # Every advertised combination must fit; never silently drop an object.
    for h,w,n,k in product((6,7,8,12,20),(6,8,11,20),(1,2,3),(2,3,4)):
        request=dict(grid_h=h,grid_w=w,n_colors=n,corner_count=k)
        grid=gen.generate(710,h+w+n+k,difficulty=band,**request)
        assert observed(grid) == request
        assert gen.observe_overrides(grid) == request
        assert gen.self_check(grid) == []


@pytest.mark.parametrize('key,value',[
    ('typo',1),('grid_h',5),('grid_h',21),('grid_w',5),('grid_w',21),
    ('n_colors',0),('n_colors',4),('corner_count',1),('corner_count',5),
    ('n_colors',True),('grid_h',8.0),('corner_count','3'),
    ('palette_kind','warm'),('texture','no_colors'),('density','sparse'),
])
def test_invalid_and_retired_axes_fail_loudly(key,value):
    with pytest.raises(ValueError):
        gen.generate(10,0,**{key:value})


@pytest.mark.parametrize('grid',[None,[],[[]],[[0],[0,1]],[[10,0],[0,0]],[[True,0],[0,False]]])
def test_malformed_grid_reports_reasons_instead_of_crashing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize('mutation',['interior','stray','single','collinear','overlap'])
def test_invalid_geometry_is_rejected(mutation):
    grid=[[0]*9 for _ in range(9)]
    grid[1][1]=grid[1][5]=grid[5][1]=2
    if mutation=='interior':grid[3][3]=2
    if mutation=='stray':grid[0][3]=2
    if mutation=='single':grid[1][1]=grid[1][5]=0
    if mutation=='collinear':grid[5][1]=0
    if mutation=='overlap':grid[3][3]=grid[6][6]=4
    assert gen.self_check(grid)


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_distribution_restores_palette_and_geometric_support(band):
    colors=set();counts=set();markers=set();diagonals=set();missing=set();shapes=set();edges=0
    for i in range(300):
        grid=gen.generate(4200+i,i*11,difficulty=band)
        assert gen.self_check(grid)==[]
        assert grid==gen.generate(4200+i,i*11,difficulty=band)
        pp=points(grid); colors.update(pp);counts.add(len(pp));shapes.add((len(grid),len(grid[0])))
        for coords in pp.values():
            markers.add(len(coords)); rs,cs=zip(*coords)
            corners={(min(rs),min(cs)),(min(rs),max(cs)),(max(rs),min(cs)),(max(rs),max(cs))}
            if len(coords)==2:diagonals.add('main' if sorted(coords)[0][1]<sorted(coords)[1][1] else 'anti')
            if len(coords)==3:
                r,c=next(iter(corners-set(coords)))
                missing.add((r==max(rs),c==max(cs)))
        edges += on_boundary(grid)
        assert independent_output(grid)!=grid
    assert colors==set(range(1,10))
    assert counts=={1,2,3}
    assert markers=={2,3,4}
    assert diagonals=={'main','anti'}
    assert len(missing)==4
    assert len(shapes)>30
    assert edges>0


def test_three_demo_windows_refute_declared_canonical_shortcuts():
    shortcuts=getattr(gen,'CANONICAL_SHORTCUTS',{})
    assert shortcuts, 'Missing executable canonical shortcut contract'
    assert set(shortcuts) <= set(gen.LESSON_COMPETITORS)
    for name,rival in shortcuts.items():
        assert all(rival(p['input'])==p['output'] for p in pairs()), name
    for band,seed,start in product(('easy','medium','hard'),range(20),range(3)):
        demos=[gen.generate(seed,start+i,difficulty=band) for i in range(3)]
        for name,rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(g)!=independent_output(g) for g in demos), (band,seed,start,name)


def test_strict_hook_means_single_color_three_corners():
    assert hasattr(gen,'strict_canonical_like')
    assert all(gen.strict_canonical_like(p['input'])==[] for p in pairs())
    for i in range(30):
        g=gen.generate(89,i)
        obs=observed(g)
        assert (gen.strict_canonical_like(g)==[]) == (obs['n_colors']==1 and obs['corner_count']==3)


@pytest.mark.parametrize('turns,reflect',product(range(4),(False,True)))
def test_rotation_reflection_preserve_domain_and_output(turns,reflect):
    def transform(g):
        x=deepcopy(g)
        if reflect:x=[row[::-1] for row in x]
        for _ in range(turns):x=[list(row) for row in zip(*x[::-1])]
        return x
    for i in range(12):
        g=gen.generate(719,i)
        assert gen.self_check(transform(g))==[]
        assert independent_output(transform(g))==transform(independent_output(g))


def test_corner_color_five_is_not_special():
    for color in range(1,10):
        g=[[0]*8 for _ in range(8)]
        g[1][1]=g[1][6]=g[6][1]=color
        assert gen.self_check(g)==[]


def test_selected_active_authority_exactly_matches_canonical():
    path=HOME.parents[1]/'shared/data/base/solutions/banks/0f1ff2289d6f/E72__a452b4b4f04a.json'
    active=json.loads(path.read_text())['racket_target']['target_code']
    assert active==canonical()['program_solution']


def test_lesson_hook_checks_demonstrations_not_query_labels():
    hook=getattr(gen,'lesson_identifiable',None)
    assert callable(hook), 'Missing lesson-level executable gate'
    demos=[{'input':gen.generate(700,i),'output':independent_output(gen.generate(700,i))} for i in range(3)]
    query={'input':gen.generate(700,3)}
    assert hook(demos,query)==[]
    assert hook(pairs()[:3],query), 'Canonical-only demos do not refute the global bbox rival'
    assert hook(demos[:1],query)
    assert hook([None]*3,query)
