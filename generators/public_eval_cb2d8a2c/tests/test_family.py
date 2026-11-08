from pathlib import Path
import copy
import importlib.util
import json
import shutil
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

@pytest.fixture(scope='module')
def a():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(), 'Implement the native count-controlled detour family'
    spec=importlib.util.spec_from_file_location('cb2_adapter_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def originals():
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['cb2d8a2c']
    ys=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['cb2d8a2c']
    return d['train']+[{'input':p['input'],'output':y} for p,y in zip(d['test'],ys)]

def fixture():
    g=[[8]*13 for _ in range(11)];g[0][5]=3
    for c in range(7):g[4][c]=1 if c in (0,2) else 2
    return g

def expected(scope):
    # Two blue marks mean distance THREE from both the wall's row and its free tip.
    g=fixture()
    for c in range(7):g[4][c]=2
    for c in range(5,10):g[1][c]=3
    if scope=='full_route':
        for r in range(1,11):g[r][9]=3
    return g

@pytest.mark.parametrize('scope',['full_route','longest_bypass'])
def test_hand_computed_clearance_and_scope(a,scope):
    assert a.solve(fixture(),scope)==expected(scope)

def test_official_python_labels(a):
    for p in originals():assert a.solve(p['input'],'full_route')==p['output']

def test_official_racket_labels(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    run,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for p in originals():assert run(a.program({'trace_scope':'full_route'}),p['input'])==p['output']
    finally:bridge.close()

@pytest.mark.parametrize('turns',range(4))
@pytest.mark.parametrize('flip',[False,True])
def test_dihedral_equivariance(a,turns,flip):
    def transform(g):
        x=[row[::-1] for row in g] if flip else copy.deepcopy(g)
        for _ in range(turns):x=[list(row) for row in zip(*x[::-1])]
        return x
    for scope in ('full_route','longest_bypass'):
        assert a.solve(transform(fixture()),scope)==transform(expected(scope))

@pytest.mark.parametrize('seed',[0,7,17,43])
def test_counts_prefixes_and_matched_inputs(a,seed):
    full=a.generate(seed,{'trace_scope':'full_route'},6,4)
    for d in range(2,7):
        for q in range(1,5):
            x=a.generate(seed,{'trace_scope':'full_route'},d,q)
            y=a.generate(seed,{'trace_scope':'longest_bypass'},d,q)
            assert x['train']==full['train'][:d] and x['test']==full['test'][:q]
            assert [p['input'] for s in ('train','test') for p in x[s]]==[p['input'] for s in ('train','test') for p in y[s]]
    ins=[json.dumps(p['input']) for s in ('train','test') for p in full[s]]
    assert len(set(ins))==10
    for p in full['train']+full['test']:
        f=a.inspect(p['input'])
        assert sum(leg['length']==max(t['length'] for t in f['legs']) for leg in f['legs'])==1
        for r,row in enumerate(p['input']):
            for c,v in enumerate(row):
                if v in (1,2):assert p['output'][r][c]==2

def test_stress_covers_grid_and_trace_history(a):
    e=a.generate(17,{'trace_scope':'longest_bypass'},2,4)
    p=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    f=a.inspect(p['input']);g=p['input'];bg=f['background']
    assert len(f['walls'])==5
    assert sum(v!=bg for row in g for v in row)>90
    assert all(any(g[r][c]!=bg for r,c in edge) for edge in [
        [(0,c) for c in range(30)],[(29,c) for c in range(30)],[(r,0) for r in range(30)],[(r,29) for r in range(30)]])
    assert all(any(g[r][c]!=bg for r in range(i*15,(i+1)*15) for c in range(j*15,(j+1)*15)) for i in (0,1) for j in (0,1))
    assert f['winner']!=max(range(len(f['walls'])),key=lambda i:f['walls'][i]['markers'])

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,False),(2.0,4)])
def test_bad_counts(a,d,q):
    with pytest.raises(ValueError):a.generate(0,{'trace_scope':'full_route'},d,q)

