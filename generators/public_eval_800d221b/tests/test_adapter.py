from pathlib import Path
import copy
import importlib.util
import json
import sys
import pytest

HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'

def adapter():
    assert (BASE/'adapter.py').is_file(), 'Native adapter missing'
    spec=importlib.util.spec_from_file_location('_network_adapter_test',BASE/'adapter.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('seed',[0,4,17,43])
def test_matched_counts_unique_queries_and_substantive_boundary_case(seed):
    a=adapter();eps=[a.generate(seed,{'aggregation':m},6,4) for m in ('contacts','chambers')]
    assert [p['input'] for p in eps[0]['train']+eps[0]['test']]==[p['input'] for p in eps[1]['train']+eps[1]['test']]
    for ep in eps:
        assert len(ep['train'])==6 and len(ep['test'])==4
        inputs=[p['input'] for p in ep['train']+ep['test']]
        assert len({json.dumps(g) for g in inputs})==10
        for n in range(2,7):
            short=a.generate(seed,ep['settings'],n,1)
            assert short['train']==ep['train'][:n] and short['test']==ep['test'][:1]
        g=ep['test'][3]['input'];data=a.model.analyze(g)
        assert len(g)==len(g[0])==30 and len(data['terminals'])==5
        assert sum(v!=data['background'] for row in g for v in row)>180
        assert all(any(v!=data['background'] for v in edge) for edge in (g[0],g[-1],[row[0] for row in g],[row[-1] for row in g]))
    assert eps[0]['train'][0]['output']!=eps[1]['train'][0]['output']

@pytest.mark.parametrize('settings',[{}, {'aggregation':'unknown'},{'aggregation':'contacts','leak':1},None])
def test_settings_are_exact_and_fail_closed(settings):
    with pytest.raises(ValueError):adapter().program(settings)

@pytest.mark.parametrize('args',[(True,2,4),(-1,2,4),(3,1,4),(3,7,4),(3,2,0),(3,2,5),(3,True,4)])
def test_count_and_seed_boundaries(args):
    seed,demos,queries=args
    with pytest.raises(ValueError):adapter().generate(seed,{'aggregation':'contacts'},demos,queries)

def test_default_bytes_and_controller_private_projection():
    a=adapter();ep=a.generate(17,{'aggregation':'chambers'},2,4)
    assert a.program({'aggregation':'contacts'})==(HOME/'reference.rkt').read_text()==(BASE/'canonical.rkt').read_text()
    before=copy.deepcopy(ep);view=a.public_view(ep,0,13)
    assert len(view['test'])==1 and set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    x=copy.deepcopy(ep);x['settings']={'secret':1};x['seed']=99;x['program_solution']='secret'
    for p in x['train']:p['hidden']='not visible'
    for p in x['private']['query_bank']:p['output']=[[9]]
    assert a.public_view(x,0,13)==view and ep==before
    assert a.public_view(a.generate(17,{'aggregation':'chambers'},2,1),0,13)==view
    assert len({json.dumps(a.public_view(ep,0,s)['test']) for s in range(16)})==4
