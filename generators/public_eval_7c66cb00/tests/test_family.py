from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/runtime/reviewer_support.py').is_file())
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'shared/runtime')]

@pytest.fixture(scope='module')
def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native adapter is missing'
    spec=importlib.util.spec_from_file_location('_7c66cb00_tests',path)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a

@pytest.fixture(scope='module')
def executor():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()

def test_reference_reproduces_every_official_label(executor):
    path=HOME/'reference.rkt'
    assert path.is_file(), 'general Racket reference is missing'
    source=path.read_text()
    x=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['7c66cb00']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['7c66cb00']
    pairs=x['train']+[{**p,'output':y} for p,y in zip(x['test'],gold)]
    assert len(pairs)==4
    for i,p in enumerate(pairs):assert executor(source,p['input'])==p['output'],i

def test_canonical_copy_and_resource_relocation(adapter,tmp_path):
    import shutil
    dst=tmp_path/'native';shutil.copytree(HOME/'workspace/parametric',dst)
    spec=importlib.util.spec_from_file_location('_abc_relocated',dst/'adapter.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    assert a.program(a.DEFAULT)==(HOME/'reference.rkt').read_text()
    assert a.generate(17,a.DEFAULT,2,4)==adapter.generate(17,adapter.DEFAULT,2,4)

@pytest.mark.parametrize('seed',[0,1,7,17,43])
def test_counts_prefixes_input_matching_and_largest_stress(adapter,seed):
    full=adapter.generate(seed,adapter.DEFAULT,6,4)
    other=adapter.generate(seed,{'landing_policy':'largest_joined'},6,4)
    assert [p['input'] for s in ('train','test') for p in full[s]]==[p['input'] for s in ('train','test') for p in other[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in full[s]})==10
    assert any(len(p['input'])==len(p['input'][0])==30 for p in full['test'])
    for d,q in [(2,1),(2,4),(3,2),(6,3)]:
        ep=adapter.generate(seed,adapter.DEFAULT,d,q)
        assert ep['train']==full['train'][:d] and ep['test']==full['test'][:q]
        assert adapter.public_turn(ep,0)==adapter.public_turn(adapter.generate(seed,adapter.DEFAULT,d,1),0)

def test_public_turn_is_whitelisted_deep_copy(adapter):
    ep=adapter.generate(17,adapter.DEFAULT,2,4);turn=adapter.public_turn(ep,0)
    ep['train'][0]['secret']='canary';ep['private']={'secret':'canary'};ep['program_solution']='canary'
    ep['test'][0]['output']=[[9]];ep['test'][1]['input']=[[9]]
    assert adapter.public_turn(ep,0)==turn
    turn['train'][0]['input'][0][0]=9
    assert adapter.public_turn(ep,0)!=turn

@pytest.mark.parametrize('args',[(True,2,4),(1,True,4),(1,1,4),(1,7,4),(1,2,0),(1,2,5),(1,2,True)])
def test_invalid_counts_rejected(adapter,args):
    seed,d,q=args
    with pytest.raises(ValueError):adapter.generate(seed,adapter.DEFAULT,d,q)

@pytest.mark.parametrize('setting',[{}, {'landing_policy':True},{'landing_policy':'bad'},{'landing_policy':'all_landings','extra':0}])
def test_invalid_settings_rejected(adapter,setting):
    with pytest.raises(ValueError):adapter.program(setting)

def test_declared_and_rival_racket_programs_execute(adapter,executor):
    ep=adapter.generate(17,adapter.DEFAULT,2,4)
    programs=adapter.rival_programs()|{'largest_joined':adapter.program({'landing_policy':'largest_joined'})}
    for name,program in programs.items():
        for p in ep['train']:
            assert executor(program,p['input'])==adapter.predict(p['input'],name),name
    for p in ep['test']:
        assert executor(programs['largest_joined'],p['input'])==adapter.predict(p['input'],'largest_joined')


def test_landing_creates_connections_and_rejects_original_size(adapter):
    ep=adapter.generate(17,{'landing_policy':'largest_joined'},2,4)
    for pair in ep['train']:
        info=adapter.analyze(pair['input'])
        assert len(max(info['groups'],key=len))>max(len(d['source']) for d in info['deliveries'])
        assert adapter.predict(pair['input'],'original_largest')!=pair['output']
        assert adapter.predict(pair['input'],'most_color')!=pair['output']

def test_nine_cell_shortcut_fails_on_two_demos(adapter,executor):
    ep=adapter.generate(17,{'landing_policy':'largest_joined'},2,4)
    bad=adapter.rival_programs()['exact_nine']
    assert any(executor(bad,p['input'])!=p['output'] for p in ep['train'])

def test_most_source_pieces_is_not_the_landing_winner(adapter):
    # Catch samplers in which a simple source-object count substitutes for
    # constructing connectivity after color-specific landing.
    lesson=adapter.generate(17,{'landing_policy':'largest_joined'},2,4)
    rejected=False
    for pair in lesson['train']:
        info=adapter.analyze(pair['input'])
        counts={b['color']:sum(d['band']==b for d in info['deliveries']) for b in info['bands']}
        source_color=max(counts,key=counts.get)
        winner=max(info['groups'],key=len)
        band=next(b for b in info['bands'] if b['start']<=winner[0][0]<=b['end'])
        rejected |= counts[source_color]>counts[band['color']]
    assert rejected,'most source components still predicts the winner in every lesson'


def test_ordinary_generator_does_not_cycle_every_four_draws():
    path=HOME/'generator.py'
    spec=importlib.util.spec_from_file_location('_ordinary_sample_test',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    inputs=[module.generate(seed=17,sample_index=i) for i in range(8)]
    assert len({json.dumps(g) for g in inputs})==8
    assert module.generate(seed=17,sample_index=4)==inputs[4]