@pytest.mark.parametrize('s',[{}, {'trace_scope':'wrong'},{'trace_scope':'full_route','seed':0}])
def test_bad_settings(a,s):
    with pytest.raises(ValueError):a.generate(0,s,2,4)

def test_public_turn_copies_and_masks(a):
    e=a.generate(17,{'trace_scope':'longest_bypass'},2,4);v=a.public_turn(e,0)
    assert v=={'train':e['train'],'test':[{'input':e['test'][0]['input']}]}
    x=copy.deepcopy(e);x['private']={'answer':[[1]]};x['settings']={};x['program_solution']='secret';x['test'][0]['output']=[[9]];x['test']=x['test'][:1]
    assert a.public_turn(x,0)==v
    v['train'][0]['input'][0][0]=99
    assert e['train'][0]['input'][0][0]!=99
    for i in (-1,4,True,0.0):
        with pytest.raises(ValueError):a.public_turn(e,i)

def test_query_presentation_is_not_fixed(a):
    indices={a.generate(s,{'trace_scope':'full_route'},2,1)['private']['query_source_indices'][0] for s in range(20)}
    assert len(indices)>1

def test_native_folder_is_self_contained(a,tmp_path):
    target=tmp_path/'unrelated'/'parametric'
    shutil.copytree(HOME/'workspace/parametric',target,ignore=shutil.ignore_patterns('__pycache__','evidence'))
    spec=importlib.util.spec_from_file_location('relocated_cb2',target/'adapter.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    for opt in ('full_route','longest_bypass'):
        assert m.generate(17,{'trace_scope':opt},2,4)==a.generate(17,{'trace_scope':opt},2,4)
    assert a.program({'trace_scope':'full_route'})==(HOME/'reference.rkt').read_text()

def test_generator_registered_rule_identity(a):
    from arcpuzzles.review_public_creation import validate_reference_id
    validate_reference_id(HOME/'generator.py','cb2d8a2c')
    spec=importlib.util.spec_from_file_location('generator_cb2',HOME/'generator.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert m.generate(1,0)==m.generate(1,0)
    with pytest.raises(ValueError):m.generate(1,0,unknown=True)

@pytest.mark.parametrize('scope',['full_route','longest_bypass'])
def test_short_lessons_reject_rivals(a,scope):
    for seed in range(20):
        e=a.generate(seed,{'trace_scope':scope},2,4)
        for name in a.rival_programs({'trace_scope':scope}):
            assert any(a.rival_predict(p['input'],scope,name)!=p['output'] for p in e['train']), (seed,name)

def test_protected_generated_and_rival_parity(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    run,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for scope in ('full_route','longest_bypass'):
            e=a.generate(17,{'trace_scope':scope},2,4)
            for p in e['train']+e['test']:assert run(e['program_solution'],p['input'])==p['output']
            for name,program in a.rival_programs({'trace_scope':scope}).items():
                for p in e['train']:assert run(program,p['input'])==a.rival_predict(p['input'],scope,name),name
    finally:bridge.close()


def test_stress_retains_original_four_marker_difficulty(a):
    # The supplied parent includes a four-marker barrier. A three-marker cap
    # would simplify that part of its reasoning away in the generated family.
    e=a.generate(17,{'trace_scope':'full_route'},2,4)
    p=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    f=a.inspect(p['input'])
    assert max(w['markers'] for w in f['walls'])>=4
    assert any(w['clearance']==5 for w in f['walls'])


def test_racket_respects_all_source_orientations(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    run,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for flip in (False,True):
            g=[row[::-1] for row in fixture()] if flip else fixture()
            y=[row[::-1] for row in expected('full_route')] if flip else expected('full_route')
            for k in range(4):
                assert run(a.program({'trace_scope':'full_route'}),g)==y
                g=[list(row) for row in zip(*g[::-1])];y=[list(row) for row in zip(*y[::-1])]
    finally:bridge.close()
