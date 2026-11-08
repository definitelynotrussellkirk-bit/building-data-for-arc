from pathlib import Path
import importlib.util
import json
from copy import deepcopy
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

@pytest.fixture(scope='module')
def a():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'Native ray adapter must be implemented'
    s=importlib.util.spec_from_file_location('test_public_142',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def originals():
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['142ca369']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['142ca369']
    return d['train']+[dict(input=p['input'],output=o) for p,o in zip(d['test'],gold)]

def test_official_python_labels(a):
    for i,p in enumerate(originals()):assert a.solve(p['input'],'all_legs')==p['output'],i

def test_official_racket_labels(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    run,_,b=_real_evaluator(ROOT/'shared/runtime')
    try:
        for i,p in enumerate(originals()):assert run(a.program({'trace_scope':'all_legs'}),p['input'])==p['output'],i
    finally:b.close()

def test_literal_singleton_reflection_color_changes_at_bounce(a):
    g=[[0]*9 for _ in range(9)]
    for r,c in ((0,1),(1,0),(1,1)):g[r][c]=2
    g[4][5]=3  # singleton immediately right of bounce (4,4)
    y=deepcopy(g)
    for r,c in ((2,2),(3,3)):y[r][c]=2
    for r,c in ((4,4),(5,3),(6,2),(7,1),(8,0)):y[r][c]=3
    z=deepcopy(g)
    for r,c in ((4,4),(5,3),(6,2),(7,1),(8,0)):z[r][c]=3
    assert a.solve(g,'all_legs')==y
    assert a.solve(g,'longest_leg')==z

@pytest.mark.parametrize('seed',[0,7,17,43])
def test_counts_prefixes_and_geometry(a,seed):
    full=a.generate(seed,{'trace_scope':'all_legs'},6,4)
    for d in range(2,7):
        for q in range(1,5):
            x=a.generate(seed,{'trace_scope':'all_legs'},d,q)
            z=a.generate(seed,{'trace_scope':'longest_leg'},d,q)
            assert x['train']==full['train'][:d] and x['test']==full['test'][:q]
            assert [p['input'] for s in ('train','test') for p in x[s]]==[p['input'] for s in ('train','test') for p in z[s]]
            assert len({json.dumps(p['input']) for s in ('train','test') for p in x[s]})==d+q
            assert all(p['output']!=a.solve(p['input'],'longest_leg') for p in x['train'])
    assert any(len(p['input'])==len(p['input'][0])==30 for p in full['test'])

def test_all_d4_covariance(a):
    # Direction and turn geometry must not privilege the generated NW->SE frame.
    for p in a.generate(0,{'trace_scope':'all_legs'},2,4)['train']:
        for t in range(8):
            for mode in ('all_legs','longest_leg'):
                assert a.solve(a.transform(p['input'],t),mode)==a.transform(a.solve(p['input'],mode),t)

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(3,False),(2.0,4)])
def test_invalid_counts(a,d,q):
    with pytest.raises(ValueError):a.generate(0,{'trace_scope':'all_legs'},d,q)

@pytest.mark.parametrize('s',[{}, {'trace_scope':'bad'},{'trace_scope':'all_legs','secret':1}])
def test_invalid_setting(a,s):
    with pytest.raises(ValueError):a.generate(0,s,2,4)

def test_public_turn_and_query_shuffle(a):
    e=a.generate(17,{'trace_scope':'longest_leg'},2,4);v=a.public_turn(e,0)
    e2=deepcopy(e);e2['test']=e2['test'][:1];e2['test'][0]['output']=[[9]];e2['settings']={};e2['private']={};e2['program_solution']='X'
    assert a.public_turn(e2,0)==v
    assert set(v)=={'train','test'} and set(v['test'][0])=={'input'}
    assert len({a.generate(s,{'trace_scope':'all_legs'},2,1)['private']['query_source_indices'][0] for s in range(12)})>1
    for idx in (-1,4,True,1.0):
        with pytest.raises(ValueError):a.public_turn(e,idx)

def test_generated_racket_and_default(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    assert a.program({'trace_scope':'all_legs'})==(HOME/'reference.rkt').read_text()
    run,_,b=_real_evaluator(ROOT/'shared/runtime')
    try:
        for mode in ('all_legs','longest_leg'):
            e=a.generate(17,{'trace_scope':mode},2,4)
            for p in e['train']+e['test']:assert run(e['program_solution'],p['input'])==p['output']
    finally:b.close()

def test_generator(a):
    s=importlib.util.spec_from_file_location('gen142',HOME/'generator.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    g=m.generate(5,4)
    assert isinstance(g,list) and 1<=len(g)<=30
    with pytest.raises(ValueError):m.generate(5,4,unknown=2)

def test_earliest_leg_wins_length_tie(a):
    g=[[0]*9 for _ in range(4)]
    for r,c in ((0,1),(1,0),(1,1)):g[r][c]=2
    g[3][4]=3
    expected=deepcopy(g);expected[2][2]=2
    assert a.solve(g,'longest_leg')==expected
    from arcpuzzles.parametric_worker import _real_evaluator
    run,_,b=_real_evaluator(ROOT/'shared/runtime')
    try:assert run(a.program({'trace_scope':'longest_leg'}),g)==expected
    finally:b.close()

def test_lessons_require_segment_identity_not_just_color(a):
    for seed in (0,7,17,43):
        e=a.generate(seed,{'trace_scope':'longest_leg'},2,4)
        ray=a.trace(e['train'][0]['input'])[0]
        color=next(p[2] for p in ray['cells'] if p[3]==ray['winner'])
        assert any(p[2]==color and p[3]!=ray['winner'] for p in ray['cells']), 'Winner color must recur on another leg'
        ray=a.trace(e['train'][1]['input'])[0]
        from collections import Counter
        totals=Counter(p[2] for p in ray['cells'])
        color=next(p[2] for p in ray['cells'] if p[3]==ray['winner'])
        assert totals[color]<max(totals.values()), 'Aggregate color winner must differ from longest leg'

@pytest.mark.parametrize('mode',['all_legs','longest_leg'])
def test_rivals_rejected_and_executable(a,mode):
    assert hasattr(a,'rival_programs'),'Executable nearby rules are required'
    from arcpuzzles.parametric_worker import _real_evaluator
    run,_,b=_real_evaluator(ROOT/'shared/runtime')
    try:
        e=a.generate(17,{'trace_scope':mode},2,4)
        for name,program in a.rival_programs({'trace_scope':mode}).items():
            ys=[run(program,p['input']) for p in e['train']]
            assert all(y==a.rival_predict(p['input'],mode,name) for y,p in zip(ys,e['train'])),name
            assert any(y!=p['output'] for y,p in zip(ys,e['train'])),name
    finally:b.close()
