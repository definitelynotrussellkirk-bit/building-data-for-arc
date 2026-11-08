from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest
from reviewer_support import find_root
ROOT=find_root(__file__);HOME=ROOT/'generators/515cca15a0b7/workspace/parametric'
@pytest.fixture(scope='module')
def native():
    assert (HOME/'adapter.py').exists(), 'Native border adapter not implemented'
    spec=importlib.util.spec_from_file_location('border_native_test', HOME/'adapter.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_exact_canonical(native):
    from arcpuzzles import Catalog
    ss={v['program_solution'] for v in Catalog(ROOT).get(native.TASK)['variants'] if isinstance(v.get('program_solution'),str)}
    assert native.program({'preprocess':'none'})==ss.pop()

def test_recompute_connectivity_after_recolor_not_before(native):
    g=[[0,0,1,0,0],[0,0,1,0,0],[1,1,5,0,0],[0,0,0,0,0],[0,0,0,0,0]]
    want=[[0,0,1,0,0],[0,0,1,0,0],[1,1,1,0,0],[0,0,0,0,0],[0,0,0,0,0]]
    assert native.predict(g,'none')==[[0]*5 for _ in range(5)]
    assert native.predict(g,'gray_to_blue')==want
    assert native.rival(g,'wrong_order')==[[0]*5 for _ in range(5)]

def test_diagonal_only_neighbor_is_not_absorbed(native):
    g=[[0,0,1,0,0],[0,0,1,0,0],[1,1,5,0,0],[0,0,0,1,0],[0,0,0,0,0]]
    assert native.predict(g,'gray_to_blue')[3][3]==0
    assert native.rival(g,'diagonal_after')[3][3]==1

def test_global_same_color_union_does_not_decide_keep(native):
    g=[[0,1,0,0],[0,0,0,0],[1,0,0,0],[0,0,0,0]]
    assert native.predict(g,'none')==[[0]*4 for _ in range(4)]
    assert native.rival(g,'global_before')==g

@pytest.mark.parametrize('settings',[None,{}, {'preprocess':'bad'}, {'preprocess':'none','x':0}, {'preprocess':True}])
def test_setting_errors(native,settings):
    with pytest.raises((ValueError,TypeError)):native.program(settings)

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'demos':1},{'demos':7},{'demos':True},{'queries':0},{'queries':5},{'queries':False}])
def test_count_errors(native,kwargs):
    args=dict(seed=0,settings={'preprocess':'none'},demos=3,queries=4);args.update(kwargs)
    with pytest.raises((ValueError,TypeError)):native.generate(**args)

def test_matched_inputs_prefix_and_four_novel_queries(native):
    for seed in (0,17,91):
        a=native.generate(seed,{'preprocess':'none'},2,4)
        b=native.generate(seed,{'preprocess':'gray_to_blue'},6,1)
        assert [p['input'] for p in a['train']]==[p['input'] for p in b['train'][:2]]
        assert a['test'][0]['input']==b['test'][0]['input']
        assert len({json.dumps(p['input']) for split in ('train','test') for p in a[split]})==6

def test_dense_boundary_query_and_real_causal_difference(native):
    ep=native.generate(0,{'preprocess':'gray_to_blue'},2,4)
    g=ep['test'][3]['input'];assert len(g)==len(g[0])==30
    assert sum(v!=0 for row in g for v in row)>=200
    assert any(g[0]) and any(g[-1]) and any(row[0] for row in g) and any(row[-1] for row in g)
    assert ep['test'][3]['output'] != native.rival(g,'wrong_order')

def test_teaching_filter_has_no_query_answer_leak(native):
    ep=native.generate(0,{'preprocess':'gray_to_blue'},2,4)
    report=native.teaching(ep);assert report['passed']
    altered=deepcopy(ep);altered['test'][0]['output']=[[9]]
    other=native.teaching(altered)
    assert other['survivors']==report['survivors'] and not other['passed']

def test_only_current_public_turn_and_private_metadata_invariance(native):
    ep=native.generate(17,{'preprocess':'gray_to_blue'},2,4);v=native.public_turn(ep,0)
    altered=deepcopy(ep);altered['test']=altered['test'][:1];altered['test'][0]['output']=[[3]]
    altered['settings']={'secret':1};altered['program_solution']='secret'
    for split in ('train','test'):
        for p in altered[split]:p['secret']={'answers':[1,2,3]}
    assert v==native.public_turn(altered,0)
    assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}

def test_minimum_lesson_teaches_color_boundaries_after_merging(native):
    ep=native.generate(17,{'preprocess':'gray_to_blue'},2,4)
    assert any(native.rival(p['input'],'ignore_colors_after')!=p['output'] for p in ep['train'])
