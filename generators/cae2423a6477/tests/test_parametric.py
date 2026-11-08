"""Native selected-frame / global-enclosure contract tests."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest

TASK = next(p for p in Path(__file__).resolve().parents if (p / 'generator.py').is_file())
HOME = TASK / 'workspace/parametric'


@pytest.fixture(scope='module')
def api():
    spec = importlib.util.spec_from_file_location('cae_native_tests', HOME / 'prototype.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def frame(g, top, left, h, w):
    for r in range(h):
        for c in range(w):
            if r in (0, h-1) or c in (0, w-1): g[top+r][left+c] = 3


def cage():
    g = [[0]*9 for _ in range(9)]
    for r,c in [(0,3),(3,0),(3,6),(6,3)]: frame(g,r,c,3,3)
    return g


def test_collective_enclosure_is_not_per_frame_bbox_fill(api):
    g = cage(); original = copy.deepcopy(g)
    a = api.mirror(g, {'completion_mode':'border'})
    b = api.mirror(g, {'completion_mode':'enclosed'})
    assert sum(v == 7 for row in a for v in row) == 32
    assert sum(v == 2 for row in b for v in row) == 13
    assert all(b[r][c] == 2 for r in range(3,6) for c in range(3,6))
    assert g == original
    assert api.second_stage(a) == b
    assert api.second_stage(g) == g


def test_green_content_is_passable_but_preserved(api):
    g = [[0]*7 for _ in range(7)]; frame(g,0,0,7,7);g[3][3]=3
    b = api.mirror(g, {'completion_mode':'enclosed'})
    assert b[3][3] == 3
    assert sum(v==2 for row in b for v in row) == 24


def test_green_nubbed_ring_does_not_form_an_orange_barrier(api):
    g = [[0]*6 for _ in range(6)];frame(g,0,0,5,5);g[2][5]=3
    assert api.mirror(g, {'completion_mode':'enclosed'}) == g


@pytest.mark.parametrize('grid', [[[0]],[[3]],[[3,3,3]],[[3],[3],[3]],[[3,3,3],[3,3,3]]])
@pytest.mark.parametrize('mode',['border','enclosed'])
def test_thin_shapes_are_not_frames(api,grid,mode):
    assert api.mirror(grid,{'completion_mode':mode}) == grid


@pytest.mark.parametrize('grid',[[],[[]],[[False]],[[3.0]],[[1]],[[7]],[[2]],[[0],[0,0]],[[0]*31]])
def test_strict_original_grammar(api,grid):
    with pytest.raises((TypeError,ValueError)):api.mirror(grid,{'completion_mode':'border'})


@pytest.mark.parametrize('settings',[{},None,{'completion_mode':'other'},{'completion_mode':True},{'completion_mode':'border','x':1}])
def test_settings_exact(api,settings):
    with pytest.raises((TypeError,ValueError)):api.program(settings)


@pytest.mark.parametrize('seed,demos,queries',[(True,3,4),(-1,3,4),(2**63,3,4),(0.0,3,4),(0,1,4),(0,7,4),(0,True,4),(0,3,0),(0,3,5),(0,3,1.0)])
def test_count_and_seed_bounds(api,seed,demos,queries):
    with pytest.raises((TypeError,ValueError)):api.generate(seed,{'completion_mode':'border'},demos=demos,queries=queries)


@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_matched_inputs_prefixes_distinct_and_rng(api,seed):
    before=random.getstate()
    a=api.generate(seed,{'completion_mode':'border'},demos=2,queries=1)
    b=api.generate(seed,{'completion_mode':'border'},demos=6,queries=4)
    c=api.generate(seed,{'completion_mode':'enclosed'},demos=6,queries=4)
    assert random.getstate()==before
    assert a==api.generate(seed,{'completion_mode':'border'},demos=2,queries=1)
    assert a['train']==b['train'][:2] and a['test']==b['test'][:1]
    assert [p['input'] for p in b['train']+b['test']]==[p['input'] for p in c['train']+c['test']]
    assert len({json.dumps(p['input']) for p in b['train']+b['test']})==10
    assert {(len(p['input']),len(p['input'][0])) for p in b['test']}=={(9,11),(17,21),(25,29),(30,30)}
    for mode,episode in [('border',b),('enclosed',c)]:
        for pair in episode['train']+episode['test']:
            assert pair['output']==api.mirror(pair['input'],{'completion_mode':mode})


def test_returned_arrays_are_fresh(api):
    a=api.generate(0,{'completion_mode':'enclosed'});old=copy.deepcopy(a)
    a['train'][0]['input'][0][0]=9;a['test'][0]['output'][0][0]=9
    assert api.generate(0,{'completion_mode':'enclosed'})==old


@pytest.mark.parametrize('mode',['border','enclosed'])
def test_dihedral_semantics(api,mode):
    g=cage();g[0][0]=3
    output=api.mirror(g,{'completion_mode':mode})
    for turns in range(4):
        for flip in (False,True):
            transformed=api.transform(g,turns,flip)
            assert api.mirror(transformed,{'completion_mode':mode})==api.transform(output,turns,flip)
