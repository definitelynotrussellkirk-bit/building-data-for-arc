import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace/parametric'

def load(name='model', path=None):
    path = path or BASE / (name + '.py')
    assert path.is_file(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location('_size_' + name + str(path).encode().hex(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('index', range(4))
def test_originals(index):
    pair = json.loads((HOME/'tests/fixtures/originals.json').read_text())['pairs'][index]
    assert load().solve(pair['input'], 'occupied_area') == pair['output']

def test_same_color_components_are_not_merged_and_diagonal_cells_are_connected():
    # A diagonal size-two object and a horizontal size-two partner go up.
    # A singleton of the same color as the diagonal object goes down.
    grid = [[0]*9 for _ in range(8)]
    for r,c,v in [(3,0,2),(4,1,2),(4,4,3),(4,5,3),(2,8,2)]: grid[r][c]=v
    want = [[0]*9 for _ in range(8)]
    for r,c,v in [(0,0,2),(1,1,2),(0,4,3),(0,5,3),(7,8,2)]: want[r][c]=v
    assert load().solve(grid) == want

def test_box_metric_changes_grouping_without_changing_pixels():
    grid = [[0]*9 for _ in range(8)]
    for r,c,v in [(3,0,2),(4,1,2),(4,4,3),(4,5,3),(2,8,2)]: grid[r][c]=v
    want = [[0]*9 for _ in range(8)]
    for r,c,v in [(6,0,2),(7,1,2),(7,4,3),(7,5,3),(7,8,2)]: want[r][c]=v
    assert load().solve(grid,'bbox_area') == want

@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_determinism_matched_inputs_and_distinct_queries(demos):
    a=load('adapter')
    for seed in (0,17,43):
        x=a.generate(seed,{'match_by':'occupied_area'},demos,4)
        y=a.generate(seed,{'match_by':'bbox_area'},demos,4)
        assert x==a.generate(seed,{'match_by':'occupied_area'},demos,4)
        assert len(x['train'])==demos and len(x['test'])==4
        inputs=lambda e:[p['input'] for split in ('train','test') for p in e[split]]
        assert inputs(x)==inputs(y)
        assert len({json.dumps(g) for g in inputs(x)})==demos+4
        assert x['train'][0]['output']!=y['train'][0]['output']
        assert a.generate(seed,{'match_by':'occupied_area'},2,4)['train']==x['train'][:2]
        stress=[p for p in x['test'] if len(p['input'])==len(p['input'][0])==30]
        assert len(stress)==1
        model=load(); records=model.analyze(stress[0]['input'])['objects']
        cells=[(r,c) for obj in records for r,c in obj['cells']]
        assert min(r for r,c in cells)==0 and max(r for r,c in cells)==29
        assert min(c for r,c in cells)==0 and max(c for r,c in cells)==29
        assert len(records)>=6 and len(cells)>=40

@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('demos',1),('demos',7),('demos',True),('queries',1),('queries',3),('queries',5),('queries',True)])
def test_bad_counts_are_rejected(field,value):
    args={'seed':17,'settings':{'match_by':'occupied_area'},'demos':3,'queries':4};args[field]=value
    with pytest.raises(ValueError):load('adapter').generate(**args)

@pytest.mark.parametrize('settings',[{}, {'match_by':'no'}, {'match_by':True}, {'match_by':'occupied_area','extra':1}])
def test_bad_settings_are_rejected(settings):
    with pytest.raises(ValueError):load('adapter').generate(0,settings,2,4)

def test_canonical_program_contract():
    a=load('adapter')
    assert a.program({'match_by':'occupied_area'})==(HOME/'reference.rkt').read_text()
    assert a.program({'match_by':'bbox_area'})!=a.program({'match_by':'occupied_area'})

def test_input_and_global_rng_are_not_mutated():
    import random
    a=load('adapter');state=random.getstate();setting={'match_by':'bbox_area'}
    e=a.generate(9,setting,2,4);before=copy.deepcopy(e['test'][0]['input'])
    load().solve(e['test'][0]['input'],'occupied_area')
    assert e['test'][0]['input']==before and setting=={'match_by':'bbox_area'} and random.getstate()==state

def test_generator_is_standalone_when_relocated(tmp_path):
    source=HOME/'generator.py';assert source.is_file()
    target=tmp_path/'standalone.py';target.write_bytes(source.read_bytes())
    m=load('standalone',target)
    for i in range(4):
        g=m.generate(17,i,difficulty='medium');assert m.self_check(g)==[]
        assert m.solve(g)==load().solve(g)

def test_originals_in_protected_racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    root=HOME.parents[1];program=(HOME/'reference.rkt').read_text()
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    try:
        assert identity['protected'] is True
        for p in json.loads((HOME/'tests/fixtures/originals.json').read_text())['pairs']:
            assert apply(program,p['input'])==p['output']
    finally:bridge.close()

def test_finite_rivals_do_not_survive_demos_and_change_queries():
    result=load('audit').audit([0,17,31],[2,3,6])
    assert result['status']=='passed' and result['failures']==[]
    assert result['episodes']==18 and result['pairs']==138
    assert result['max_size_episodes']==18 and len(result['rivals'])>=15

def test_sampler_32_seed_boundaries_and_counts():
    m=load();sizes=set(); backgrounds=set()
    for seed in range(32):
        for q in range(4):
            grid=m.scene(seed,q,query=True)
            assert m.self_check(grid)==[]
            data=m.analyze(grid);sizes.add(len(data['objects']));backgrounds.add(data['background'])
    assert sizes=={6,7,8} and len(backgrounds)>=8
