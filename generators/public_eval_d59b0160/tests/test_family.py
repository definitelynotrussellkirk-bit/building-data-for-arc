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
    spec=importlib.util.spec_from_file_location('_d59b0160_tests',path)
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
    pairs=json.loads((HOME/'tests/original-pairs.json').read_text())
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
    other=adapter.generate(seed,{'erase_policy':'area_relay'},6,4)
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

@pytest.mark.parametrize('setting',[{}, {'erase_policy':True},{'erase_policy':'bad'},{'erase_policy':'all_matches','extra':0}])
def test_invalid_settings_rejected(adapter,setting):
    with pytest.raises(ValueError):adapter.program(setting)

def test_declared_and_rival_racket_programs_execute(adapter,executor):
    ep=adapter.generate(17,adapter.DEFAULT,2,4)
    programs=adapter.rival_programs()|{'area_relay':adapter.program({'erase_policy':'area_relay'})}
    for name,program in programs.items():
        for p in ep['train']:
            assert executor(program,p['input'])==adapter.predict(p['input'],name),name
    for p in ep['test']:
        assert executor(programs['area_relay'],p['input'])==adapter.predict(p['input'],'area_relay')



def test_python_reference_claims_match_independent_originals(adapter):
    pairs=json.loads((HOME/'tests/original-pairs.json').read_text())
    for pair in pairs: assert adapter.predict(pair['input'])==pair['output']


def test_key_subset_not_exact_palette_or_any_overlap(adapter):
    for seed in (0,7,17,43):
        g=adapter.generate(seed,adapter.DEFAULT,2,4)['train'][0]['input']
        info=adapter.analyze(g);keys=set(info['key_colors'])
        assert any(set(p['colors'])>keys for p in info['panels'] if p['matched'])
        assert any(set(p['colors'])&keys and not p['matched'] for p in info['panels'])
        assert adapter.predict(g,'exact_colors')!=adapter.predict(g)
        assert adapter.predict(g,'any_color')!=adapter.predict(g)

def test_area_receiver_uses_largest_matched_not_largest_original(adapter):
    for seed in (0,1,7,17,43):
        ep=adapter.generate(seed,{'erase_policy':'area_relay'},2,4)
        for pair in ep['train']+ep['test']:
            info=adapter.analyze(pair['input'])
            selected=[p for p in info['panels'] if p['matched']]
            winner=max(selected,key=lambda p:len(p['cells']))
            area=len(winner['cells'])
            receivers=[p for p in info['panels'] if not p['matched'] and len(p['cells'])==area]
            assert len(receivers)==1
            assert max(len(p['cells']) for p in info['panels'])>area
            # Equal occupied area does not mean the same rectangle dimensions.
            assert sorted(winner['shape'])!=sorted(receivers[0]['shape'])
            before=adapter.predict(pair['input'])
            changed={(r,c) for r,row in enumerate(before) for c,v in enumerate(row) if pair['output'][r][c]!=v}
            assert changed==set(receivers[0]['cells'])

def test_two_demos_reject_declared_rivals(adapter):
    for seed in range(20):
        for value in adapter.PARAMETERS['erase_policy']:
            ep=adapter.generate(seed,{'erase_policy':value},2,4)
            names=list(adapter.rival_programs())+['area_relay']
            survivors=[name for name in names if all(adapter.predict(p['input'],name)==p['output'] for p in ep['train'])]
            assert survivors==[value],(seed,value,survivors)

def test_base_api_is_repeatable_and_does_not_cycle():
    path=HOME/'generator.py';assert path.is_file()
    spec=importlib.util.spec_from_file_location('_d59b0160_base_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    inputs=[m.generate(17,i) for i in range(8)]
    assert len({json.dumps(g) for g in inputs})==8
    assert m.generate(17,4)==inputs[4]
    assert m.self_check(inputs[4])==[]


def test_second_largest_survivor_shortcut_fails_on_demos(adapter):
    """Catch an area schedule that makes key-conditioned selection dispensable."""
    lesson=adapter.generate(17,{'erase_policy':'area_relay'},2,4)
    rejected=False
    for pair in lesson['train']:
        info=adapter.analyze(pair['input'])
        survivors=[p for p in info['panels'] if not p['matched']]
        second=sorted(survivors,key=lambda p:-len(p['cells']))[1]
        wrong=adapter.predict(pair['input'])
        for r,c in second['cells']:wrong[r][c]=7
        rejected |= wrong!=pair['output']
    assert rejected, 'second-largest-survivor shortcut still fits both demos'


def test_relay_rank_and_repeated_area_are_not_fixed(adapter):
    lesson=adapter.generate(17,{'erase_policy':'area_relay'},2,4)
    ranks=set();repeated_distractor=False
    for pair in lesson['train']+lesson['test']:
        info=adapter.analyze(pair['input']);panels=info['panels']
        area=max(len(p['cells']) for p in panels if p['matched'])
        ranks.add(1+sum(not p['matched'] and len(p['cells'])>area for p in panels))
        sizes=[len(p['cells']) for p in panels]
        repeated_distractor |= any(s>area and sizes.count(s)>1 for s in sizes)
    assert len(ranks)>=3
    assert repeated_distractor


def test_largest_match_is_not_always_the_richest_palette(adapter):
    lesson=adapter.generate(17,{'erase_policy':'area_relay'},2,4)
    assert any(max((p for p in adapter.analyze(pair['input'])['panels'] if p['matched']),
                   key=lambda p:len(p['colors']))['cells']
               != max((p for p in adapter.analyze(pair['input'])['panels'] if p['matched']),
                      key=lambda p:len(p['cells']))['cells'] for pair in lesson['train'])
