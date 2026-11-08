import copy
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

HOME=Path(__file__).resolve().parents[1]

def load(path,name='stencil_test_adapter'):
    assert path.is_file(), f'Missing implementation: {path.name}'
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def adapter():return load(HOME/'workspace/parametric/adapter.py')

def fixture():
    g=[[0]*7 for _ in range(7)]
    for r,c in [(0,0),(0,1),(1,1),(2,2)]:g[r][c]=2
    g[4][4:6]=[3,4];g[5][4:6]=[4,3]
    return g

def test_literal_kronecker_product_and_region_selection():
    a=adapter();g=fixture()
    expected=[[3,4,3,4,0,0],[4,3,4,3,0,0],[0,0,3,4,0,0],[0,0,4,3,0,0],
              [0,0,0,0,3,4],[0,0,0,0,4,3]]
    assert a.G.solve(g,'all')==expected
    expected[-2:]=[[0]*6,[0]*6]
    assert a.G.solve(g,'largest')==expected
    assert g==fixture()

def test_original_labels_python_and_exact_default_source():
    a=adapter();root=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())
    data=json.loads((root/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['bf45cf4b']
    gold=json.loads((root/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['bf45cf4b']
    for p in data['train']+[dict(x,output=y) for x,y in zip(data['test'],gold)]:
        assert a.G.solve(p['input'],'all')==p['output']
    assert a.program({'mask_rule':'all'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,17,43,127])
def test_deterministic_prefixes_matched_settings_and_finite_teaching(seed):
    a=adapter();one=a.generate(seed,{'mask_rule':'all'},6,4)
    two=a.generate(seed,{'mask_rule':'largest'},6,4)
    assert [p['input'] for s in ('train','test') for p in one[s]]==[p['input'] for s in ('train','test') for p in two[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in one[s]})==10
    for value,ep in [('all',one),('largest',two)]:
        for d in range(2,7):
            sub=a.generate(seed,{'mask_rule':value},d,4)
            assert sub['train']==ep['train'][:d] and sub['test']==ep['test']
        for q in range(1,5):
            sub=a.generate(seed,{'mask_rule':value},2,q)
            assert sub['test']==ep['test'][:q] and sub['train']==ep['train'][:2]
        for rival in a.G.RIVALS:
            assert any(a.G.solve(p['input'],value,rival=rival)!=p['output'] for p in ep['train'][:2]),rival
        stress=ep['test'][-1]
        assert (len(stress['input']),len(stress['input'][0]))==(30,30)
        assert (len(stress['output']),len(stress['output'][0]))==(30,30)
        assert all(a.G.self_check(p['input'])==[] for s in ('train','test') for p in ep[s])

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'demos':1},{'demos':7},{'queries':0},{'queries':5},{'queries':True},{'settings':{}},{'settings':{'mask_rule':'no'}},{'settings':{'mask_rule':'all','extra':1}}])
def test_invalid_requests_fail_closed(kwargs):
    a=adapter();args=dict(seed=0,settings={'mask_rule':'all'},demos=2,queries=4);args.update(kwargs)
    with pytest.raises((ValueError,TypeError)):a.generate(**args)

def test_public_first_turn_independent_and_copy_isolated():
    a=adapter();seen=set()
    for seed in range(8):
        b=a.present(seed,{'mask_rule':'largest'},2,4,presentation_seed=12)
        c=a.present(seed,{'mask_rule':'largest'},2,1,presentation_seed=12)
        assert b['public'][:1]==c['public']
        seen.add(b['private']['source_indices'][0])
        for v in b['public']:
            assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
        b['public'][0]['train'][0]['input'][0][0]=99
        assert a.present(seed,{'mask_rule':'largest'},2,1,presentation_seed=12)==c
    assert len(seen)>1

def test_source_closure_relocates_and_uses_no_sibling(tmp_path):
    src=HOME/'workspace/parametric';contract=json.loads((src/'promotion.json').read_text())
    for name in ['adapter.py','engine.py','canonical.rkt']:
        shutil.copyfile(src/name,tmp_path/name)
    a=load(tmp_path/'adapter.py','relocated_stencil')
    assert a.generate(17,{'mask_rule':'largest'},2,4)==adapter().generate(17,{'mask_rule':'largest'},2,4)

@pytest.mark.parametrize('g',[[],[[True]],[[0,1],[0]],[[10]],[[0]*31],[[0]]])
def test_bad_or_out_of_grammar_grids_rejected(g):
    assert adapter().G.self_check(g)
    with pytest.raises(ValueError):adapter().G.solve(g,'all')

def test_every_declared_rival_executes_in_protected_racket():
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    root=next(p for p in HOME.parents if (p/'shared/runtime').is_dir())
    a=adapter();apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    try:
        assert identity['protected'] is True
        for setting in ('all','largest'):
            for rival in a.G.RIVALS:
                actual=_grid(apply(a.rival_program({'mask_rule':setting},rival),fixture()))
                assert actual==a.G.solve(fixture(),setting,rival)
    finally:bridge.close()

def test_ambiguous_background_is_rejected_instead_of_runtime_tie_break():
    a=adapter();g=[[1,1,0,0,2 if r%2 else 3] for r in range(5)]
    with pytest.raises(ValueError,match='unique modal background'):a.G.parse(g)
