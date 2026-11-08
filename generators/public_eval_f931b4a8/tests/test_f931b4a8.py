import copy
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]

def api():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'Missing two-scale implementation'
    s=importlib.util.spec_from_file_location('quadrant_test_adapter',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def originals():
    d=json.loads((HOME/'tests/originals.json').read_text());return d['train']+d['test']

@pytest.mark.parametrize('index',range(7))
def test_all_official_labels(index):
    p=originals()[index]
    assert api().solve(p['input'],{'background_sampling':'block'})==p['output']

def test_handderived_layers_and_scale():
    a=api()
    grid=[[1,1,2,2],[1,1,0,0],[3,4,7,0],[5,6,0,8]]
    assert a.solve(grid,{'background_sampling':'block'})==[[7,3],[3,8],[7,5],[5,8]]
    assert a.solve(grid,{'background_sampling':'periodic'})==[[7,4],[5,8],[7,4],[5,8]]

def test_zero_pattern_and_zero_backing_are_literal():
    a=api()
    grid=[[1,0,2,2],[0,0,0,0],[0,4,0,0],[5,6,0,0]]
    assert a.solve(grid,{'background_sampling':'block'})==[[0,4]]
    assert a.solve(grid,{'background_sampling':'periodic'})==[[0,4]]

@pytest.mark.parametrize('settings',[{}, {'background_sampling':True},{'background_sampling':'bad'},{'background_sampling':'block','extra':0}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):api().generate(0,settings,2,4)

@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(-1,2,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,True,4)])
def test_invalid_counts(seed,demos,queries):
    with pytest.raises(ValueError):api().generate(seed,{'background_sampling':'block'},demos,queries)

@pytest.mark.parametrize('grid',[[[0]],[[1,0],[0,0]],[[True,1],[0,0]],[[1,1,1],[1,1,1]],[[1,1],[1]]])
def test_bad_grammar(grid):
    with pytest.raises(ValueError):api().solve(grid,{'background_sampling':'block'})

def test_all_prefixes_matched_inputs_and_distinctness():
    a=api()
    for seed in [0,1,17,43]:
        all_e=[a.generate(seed,s,6,4) for s in a.SETTINGS]
        assert [p['input'] for p in all_e[0]['train']+all_e[0]['test']]==[p['input'] for p in all_e[1]['train']+all_e[1]['test']]
        for s,e in zip(a.SETTINGS,all_e):
            assert len({json.dumps(p['input']) for p in e['train']+e['test']})==10
            for d in range(2,7):
                for q in range(1,5):
                    little=a.generate(seed,s,d,q)
                    assert little['train']==e['train'][:d] and little['test']==e['test'][:q]
            for i in range(4):
                view=a.public_view(e,i);altered=copy.deepcopy(e);altered['settings']={};altered['program_solution']='private'
                for j,p in enumerate(altered['test']):
                    p['output']=[[9]]
                    if j!=i:p['input']=[[0]]
                assert view==a.public_view(altered,i)
                assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}

def test_stress_and_first_query_varies():
    a=api();sizes=[]
    for seed in range(16):
        e=a.generate(seed,a.SETTINGS[0],2,4)
        stress=[p for p in e['test'] if len(p['input'])==30]
        assert len(stress)==1 and len(stress[0]['output'])==30 and len(stress[0]['output'][0])==30
        assert sum(v!=0 for row in stress[0]['input'] for v in row)>=300
        sizes.append(len(e['test'][0]['input']))
    assert len(set(sizes))>=3

def test_canonical_resource_and_settings_differ():
    a=api()
    assert a.program(a.SETTINGS[0]).encode()==(HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    for seed in range(16):
        one,two=[a.generate(seed,s,2,4) for s in a.SETTINGS]
        assert any(x['output']!=y['output'] for x,y in zip(one['train'],two['train']))


def test_absent_stencil_is_identity_tile_not_quadrant_sized_hole():
    a=api()
    grid=[[1,1,2,2],[0,0,2,2],[3,4,0,0],[5,6,0,0]]
    assert a.solve(grid,{'background_sampling':'block'})==[[3,4,3,4],[5,6,5,6]]
    assert a.solve([[1,1],[0,0]],{'background_sampling':'block'})==[[0]]

def test_counter_values_vary_independently_of_quadrant_size():
    a=api();counts_by_side={}
    for seed in range(24):
        e=a.generate(seed,a.SETTINGS[0],2,4)
        for p in e['train']+e['test']:
            side,h,w,_,_=a.model.analyze(p['input'])
            counts_by_side.setdefault(side,set()).add((h,w))
    assert len(counts_by_side[3])>=8
    assert len(counts_by_side[7])>=8
    assert len(counts_by_side[4])>=8
