from pathlib import Path
import importlib.util
import json
import shutil
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

def load(path,name='path_adapter_test'):
    assert path.is_file(),f'Missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);return a
@pytest.fixture(scope='module')
def a():return load(HOME/'workspace/parametric/adapter.py')

@pytest.mark.parametrize('index',range(3))
def test_original_path_preserves_counts_and_repeated_runs(a,index):
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['7b5033c1']
    s=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['7b5033c1']
    ps=d['train']+[dict(input=p['input'],output=o) for p,o in zip(d['test'],s)]
    assert a.G.solve(ps[index]['input'],'straighten')==ps[index]['output']

def test_literal_nonmonotone_path(a):
    g=[[8,8,8,8,8],[1,1,2,8,8],[8,8,2,8,8],[3,3,3,8,8],[4,8,8,8,8]]
    assert a.G.solve(g,'straighten')==[[1],[1],[2],[2],[3],[3],[3],[4]]
    # First run length 2 selects candidate index 1, the three green cells.
    assert a.G.solve(g,'anchor_indexed_run')==[[3],[3],[3]]

def test_default_exact_and_declared_resources_portable(a,tmp_path):
    assert a.program({'mode':'straighten'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    c=json.loads((HOME/'workspace/parametric/promotion.json').read_text())
    for f in [c['adapter'],*c['resources']]:shutil.copyfile(ROOT/f,tmp_path/Path(f).name)
    b=load(tmp_path/'adapter.py','relocated_path_adapter')
    assert b.generate(43,{'mode':'anchor_indexed_run'},2,4)==a.generate(43,{'mode':'anchor_indexed_run'},2,4)

@pytest.mark.parametrize('seed',[0,1,2,17,43,127])
def test_prefix_matching_and_copy_isolation(a,seed):
    e=a.generate(seed,{'mode':'straighten'},6,4);f=a.generate(seed,{'mode':'anchor_indexed_run'},6,4)
    assert [p['input'] for k in ('train','test') for p in e[k]]==[p['input'] for k in ('train','test') for p in f[k]]
    assert len({json.dumps(p['input']) for k in ('train','test') for p in e[k]})==10
    for d in range(2,7):
        sub=a.generate(seed,{'mode':'straighten'},d,4)
        assert sub['train']==e['train'][:d] and sub['test']==e['test']
    for q in range(1,5):assert a.generate(seed,{'mode':'straighten'},2,q)['test']==e['test'][:q]
    e['train'][0]['input'][0][0]=-1
    assert min(v for row in a.generate(seed,{'mode':'straighten'},6,4)['train'][0]['input'] for v in row)>=0

@pytest.mark.parametrize('seed',range(8))
def test_minimum_lesson_refutes_query_changing_shortcuts(a,seed):
    for mode in a.G.MODES:
        e=a.generate(seed,{'mode':mode},2,4)
        for rival in a.G.RIVALS:
            survives=all(a.G.solve(p['input'],mode,rival=rival)==p['output'] for p in e['train'])
            changes=any(a.G.solve(p['input'],mode,rival=rival)!=p['output'] for p in e['test'])
            assert not(survives and changes),(seed,mode,rival)

def test_stress_uses_entire_lawful_length_budget(a):
    e=a.generate(17,{'mode':'straighten'},2,4);g=e['test'][-1]['input'];z=a.G.analyze(g)
    assert len(g)==len(g[0])==30
    assert len(z['path'])==30 and len(e['test'][-1]['output'])==30
    assert max(max(p[j] for p in z['path'])-min(p[j] for p in z['path']) for j in (0,1))==29
    assert len(z['runs'])>=5 and len({r[0] for r in z['runs']})<len(z['runs'])

def test_public_masked_and_first_turn_consistent(a):
    seen=set()
    for seed in range(8):
        b=a.present(seed,{'mode':'anchor_indexed_run'},2,4,presentation_seed=73)
        assert b['public'][0]==a.present(seed,{'mode':'anchor_indexed_run'},2,1,presentation_seed=73)['public'][0]
        seen.add(b['private']['source_indices'][0])
        for v in b['public']:
            assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
    assert len(seen)>1

@pytest.mark.parametrize('g',[[],[[]],[[True]],[[10]],[[0],[1,2]],[[0.0]],[[0]*3 for _ in range(3)],[[0,1,0],[1,1,1],[0,1,0]]])
def test_invalid_grid_or_branched_path(a,g):
    with pytest.raises((ValueError,TypeError)):a.G.solve(g)

@pytest.mark.parametrize('args',[(True,{'mode':'straighten'},2,4),(0,{'mode':'bad'},2,4),(0,{},2,4),(0,{'mode':'straighten'},1,4),(0,{'mode':'straighten'},7,4),(0,{'mode':'straighten'},2,0),(0,{'mode':'straighten'},2,5)])
def test_invalid_generation_controls(a,args):
    with pytest.raises((ValueError,TypeError)):a.generate(*args)
