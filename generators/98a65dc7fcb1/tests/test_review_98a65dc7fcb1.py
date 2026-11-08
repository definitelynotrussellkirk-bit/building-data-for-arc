"""Task-local regression tests; run explicitly (root pytest uses tests/ only)."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('review_ring_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def targets(grid):
    result = []
    for r in range(1, len(grid)-1):
        for c in range(1, len(grid[0])-1):
            perimeter = [grid[i][j] for i in range(r-1,r+2)
                         for j in range(c-1,c+2) if (i,j)!=(r,c)]
            if grid[r][c] == 0 and perimeter[0] and len(set(perimeter)) == 1:
                result.append((r,c,perimeter[0]))
    return result


def oracle(grid):
    out = copy.deepcopy(grid)
    for r,c,color in targets(grid): out[r][c] = color
    return out


def cardinal(grid):
    out = copy.deepcopy(grid)
    for r in range(1,len(grid)-1):
        for c in range(1,len(grid[0])-1):
            ns = [grid[r-1][c],grid[r+1][c],grid[r][c-1],grid[r][c+1]]
            if grid[r][c] == 0 and ns[0] and len(set(ns))==1: out[r][c]=ns[0]
    return out


@pytest.mark.parametrize('band',['easy','medium','hard'])
@pytest.mark.parametrize('texture',['default','contrast','attached'])
@pytest.mark.parametrize('dims',[(5,5,1,0),(5,18,3,0),(18,18,6,3)])
def test_exact_shape_and_counts(band,texture,dims):
    h,w,n,d = dims
    g = gen.generate(713,2,difficulty=band,grid_h=h,grid_w=w,
                     n_rings=n,n_decoys=d,texture=texture)
    assert (len(g),len(g[0])) == (h,w)
    assert len(targets(g)) == n
    assert gen.self_check(g) == []
    assert hasattr(gen,'observe_overrides'), 'exact counts need an observer'
    assert gen.observe_overrides(g) == {'grid_h':h,'grid_w':w,'n_rings':n,'n_decoys':d}


@pytest.mark.parametrize('key',['typo_axis','palette_size','n_distinct_colors','position_bias','density'])
def test_unknown_or_removed_axis_is_not_silently_ignored(key):
    with pytest.raises(ValueError,match='unknown override'):
        gen.generate(11,0,**{key:2})


@pytest.mark.parametrize('band',['easy','medium','hard'])
def test_every_default_lesson_rejects_four_neighbor_shortcut(band):
    grids = [gen.generate(713,i,difficulty=band) for i in range(12)]
    for start in range(10):
        assert any(cardinal(g) != oracle(g) for g in grids[start:start+3]), (band,start)


def test_capacity_failure_is_structured_not_silent_underfill():
    with pytest.raises(ValueError) as e:
        gen.generate(42,0,grid_h=5,grid_w=5,n_rings=2,n_decoys=0)
    assert set(getattr(e.value,'incompatible_axes',())) >= {'grid_h','grid_w','n_rings'}


@pytest.mark.parametrize('bad',[[],[[]],[[0],[0,1]],[[True]*5]*5,[[10]*5]*5,None])
def test_selfcheck_rejects_malformed_without_raising(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('axis',['grid_h','grid_w','n_rings','n_decoys'])
@pytest.mark.parametrize('bad',[True,1.5,'5'])
def test_integer_axis_rejects_coercion(axis,bad):
    with pytest.raises(ValueError): gen.generate(42,0,**{axis:bad})


def test_palette_choices_actually_control_colors():
    for name,palette in [('warm',{2,4,6,9}),('cool',{1,3,5,7,8})]:
        for i in range(8):
            g=gen.generate(712,i,palette_kind=name)
            assert {v for row in g for v in row if v} <= palette


def test_global_rng_purity_determinism_and_fresh_rows():
    random.seed(90210)
    state = random.getstate()
    a = gen.generate(42,3,difficulty='hard')
    assert random.getstate() == state
    b = gen.generate(42,3,difficulty='hard')
    assert a == b and a is not b and all(x is not y for x,y in zip(a,b))
    a[0][0] = (a[0][0]+1)%10
    assert a != b


def test_canonical_pairs_and_semantic_shortcuts():
    assert hasattr(gen,'rule_mirror'), 'parity hook must be available'
    rows = [json.loads(x) for x in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
    row = next(x for x in rows if x['task_id']==gen.TASK_ID)
    test = row['test']
    pairs = row['train'] + ([test] if isinstance(test,dict) else test)
    for p in pairs:
        assert gen.self_check(p['input']) == []
        assert gen.strict_canonical_like(p['input']) == []
        assert gen.rule_mirror(p['input']) == p['output'] == oracle(p['input'])
        for name,fn in gen.CANONICAL_SHORTCUTS.items():
            assert fn(p['input']) == p['output'],name


def test_all_semantic_rivals_are_refuted_in_every_three_demo_window():
    assert hasattr(gen,'SEMANTIC_RIVALS'), 'publish executable rival probes'
    grids = [gen.generate(90210,i,difficulty='medium') for i in range(12)]
    for start in range(9):
        demos=[{'input':g,'output':oracle(g)} for g in grids[start:start+3]]
        for name,fn in gen.SEMANTIC_RIVALS.items():
            assert any(fn(p['input']) != p['output'] for p in demos),(start,name)
        assert gen.lesson_identifiable(demos,grids[start+3]) == []


def test_diagnostic_negative_textures_stay_out_of_training_domain():
    for name in gen.DEGENERATE_TEXTURES:
        assert name not in gen.AXES['texture']['valid'].split('|')
        g = gen.generate(11,0,texture=name)
        assert gen.self_check(g) and not targets(g)
