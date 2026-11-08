"""Regression tests: interval, priority, orientation, privacy, and native contract."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]

def adapter():
    p = HOME / 'workspace/parametric/adapter.py'
    assert p.is_file(), 'native adapter has not been implemented'
    s = importlib.util.spec_from_file_location('pulse_under_test', p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m

@pytest.mark.parametrize('split,index', [('train',i) for i in range(3)]+[('test',i) for i in range(3)])
def test_original_labels(split,index):
    a=adapter(); pair=json.loads((HOME/'tests/originals.json').read_text())[split][index]
    assert a.solve(pair['input'],'leading') == pair['output']

def test_interval_priority_and_reversal():
    a=adapter()
    g=[[0,0,0,0,0,2]+[0]*10 for _ in range(5)]
    g[2][:5]=[3,3,3,4,4]
    assert a.solve(g,'leading')[2][6:]==[4,0,4,3,4,0,4,0,4,3]
    assert a.solve(g,'trailing')[2][6:]==[0,4,3,4,0,4,0,4,3,4]
    assert a.solve([r[::-1] for r in g],'leading')==[r[::-1] for r in a.solve(g,'leading')]

@pytest.mark.parametrize('seed',[0,1,17,43,2**63-1])
def test_counts_matched_inputs_and_finite_teaching(seed):
    a=adapter(); settings=[{'pulse_phase':v} for v in ('leading','trailing')]
    banks=[]
    for st in settings:
        full=a.generate(seed,st,6,4); short=a.generate(seed,st,2,1)
        assert short['train']==full['train'][:2] and short['test']==full['test'][:1]
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in full[sp]})==10
        assert a.survivors(full['train'][:2], st)==['intended']
        assert len(full['test'][3]['input'])==len(full['test'][3]['input'][0])==30
        banks.append([p['input'] for sp in ('train','test') for p in full[sp]])
    assert banks[0]==banks[1]

@pytest.mark.parametrize('args',[(True,{'pulse_phase':'leading'},2,4),(-1,{'pulse_phase':'leading'},2,4),(2**63,{'pulse_phase':'leading'},2,4),(0,{},2,4),(0,{'pulse_phase':'leading','secret':1},2,4),(0,{'pulse_phase':'bad'},2,4),(0,{'pulse_phase':'leading'},1,4),(0,{'pulse_phase':'leading'},7,4),(0,{'pulse_phase':'leading'},True,4),(0,{'pulse_phase':'leading'},2,0),(0,{'pulse_phase':'leading'},2,5)])
def test_invalid_requests_fail(args):
    with pytest.raises(ValueError):adapter().generate(*args)

@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1,2],[3]],[[10]],[[0]*31]])
def test_invalid_grids_fail(g):
    with pytest.raises(ValueError):adapter().solve(g,'leading')

def test_public_projection_and_full_bank_shuffle():
    a=adapter(); st={'pulse_phase':'leading'}; e=a.generate(17,st,2,4)
    visible=a.public_view(e,0); mutated=copy.deepcopy(e)
    mutated.update(settings={'secret':42},program_solution='SECRET',seed=88)
    mutated['test'][0]['output']=[[9]]; mutated['test'][1:]=[{'input':[[9]],'output':[[8]]}]
    assert a.public_view(mutated,0)==visible
    assert set(visible)=={'train','test'} and len(visible['test'])==1
    assert set(visible['test'][0])=={'input'}
    for p in range(8):
        assert a.public_turns(17,st,2,p,1)==a.public_turns(17,st,2,p,4)[:1]
    assert len({json.dumps(a.public_turns(17,st,2,p,1)[0]['test']) for p in range(8)})>1

def test_exact_reference_and_production_sampler():
    a=adapter(); assert a.program({'pulse_phase':'leading'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    p=HOME/'generator.py';s=importlib.util.spec_from_file_location('pulse_generator',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert m.RULE_TASK_ID=='ee_1ae2feb7'
    for i in range(8):
        g=m.generate(13,i,difficulty='hard'); assert m.self_check(g)==[]

def test_default_presentation_varies_across_source_seeds():
    a=adapter();seen=set();st={'pulse_phase':'leading'}
    for seed in range(8):
        bank=a.generate(seed,st,2,4)['test']
        current=a.public_turns(seed,st,2,0,1)[0]['test'][0]['input']
        seen.add(next(i for i,p in enumerate(bank) if p['input']==current))
    assert len(seen)>1, 'default presentation always starts at the same source ordinal'
