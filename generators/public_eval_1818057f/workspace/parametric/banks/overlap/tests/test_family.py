"""Regression fixtures are literal or hand-constructed, not solver-derived labels."""
from pathlib import Path
import importlib.util
import json
import pytest

HOME = Path(__file__).resolve().parents[1]

def load(name, path):
    assert path.is_file(), f'missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def test_implementation_exists():
    assert (HOME/'generator.py').is_file(), 'missing self-contained generator'
    assert (HOME/'workspace/parametric/adapter.py').is_file(), 'missing native adapter'

@pytest.fixture
def engine(): return load('plus_base', HOME/'generator.py')
@pytest.fixture
def adapter(): return load('plus_adapter', HOME/'workspace/parametric/adapter.py')

def stamp(g,r,c):
    for dr,dc in ((0,0),(-1,0),(1,0),(0,-1),(0,1)):g[r+dr][c+dc]=4

def test_canonical_literal_and_simultaneous_detection(engine):
    g=[[2,4,2,4,2],[4,4,4,4,4],[2,4,2,4,2]]
    assert engine.solve(g,'all')==[[2,8,2,8,2],[8,8,8,8,8],[2,8,2,8,2]]
    assert g==[[2,4,2,4,2],[4,4,4,4,4],[2,4,2,4,2]]

def test_largest_overlap_not_all_or_area(engine):
    g=[[2]*15 for _ in range(9)]
    for r,c in [(1,1),(1,3),(1,10)]:stamp(g,r,c)
    # Long arm belongs to the singleton's yellow component, not another plus.
    for c in range(10,15):g[1][c]=4
    for r in range(1,9):g[r][14]=4
    out=engine.solve(g,'largest_overlap')
    assert {(r,c) for r in range(9) for c in range(15) if out[r][c]==8}=={(0,1),(1,0),(1,1),(1,2),(2,1),(0,3),(1,3),(1,4),(2,3)}
    assert out[1][10]==4

def test_maximum_ties_are_all_retained(engine):
    g=[[2]*13 for _ in range(7)]
    for r,c in [(1,1),(1,3),(4,8),(4,10)]:stamp(g,r,c)
    assert engine.solve(g,'largest_overlap')==engine.solve(g,'all')

def test_missing_arm_diagonal_and_off_canvas_do_not_match(engine):
    g=[[4,4,4],[4,4,2],[4,2,4]]
    assert engine.solve(g,'all')==g

@pytest.mark.parametrize('g',[[],[[]],[[True]],[[1.0]],[[10]],[[1],[1,2]],[[0]*31],[[0]]*31])
def test_grid_types_fail_closed(engine,g):
    with pytest.raises(ValueError):engine.solve(g,'all')

@pytest.mark.parametrize('seed',[0,1,17,43,103])
def test_episode_contract_and_prefixes(adapter,seed):
    a=adapter.generate(seed,{'selection':'all'},2,4)
    b=adapter.generate(seed,{'selection':'largest_overlap'},2,4)
    assert [p['input'] for s in ('train','test') for p in a[s]]==[p['input'] for s in ('train','test') for p in b[s]]
    assert a!=b and all(x['output']!=y['output'] for x,y in zip(a['train'],b['train']))
    assert len({json.dumps(p['input']) for s in ('train','test') for p in a[s]})==6
    for d in range(2,7):
        full=adapter.generate(seed,{'selection':'all'},d,4)
        assert full['train'][:2]==a['train'] and full['test']==a['test']
        for q in (1,2,3):assert adapter.generate(seed,{'selection':'all'},d,q)['test']==full['test'][:q]
    g=a['test'][3]['input'];assert len(g)==len(g[0])==30
    assert sum(x!=2 for row in g for x in row)>100
    assert all(any(g[r][c]!=2 for r,c in side) for side in [[(0,c) for c in range(30)],[(29,c) for c in range(30)],[(r,0) for r in range(30)],[(r,29) for r in range(30)]])

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'demos':1},{'demos':7},{'demos':3.0},{'queries':0},{'queries':5},{'queries':True},{'settings':{}},{'settings':{'selection':'bad'}},{'settings':{'selection':'all','x':1}}])
def test_bad_episode_requests(adapter,kwargs):
    args={'seed':0,'settings':{'selection':'all'},'demos':2,'queries':4};args.update(kwargs)
    with pytest.raises(ValueError):adapter.generate(**args)

