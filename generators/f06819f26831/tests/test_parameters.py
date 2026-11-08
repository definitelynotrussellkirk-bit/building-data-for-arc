"""Independent literal-template completion and gain-selection regressions."""
from pathlib import Path
import copy
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1]
P=HOME/'workspace/parametric'

@pytest.fixture(scope='module')
def mod():
    spec=importlib.util.spec_from_file_location('gain_adapter_test',P/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def fixture(dense=False):
    g=[[0]*22 for _ in range(18)]
    small=[[1,1,1],[1,2,1],[1,1,1]]
    big=[[3,3,3,3],[3,4,4,3],[3,3,3,3],[3,3,3,3]]
    for template,rr,cc in [(small,0,0),(big,0,7)]:
        for r,row in enumerate(template):
            for c,v in enumerate(row):g[rr+r][cc+c]=v
    g[9][1]=2
    for r,row in enumerate(big):
        for c,v in enumerate(row):
            if (dense and v==3) or (not dense and v==4):g[8+r][8+c]=v
    expected=copy.deepcopy(g)
    for template,rr,cc in [(small,8,0),(big,8,8)]:
        for r,row in enumerate(template):
            for c,v in enumerate(row):expected[rr+r][cc+c]=v
    return g,expected

def test_native_family_generates_complete_lesson():
    assert (P/'adapter.py').is_file(), 'native completion family is missing'
    spec=importlib.util.spec_from_file_location('gain_smoke',P/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    e=module.generate(0,{'completion_policy':'largest_gain'},2,4)
    assert len(e['train'])==2 and len(e['test'])==4

@pytest.mark.parametrize('dense',[False,True])
def test_completion_gain_not_template_size_or_partial_size(mod,dense):
    g,expected=fixture(dense);before=copy.deepcopy(g)
    assert mod.predict(g,'all_copies')==expected
    rr,cc,n=(8,0,3) if dense else (8,8,4)
    for r in range(rr,rr+n):
        for c in range(cc,cc+n):expected[r][c]=8
    assert mod.predict(g,'largest_gain')==expected
    assert g==before

def test_unmatched_monochrome_cells_are_not_invented_templates(mod):
    g=[[0]*10 for _ in range(8)];g[2][2]=g[2][3]=6
    assert mod.predict(g,'all_copies')==g and mod.predict(g,'largest_gain')==g

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(True,4),(3,0),(3,5),(3,True)])
def test_invalid_counts_rejected(mod,d,q):
    with pytest.raises((TypeError,ValueError)):mod.generate(0,{'completion_policy':'largest_gain'},d,q)

@pytest.mark.parametrize('settings',[{}, {'completion_policy':'bad'}, {'completion_policy':'all_copies','extra':0}])
def test_undeclared_settings_rejected(mod,settings):
    with pytest.raises((TypeError,ValueError)):mod.program(settings)

def test_racket_exact_canonical_and_literal_cases(mod):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    root=find_root(HOME)
    exact={v['program_solution'] for v in Catalog(root).get('f06819f26831')['variants']}
    assert mod.program({'completion_policy':'all_copies'}) in exact
    apply,identity,bridge=_real_evaluator(root if (root/'RUNTIME_MANIFEST.json').is_file() else root/'shared/runtime')
    try:
        assert identity['protected'] is True
        for mode in ('all_copies','largest_gain'):
            for dense in (False,True):
                g,_=fixture(dense)
                assert apply(mod.program({'completion_policy':mode}),g)==mod.predict(g,mode)
            e=mod.generate(17,{'completion_policy':mode},2,4)
            for p in e['train']+e['test']:assert apply(e['program_solution'],p['input'])==p['output']
    finally:bridge.close()

def test_matched_prefixes_unique_inputs_and_large_query(mod):
    positions=set()
    for seed in range(5):
        a=mod.generate(seed,{'completion_policy':'all_copies'},6,4)
        b=mod.generate(seed,{'completion_policy':'largest_gain'},6,4)
        assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
        assert len({json.dumps(p['input']) for p in b['train']+b['test']})==10
        short=mod.generate(seed,{'completion_policy':'largest_gain'},2,1)
        assert short['train']==b['train'][:2] and short['test']==b['test'][:1]
        assert all(x['output']!=y['output'] for x,y in zip(a['train'][:2],b['train'][:2]))
        large=[(i,p) for i,p in enumerate(b['test']) if len(p['input'])==len(p['input'][0])==30]
        assert len(large)==1;positions.add(large[0][0]);g=large[0][1]['input']
        pts=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
        assert len(pts)>150
        assert (min(r for r,c in pts),max(r for r,c in pts),min(c for r,c in pts),max(c for r,c in pts))==(0,29,0,29)
        assert {(r//15,c//15) for r,c in pts}=={(0,0),(0,1),(1,0),(1,1)}
        for i in range(4):
            v=mod.public_view(b,i)
            assert v=={'train':b['train'],'test':[{'input':b['test'][i]['input']}]}
            noisy=copy.deepcopy(b);noisy['program_solution']='private';noisy['test'][i]['output']=[[9]]
            assert mod.public_view(noisy,i)==v
    assert len(positions)>1

def test_public_index_validation_and_copy(mod):
    e=mod.generate(0,{'completion_policy':'largest_gain'},2,4);before=copy.deepcopy(e)
    for i in (-1,4,True):
        with pytest.raises((ValueError,IndexError)):mod.public_view(e,i)
    mod.public_view(e,0)['train'][0]['input'][0][0]=9
    assert e==before

def test_audit_sweep_real_family(mod):
    path=P/'audit.py';assert path.is_file(), 'bounded audit tool missing'
    spec=importlib.util.spec_from_file_location('gain_audit_test',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    result=audit.sweep(1)
    assert result['requests']==40 and result['pairs']==260
    assert result['matched_inputs']==20 and result['public_turns']==100


def test_all_eight_poses_preserve_literal_labels(mod):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    def pose(g,k):
        out=copy.deepcopy(g)
        for _ in range(k%4):out=[list(row) for row in zip(*out[::-1])]
        if k//4:out=[row[::-1] for row in out]
        return out
    apply,identity,bridge=_real_evaluator(find_root(HOME) if (find_root(HOME)/'RUNTIME_MANIFEST.json').is_file() else find_root(HOME)/'shared/runtime')
    try:
        for dense in (False,True):
            g,expected=fixture(dense)
            rr,cc,n=(8,0,3) if dense else (8,8,4)
            for r in range(rr,rr+n):
                for c in range(cc,cc+n):expected[r][c]=8
            for k in range(8):
                actual=pose(g,k);want=pose(expected,k)
                assert mod.predict(actual,'largest_gain')==want
                assert apply(mod.program({'completion_policy':'largest_gain'}),actual)==want
    finally:bridge.close()


def test_cached_episode_cannot_be_poisoned_by_caller(mod):
    settings={'completion_policy':'largest_gain'}
    original=mod.generate(5,settings,2,4)
    changed=mod.generate(5,settings,6,4)
    changed['train'][0]['input'][0][0]=8
    changed['train'][0]['output'][0][0]=9
    changed['test'].clear()
    assert mod.generate(5,settings,2,4)==original


def test_tied_gains_do_not_arbitrarily_recolor(mod):
    g,_=fixture(False)
    # Remove the large sparse partial, then add a second small-template center.
    g[9][9]=g[9][10]=0;g[14][6]=2
    stage=mod.predict(g,'all_copies')
    assert mod.predict(g,'largest_gain')==stage
