"""Native first-seed/parity-relay API and causal regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import pytest

TASK = next(p for p in Path(__file__).resolve().parents if (p/'generator.py').is_file())
HOME = TASK/'workspace/parametric'

@pytest.fixture(scope='module')
def api():
    s=importlib.util.spec_from_file_location('native_seed_tests',HOME/'prototype.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def grid(h,w,cells):
    g=[[0]*w for _ in range(h)]
    for r,c,v in cells:g[r][c]=v
    return g

def test_relay_uses_origin_mask_then_target_geometry_and_color(api):
    g=grid(8,11,[(1,5,7),(1,7,2),(2,0,1),(3,9,6),(4,5,3),(5,1,9)])
    a=api.analyze(g,{'seed_mode':'parity_relay'})
    assert a['origin']==[1,5,7] and a['target']==[3,9,6]
    assert a['lane_mask'][1][7]==0 and a['lane_mask'][2][0]==0
    assert a['lane_mask'][3][9]==4
    assert a['output'][4][9]==6 and a['output'][2][5]==4
    assert api.mirror(g,{'seed_mode':'first'})[2][5]==7
    assert a['output']!=api.mirror(g,{'seed_mode':'first'})

def test_no_hit_falls_back_even_with_same_row_same_parity_markers(api):
    g=grid(5,7,[(1,1,2),(1,3,8),(2,0,5),(4,6,9)])
    a=api.analyze(g,{'seed_mode':'parity_relay'})
    assert a['target']==[1,1,2] and a['eligible']==[]
    assert a['output']==api.mirror(g,{'seed_mode':'first'})

def test_bottom_hit_has_canopy_and_no_echo(api):
    g=grid(4,5,[(0,1,6),(3,3,2)])
    out=api.mirror(g,{'seed_mode':'parity_relay'})
    assert out==[[0,4,0,4,0]]*4

def test_column_major_origin_is_wrong(api):
    g=grid(5,7,[(1,5,8),(2,1,3)])
    assert api.analyze(g,{'seed_mode':'first'})['origin']==[1,5,8]

@pytest.mark.parametrize('g',[[[3]],[[0,0,6]],[[0],[8],[2]],[[1,2],[3,5]]])
@pytest.mark.parametrize('mode',['first','parity_relay'])
def test_degenerate_dimensions_are_lawful(api,g,mode):
    out=api.mirror(g,{'seed_mode':mode})
    assert len(out)==len(g) and len(out[0])==len(g[0])

@pytest.mark.parametrize('g',[[],[[]],[[0]],[[False]],[[3.0]],[[4]],[[10]],[[1],[0,0]],[[1]*31]])
def test_strict_input_grammar(api,g):
    with pytest.raises((TypeError,ValueError)):api.mirror(g,{'seed_mode':'first'})

@pytest.mark.parametrize('s',[None,{}, {'seed_mode':True},{'seed_mode':'x'},{'seed_mode':'first','x':1}])
def test_strict_settings(api,s):
    with pytest.raises((TypeError,ValueError)):api.program(s)

@pytest.mark.parametrize('seed,demos,queries',[(True,3,4),(-1,3,4),(2**63,3,4),(0.0,3,4),(0,1,4),(0,2,4),(0,7,4),(0,True,4),(0,3,0),(0,3,5),(0,3,1.0)])
def test_seed_count_bounds(api,seed,demos,queries):
    with pytest.raises((TypeError,ValueError)):api.generate(seed,{'seed_mode':'first'},demos,queries)

@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_deterministic_matched_prefixes_and_distinct_inputs(api,seed):
    state=random.getstate()
    full=api.generate(seed,{'seed_mode':'first'},6,4)
    alt=api.generate(seed,{'seed_mode':'parity_relay'},6,4)
    small=api.generate(seed,{'seed_mode':'first'},3,1)
    assert random.getstate()==state
    assert small['train']==full['train'][:3] and small['test']==full['test'][:1]
    assert full==api.generate(seed,{'seed_mode':'first'},6,4)
    assert [p['input'] for p in full['train']+full['test']]==[p['input'] for p in alt['train']+alt['test']]
    assert len({json.dumps(p['input']) for p in full['train']+full['test']})==10
    assert {(len(p['input']),len(p['input'][0])) for p in full['test']}=={(5,7),(13,17),(23,27),(30,30)}
    for mode,ep in [('first',full),('parity_relay',alt)]:
        for pair in ep['train']+ep['test']:
            assert api.mirror(pair['input'],{'seed_mode':mode})==pair['output']

def test_no_mutation_or_return_aliasing(api):
    ep=api.generate(0,{'seed_mode':'parity_relay'});before=copy.deepcopy(ep)
    g=ep['train'][0]['input'];api.mirror(g,{'seed_mode':'first'});assert ep==before
    ep['train'][0]['input'][0][0]=9;ep['test'][0]['output'][0][0]=9
    assert api.generate(0,{'seed_mode':'parity_relay'})==before


@pytest.mark.parametrize('seed',[0,17])
def test_teaching_covers_direction_color_extremes_fallback_and_bottom(api,seed):
    ep=api.generate(seed,{'seed_mode':'parity_relay'},3,4)
    active,fallback,bottom=[api.analyze(p['input'],{'seed_mode':'parity_relay'}) for p in ep['train']]
    assert active['target'][1]<active['origin'][1]
    assert min(p[2] for p in active['eligible'])<active['target'][2]<max(p[2] for p in active['eligible'])
    assert active['target'][2]!=active['origin'][2]
    distance=lambda p:(p[0]-active['origin'][0])**2+(p[1]-active['origin'][1])**2
    assert min(distance(p) for p in active['eligible'])<distance(active['target'])
    assert fallback['eligible']==[] and fallback['target']==fallback['origin']
    assert bottom['target'][0]==len(bottom['output'])-1
    assert bottom['target'][1]>bottom['origin'][1]
    assert all(p[2]==bottom['origin'][2] for p in bottom['eligible'])
