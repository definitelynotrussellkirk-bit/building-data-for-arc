"""Native contract tests; labels remain claims until protected Racket execution."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace/parametric'

@pytest.fixture(scope='module')
def adapter():
    path = BASE / 'adapter.py'
    assert path.is_file(), 'native adapter must be implemented'
    spec = importlib.util.spec_from_file_location('_58f5_native_test', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('setting',[{}, {'ink_mode':True}, {'ink_mode':0}, {'ink_mode':'other'}, {'ink_mode':'carve','extra':1}, None, []])
def test_rejects_bad_settings(adapter, setting):
    with pytest.raises(ValueError): adapter.program(setting)

@pytest.mark.parametrize('name,value',[('seed',True),('seed',-1),('seed',2**63),('seed',1.0),('seed','1'),('demos',True),('demos',1),('demos',7),('queries',0),('queries',5),('queries',False),('queries',1.0)])
def test_rejects_bad_request(adapter,name,value):
    request={'seed':17,'settings':{'ink_mode':'carve'},'demos':2,'queries':4};request[name]=value
    with pytest.raises(ValueError): adapter.generate(**request)


def test_canonical_copy_and_default_are_exact(adapter):
    original=(HOME/'reference.rkt').read_text()
    assert (BASE/'canonical.rkt').read_text()==original
    assert adapter.program({'ink_mode':'carve'})==original
    alternate=adapter.program({'ink_mode':'stamp'})
    assert alternate != original and alternate.startswith('(rule!')

@pytest.mark.parametrize('seed',[0,17,43,2**63-1])
def test_counts_prefixes_matched_inputs_and_distinctness(adapter,seed):
    full=adapter.generate(seed,{'ink_mode':'carve'},6,4)
    other=adapter.generate(seed,{'ink_mode':'stamp'},6,4)
    inputs=[p['input'] for s in ('train','test') for p in full[s]]
    assert len({json.dumps(g) for g in inputs})==10
    assert inputs==[p['input'] for s in ('train','test') for p in other[s]]
    assert all(a['output'] != b['output'] for a,b in zip(full['train'],other['train']))
    for demos,queries in ((2,1),(2,4),(3,2),(6,3)):
        short=adapter.generate(seed,{'ink_mode':'carve'},demos,queries)
        assert short['train']==full['train'][:demos]
        assert short['test']==full['test'][:queries]
        assert set(short)=={'train','test','program_solution'}
        assert all(set(p)=={'input','output'} for s in ('train','test') for p in short[s])


def test_bank_presentation_is_not_fixed_to_source_zero(adapter):
    positions=[]
    for seed in range(12):
        demos,queries=adapter.sampler.sample_banks(seed)
        source_zero=adapter.sampler.generator().generate(seed,6)
        positions.append(queries.index(source_zero))
    assert len(set(positions))>=3


def test_output_does_not_alias_input(adapter):
    lesson=adapter.generate(17,{'ink_mode':'carve'},2,4)
    pair=lesson['test'][0];before=[row[:] for row in pair['input']]
    pair['output'][0][0]=(pair['output'][0][0]+1)%10
    assert pair['input']==before


def test_native_contract_resources_are_local(adapter):
    contract=json.loads((BASE/'promotion.json').read_text())
    assert contract['parameters']=={'ink_mode':['carve','stamp']}
    assert contract['limits']=={'demos':[2,6],'queries':[1,4]}
    assert contract['qualification_demos']==2
    assert contract['resources']==['generators/public_eval_58f5dbd5/workspace/parametric/canonical.rkt']
