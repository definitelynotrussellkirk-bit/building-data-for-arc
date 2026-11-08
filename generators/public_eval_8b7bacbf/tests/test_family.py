from __future__ import annotations
import copy, importlib.util, json, sys
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

@pytest.fixture(scope='module')
def family(): return load(HOME/'workspace/parametric/family.py','fec_family_test')
@pytest.fixture(scope='module')
def adapter(): return load(HOME/'workspace/parametric/adapter.py','fec_adapter_test')

def official_pairs():
    raw=ROOT/'shared/data/raw'
    ch=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['8b7bacbf']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['8b7bacbf']
    return ch['train']+[{'input':p['input'],'output':o} for p,o in zip(ch['test'],gold,strict=True)]

def test_reference_is_canonical_and_modes_are_distinct(adapter):
    ref=(HOME/'reference.rkt').read_text(); can=(HOME/'workspace/parametric/canonical.rkt').read_text()
    assert ref==can==adapter.program({'indicator_policy':'clean'})
    assert adapter.program({'indicator_policy':'all'}) != can

@pytest.mark.parametrize('mode',['clean','all'])
@pytest.mark.parametrize('demos',[2,6])
@pytest.mark.parametrize('queries',[1,4])
def test_episode_contract(family,adapter,mode,demos,queries):
    e=adapter.generate(17,{'indicator_policy':mode},demos,queries)
    assert e==adapter.generate(17,{'indicator_policy':mode},demos,queries)
    assert len(e['train'])==demos and len(e['test'])==queries
    inputs=[p['input'] for s in ('train','test') for p in e[s]]
    assert len({json.dumps(x,separators=(',',':')) for x in inputs})==len(inputs)
    for p in e['train']+e['test']: assert family.solve(p['input'],mode)==p['output']

def test_settings_change_labels_on_same_inputs(adapter):
    a=adapter.generate(43,{'indicator_policy':'clean'},2,4); b=adapter.generate(43,{'indicator_policy':'all'},2,4)
    assert [p['input'] for s in ('train','test') for p in a[s]] == [p['input'] for s in ('train','test') for p in b[s]]
    assert any(x['output']!=y['output'] for x,y in zip(a['train'],b['train']))

def test_public_view_hides_future_answers(adapter):
    e=adapter.generate(17,{'indicator_policy':'clean'},3,4); before=copy.deepcopy(e); v=adapter.public_view(e,2)
    assert len(v['train'])==3 and len(v['test'])==1 and set(v['test'][0])=={'input'}
    assert v['test'][0]['input']==e['test'][2]['input'] and e==before

def test_protected_racket_matches_official_and_generated(adapter):
    from arcpuzzles.parametric_worker import _real_evaluator,_local_imports
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        assert identity['protected'] and identity['backend']=='racket'
        try:
            p=adapter.program({'indicator_policy':'clean'})
            for pair in official_pairs(): assert apply(p,pair['input'])==pair['output']
            for mode in ('clean','all'):
                e=adapter.generate(17,{'indicator_policy':mode},2,4)
                for pair in e['train']+e['test']: assert apply(e['program_solution'],pair['input'])==pair['output']
        finally: bridge.close()
