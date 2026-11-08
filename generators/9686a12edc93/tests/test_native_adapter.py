"""Native contract, matched settings, and independent count controls."""
import importlib.util
import json
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]/'workspace/parametric'
spec=importlib.util.spec_from_file_location('endpoint_native_adapter_test',HOME/'adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


def test_contract_and_exact_canonical_default():
    contract=json.loads((HOME/'promotion.json').read_text())
    assert contract['parameters']=={'clearance_stage':['input','painted']}
    assert contract['default']=={'clearance_stage':'input'}
    assert contract['qualification_demos']==3
    assert contract['limits']=={'demos':[3,6],'queries':[1,4]}
    assert a.program(contract['default']).encode()==(HOME/'canonical.rkt').read_bytes()
    for name in contract['resources']:
        assert (HOME.parents[3]/name).is_file()


@pytest.mark.parametrize('mode',['input','painted'])
@pytest.mark.parametrize('demos,queries',[(3,1),(3,4),(6,1),(6,4)])
def test_independent_counts_and_exact_episode_shape(mode,demos,queries):
    episode=a.generate(17,{'clearance_stage':mode},demos,queries)
    assert set(episode)=={'train','test','program_solution'}
    assert len(episode['train'])==demos and len(episode['test'])==queries
    for pair in episode['train']+episode['test']:
        assert set(pair)=={'input','output'}
        assert len(pair['output'])==len(pair['input'])
    assert episode['program_solution']==a.program({'clearance_stage':mode})


def test_settings_share_inputs_but_are_demonstrably_distinct():
    episodes=[a.generate(0,{'clearance_stage':mode},3,4) for mode in ('input','painted')]
    for split in ('train','test'):
        assert [p['input'] for p in episodes[0][split]]==[p['input'] for p in episodes[1][split]]
    assert any(x['output']!=y['output'] for x,y in zip(episodes[0]['train'],episodes[1]['train']))


def test_prefixes_and_fresh_results():
    whole=a.generate(0,{'clearance_stage':'painted'},6,4)
    small=a.generate(0,{'clearance_stage':'painted'},3,1)
    assert small['train']==whole['train'][:3]
    assert small['test']==whole['test'][:1]
    small['train'][0]['input'][0][0]=99
    assert a.generate(0,{'clearance_stage':'painted'},6,4)==whole


@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_default_setting_is_once_per_episode(seed):
    assert a.generate(seed)==a.generate(seed,{'clearance_stage':['input','painted'][seed%2]})


@pytest.mark.parametrize('call',[{'seed':True},{'seed':-1},{'seed':2**63},
    {'seed':0,'demos':2},{'seed':0,'demos':7},{'seed':0,'queries':0},
    {'seed':0,'queries':5},{'seed':0,'settings':{}},
    {'seed':0,'settings':{'clearance_stage':'input','leak':1}}])
def test_native_entry_rejects_invalid_controls(call):
    with pytest.raises((TypeError,ValueError)):a.generate(**call)
