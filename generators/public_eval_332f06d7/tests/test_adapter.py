from pathlib import Path
import copy
import importlib.util
import json
import sys
import pytest
HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'

def adapter():
    assert (BASE/'adapter.py').is_file(),'Native adapter missing'
    s=importlib.util.spec_from_file_location('_motion_adapter_test',BASE/'adapter.py')
    a=importlib.util.module_from_spec(s);sys.modules[s.name]=a;s.loader.exec_module(a);return a

@pytest.mark.parametrize('seed',[0,4,17,43])
def test_matched_independent_counts_and_boundary_routing(seed):
    a=adapter();eps=[a.generate(seed,{'travel':mode},6,4)for mode in ('terminal','halfway')]
    assert [p['input']for p in eps[0]['train']+eps[0]['test']]==[p['input']for p in eps[1]['train']+eps[1]['test']]
    for ep in eps:
        assert len(ep['train'])==6 and len(ep['test'])==4
        assert len({json.dumps(p['input'])for p in ep['train']+ep['test']})==10
        for n in range(2,7):
            small=a.generate(seed,ep['settings'],n,1)
            assert small['train']==ep['train'][:n] and small['test']==ep['test'][:1]
        g=ep['test'][3]['input'];d=a.model.analyze(g)
        assert len(g)==len(g[0])==30 and d['shape']==(4,4)
        assert len(d['walkable'])>550 and len(d['route'])>70
        assert d['scores'][d['terminal']]>0  # The 4x4 block cannot cross the final neck.
    assert eps[0]['train'][0]['output']!=eps[1]['train'][0]['output']

def test_visible_demos_teach_arrival_and_size_limited_stop():
    a=adapter();ep=a.generate(17,{'travel':'terminal'},2,4)
    x,y=[a.model.analyze(p['input'])for p in ep['train']]
    assert x['scores'][x['terminal']]==0 and y['scores'][y['terminal']]>0
    assert len(x['route'])>8 and len(y['route'])>8

@pytest.mark.parametrize('settings',[{},None,{'travel':'wrong'},{'travel':'terminal','hidden':1}])
def test_settings_fail_closed(settings):
    with pytest.raises(ValueError):adapter().program(settings)

@pytest.mark.parametrize('args',[(True,2,4),(-1,2,4),(1,1,4),(1,7,4),(1,2,0),(1,2,5),(1,True,4)])
def test_count_and_seed_boundaries(args):
    s,d,q=args
    with pytest.raises(ValueError):adapter().generate(s,{'travel':'terminal'},d,q)

def test_exact_default_and_one_query_hidden_field_invariance():
    a=adapter();ep=a.generate(17,{'travel':'halfway'},2,4)
    assert a.program({'travel':'terminal'})==(HOME/'reference.rkt').read_text()==(BASE/'canonical.rkt').read_text()
    before=copy.deepcopy(ep);view=a.public_view(ep,0,13)
    assert len(view['test'])==1 and set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    changed=copy.deepcopy(ep);changed['settings']={'secret':1};changed['seed']=99;changed['program_solution']='hidden'
    for p in changed['train']:p['private']='not visible'
    for p in changed['private']['query_bank']:p['output']=[[9]]
    assert a.public_view(changed,0,13)==view and ep==before
    assert a.public_view(a.generate(17,{'travel':'halfway'},2,1),0,13)==view
    assert len({json.dumps(a.public_view(ep,0,s)['test'])for s in range(16)})==4

def test_minimum_prefix_teaches_half_rounding_and_whole_goal_coverage():
    a=adapter()
    for seed in (0,1,4,17):
        g=a.generate(seed,{'travel':'halfway'},2,4)['train'][0]['input']
        d=a.model.analyze(g)
        assert d['shape'][0]>=3  # Partial overlap differs by >=2 route steps.
        assert (len(d['route'])-1)%2==1  # Floor and ceil halfway must differ visibly.
