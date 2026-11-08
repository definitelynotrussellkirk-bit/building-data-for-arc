"""Author-private original-label tests; never imported by generation."""
import importlib.util,json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def model():
    path=HOME/'workspace/parametric/prototype.py'
    assert path.is_file(),'support-physics solver is not implemented'
    spec=importlib.util.spec_from_file_location('support_model_test',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def original_pairs():
    raw=ROOT/'shared/data/raw';t=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['b6f77b65']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['b6f77b65']
    return t['train']+[{'input':p['input'],'output':y} for p,y in zip(t['test'],gold)]

@pytest.mark.parametrize('pair',original_pairs(),ids=['train0','train1','train2','train3','train4','test0','test1','test2'])
def test_original_labels(pair):assert model().solve(pair['input'])==pair['output']

def test_latent_endpoint_revealed_on_post_landing():
    x=[[0]*7 for _ in range(9)];x[0][0]=4
    for r in (2,3):x[r][3]=2
    for r in (4,5):x[r][0]=9;x[r][4]=7
    for c in (1,2,3):x[4][c]=4
    for r in (6,7,8):x[r][3]=1
    expected=[[0]*7 for _ in range(9)];expected[0][0]=4
    for r in (3,4,5):expected[r][3]=2
    for r in (6,7,8):expected[r][3]=1
    for r in (7,8):expected[r][0]=9;expected[r][4]=7
    assert model().solve(x)==expected

@pytest.mark.parametrize('pair',original_pairs())
def test_original_color_permutation_and_padding(pair):
    mod=model();mapping={0:0,**{i:10-i for i in range(1,10)}}
    perm=lambda g:[[mapping[v] for v in row] for row in g]
    assert mod.solve(perm(pair['input']))==perm(pair['output'])
    def padded(g):
        w=len(g[0])+4
        return [[0,0]+g[0]+[0,0]]+[[0]*w for _ in range(3)]+[[0,0]+row+[0,0] for row in g[2:]]
    assert mod.solve(padded(pair['input']))==padded(pair['output'])

def test_protected_reference_original_labels():
    reference=HOME/'reference.rkt'
    assert reference.is_file(),'native support-physics reference is missing'
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for p in original_pairs():assert _grid(apply(reference.read_text(),p['input']))==p['output']
        finally:bridge.close()

def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'native support-graph adapter missing'
    spec=importlib.util.spec_from_file_location('support_adapter_test',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

@pytest.mark.parametrize('seed',[0,17,43,101])
def test_fresh_sampler_contract(seed):
    a=adapter();eps=[a.generate(seed,s,2,4) for s in a.SETTINGS]
    assert [[p['input'] for p in ep['train']+ep['test']] for ep in eps][0]==[[p['input'] for p in ep['train']+ep['test']] for ep in eps][1]
    for setting,ep in zip(a.SETTINGS,eps):
        pairs=ep['train']+ep['test'];assert len({json.dumps(p['input']) for p in pairs})==6
        for p in pairs:
            assert len(p['input'])<=30 and len(p['input'][0])<=30
            assert model().solve(p['input'],either=setting['support_rule']=='either_post')==p['output']
        assert any(p['output']!=q['output'] for p,q in zip(eps[0]['train'],eps[1]['train']))
        stress=ep['test'][3]['input'];assert len(stress)==len(stress[0])==30
        assert any(stress[0]) and any(stress[-1]) and any(r[0] for r in stress) and any(r[-1] for r in stress)
        assert sum(v!=0 for row in stress for v in row)>100

@pytest.mark.parametrize('demos',range(2,7))
@pytest.mark.parametrize('queries',range(1,5))
def test_counts_and_prefix_stability(demos,queries):
    a=adapter();full=a.generate(4,a.SETTINGS[0],6,4);ep=a.generate(4,a.SETTINGS[0],demos,queries)
    assert ep['train']==full['train'][:demos] and ep['test']==full['test'][:queries]

@pytest.mark.parametrize('bad',[True,-1,1.5,'2'])
def test_strict_seed(bad):
    a=adapter()
    with pytest.raises(ValueError):a.generate(bad,a.SETTINGS[0])

def test_public_projection_private_fields_and_query_count():
    import copy
    a=adapter();ep=a.generate(17,a.SETTINGS[1]);views=a.public_views(ep,8,4)
    altered=copy.deepcopy(ep);altered['settings']={'hidden':True};altered['program_solution']='secret'
    for p in altered['test']:p['output']=[[9]]
    assert a.public_views(altered,8,4)==views
    assert a.public_views(ep,8,1)==views[:1]
    assert all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)

def test_exact_default_and_unknown_parameters():
    a=adapter();assert a.program(a.SETTINGS[0])==(HOME/'reference.rkt').read_text()
    for invalid in ({},{'support_rule':'bad'},{'support_rule':'both_posts','extra':0}):
        with pytest.raises(ValueError):a.program(invalid)
        with pytest.raises(ValueError):a.generate(0,invalid)

def test_generator_strict_and_canonical():
    path=HOME/'generator.py';assert path.is_file(),'production support generator missing'
    spec=importlib.util.spec_from_file_location('support_generator_test',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for index in range(4):
        grid=mod.generate(17,index);assert grid==mod.generate(17,index)
        assert not mod.self_check(grid)
        assert mod.rule_mirror(grid)==model().solve(grid)
    with pytest.raises(ValueError):mod.generate(17,0,unknown=1)

@pytest.mark.parametrize('seed',[0,17,43,101])
@pytest.mark.parametrize('either',[False,True])
def test_minimum_lesson_rejects_raw_supports(seed,either):
    a=adapter();ep=a.generate(seed,a.SETTINGS[int(either)],2,4)
    assert any(model().solve(p['input'],either=either,raw_support=True)!=p['output'] for p in ep['train'])