def test_original_python_parity(engine):
    import hashlib
    path=HOME/'tests/original-pairs.json'
    assert hashlib.sha256(path.read_bytes()).hexdigest()=='9aa8db9e7e5527b0544ffbb98dead093204801e3276c71491716dc585ac5298e'
    fixture=json.loads(path.read_text())
    parent=json.loads((HOME/'workspace/public-parent.json').read_text())
    assert fixture['source_record_sha256']==parent['source_record_sha256']
    assert fixture['test_outputs_sha256']==parent['test_outputs_sha256']
    for pair in fixture['pairs']:
        assert engine.solve(pair['input'],engine.SETTINGS[0])==pair['output']


def test_resource_and_engine_byte_identity(adapter):
    assert adapter.program({'selection':'all'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/engine.py').read_bytes()

def test_base_relocates_without_sidecars(engine,tmp_path):
    import shutil
    p=tmp_path/'generator.py';shutil.copy2(HOME/'generator.py',p);base=load('relocated_plus',p)
    for i in range(8):
        g=base.generate(23,i)
        assert base.self_check(g)==[] and g==engine.generate(23,i)
        assert base.solve(g,'all')!=g

@pytest.mark.parametrize('seed',range(12))
def test_two_demo_lesson_rejects_harmful_declared_rivals(adapter,seed):
    e=adapter.engine
    for mode in e.SETTINGS:
        episode=adapter.generate(seed,{'selection':mode},2,4)
        predictions=[e.rivals(p['input'],mode) for p in episode['train']+episode['test']]
        harmful=[name for name in predictions[0]
                 if all(pred[name]==p['output'] for pred,p in zip(predictions[:2],episode['train']))
                 and any(pred[name]!=p['output'] for pred,p in zip(predictions[2:],episode['test']))]
        assert harmful==[]

def test_curriculum_contains_embedded_corner_and_maximum_tie(adapter):
    e=adapter.engine;episode=adapter.generate(0,{'selection':'largest_overlap'},2,4)
    assert any(e.rivals(p['input'],'largest_overlap')['isolated_diagonal_corners']!=p['output'] for p in episode['train'])
    assert any(len([s for s in e.clusters(e.centers(p['input'])) if len(s)==max(map(len,e.clusters(e.centers(p['input']))))])>1 for p in episode['train'])

def test_audit_rejects_wrong_claim(adapter):
    import copy
    audit=load('plus_audit',HOME/'workspace/parametric/audit_lessons.py')
    ep=adapter.generate(3,{'selection':'largest_overlap'},2,4)
    assert audit.check_episode(adapter,ep,'largest_overlap')==[]
    bad=copy.deepcopy(ep);bad['test'][0]['output']=bad['test'][0]['input']
    assert any('claim label' in x for x in audit.check_episode(adapter,bad,'largest_overlap'))

def test_overlap_graph_topology_varies_not_only_position(engine):
    edge_counts=set()
    for seed in range(16):
        groups=engine.clusters(engine.centers(engine.scene(seed,3,'query')))
        group=max(groups,key=len)
        edge_counts.add(sum(abs(r-s)+abs(c-t)==2 for i,(r,c) in enumerate(group) for s,t in group[i+1:]))
    assert len(edge_counts)>1

def test_area_surrogate_is_taught(adapter):
    e=adapter.engine;ep=adapter.generate(2,{'selection':'largest_overlap'},2,4)
    assert 'largest_union_area' in e.rivals(ep['train'][0]['input'],'largest_overlap')
    assert any(e.rivals(p['input'],'largest_overlap')['largest_union_area']!=p['output'] for p in ep['train'])


def test_original_label_fixture_is_task_local():
    assert (HOME/'tests/original-pairs.json').is_file(), 'staged tests need a task-owned original-label fixture'
