import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def local(name):
    p=HOME/'workspace/parametric'/f'{name}.py'
    assert p.is_file(), f'{name} has not been authored'
    s=importlib.util.spec_from_file_location('_20a9e565_test_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def originals():
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['20a9e565']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['20a9e565']
    return d['train']+[{'input':p['input'],'output':v}for p,v in zip(d['test'],gold)]

@pytest.mark.parametrize('index',range(5))
def test_inferred_sequence_reproduces_supplied_labels(index):
    m=local('family');p=originals()[index]
    assert m.solve(p['input'])==p['output']

def test_protected_reference_executes_all_five_original_labels():
    p=HOME/'reference.rkt';assert p.is_file(), 'Protected sequence reference missing'
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert identity['protected']
        for pair in originals():assert apply(p.read_text(),pair['input'])==pair['output']
    finally:bridge.close()

@pytest.mark.parametrize('seed',range(6))
def test_scenes_preserve_the_growth_grammar_and_crop_ground_truth(seed):
    m=local('family');assert hasattr(m,'scene_spec'),'Sequence sampler missing'
    cases=[m.scene_spec(seed,i)for i in range(10)]
    assert len({json.dumps(x['input'])for x in cases})==10
    assert {x['kind']for x in cases}=={'arch','spine','ladder','chain','wave'}
    for case in cases:
        assert m.solve(case['input'])==case['output']
    assert len(cases[-1]['input'])==len(cases[-1]['input'][0])==30
    sizes=[]
    for case in cases[:2]:
        g=case['output'];ps=m.components((r,c)for r,row in enumerate(g)for c,v in enumerate(row)if v)
        assert len(ps)>=2
        largest=max(ps,key=len);sizes.append(ps.index(largest))
        assert m.solve(case['input'],'largest_visible_region')!=g
    assert sizes[0]==0 and sizes[1]>0

def test_component_ranking_uses_the_cropped_intermediate():
    m=local('family');assert hasattr(m,'mark_largest'), 'Post-crop selector missing'
    g=[[2,0,3,3],[2,0,3,0]]
    assert m.mark_largest(g)==[[2,0,9,9],[2,0,9,0]]

def test_coordinate_recurrences_include_acceleration_and_alternation():
    m=local('family')
    assert m.extrapolate([1,4,8,13],4)==19
    assert m.extrapolate([12,10,7,5],4)==2
    assert m.extrapolate([0,3,8],3)==15

@pytest.mark.parametrize('demos',range(2,7))
@pytest.mark.parametrize('queries',range(1,5))
def test_independent_counts_and_matched_streams(demos,queries):
    a=local('adapter')
    x=a.generate(17,{'finish':'extrapolate'},demos,queries)
    y=a.generate(17,{'finish':'largest_visible_region'},demos,queries)
    assert [len(x[s])for s in ('train','test')]==[demos,queries]
    assert [p['input']for s in ('train','test')for p in x[s]]==[p['input']for s in ('train','test')for p in y[s]]
    full=a.generate(17,{'finish':'extrapolate'},6,4)
    assert x['train']==full['train'][:demos] and x['test']==full['test'][:queries]

@pytest.mark.parametrize('bad',[True,2.0,'2',None,-1,7])
def test_exact_integer_counts_reject_coercions(bad):
    a=local('adapter')
    with pytest.raises(ValueError):a.generate(0,{'finish':'extrapolate'},bad,4)

def test_public_projection_prefix_privacy_and_ids(tmp_path):
    import copy,hashlib
    from reviewer_support import public_challenge_bytes
    a=local('adapter');p=local('public_views');e=a.generate(17,{'finish':'extrapolate'},2,4)
    many,order=p.project(e,42,4);one,first=p.project(e,42,1)
    assert one==many[:1] and first==order[:1]
    mutation=copy.deepcopy(e);mutation['seed']='secret';mutation['settings']={'secret':True};mutation['program_solution']='secret'
    for x in mutation['train']:x['secret']='leak'
    for x in mutation['test']:x['output']=[[9]];x['secret']='leak'
    assert p.project(mutation,42,4)==(many,order)
    assert {tuple(p.project(e,s,4)[1])for s in range(10)}!={tuple(range(4))}
    info=p.export(e,tmp_path/'views',42)
    assert p.verify(tmp_path/'views')['files']==4
    for f in (tmp_path/'views').glob('*.json'):
        assert f.read_bytes()==public_challenge_bytes(json.loads(f.read_bytes()))
        assert f.stem==hashlib.sha256(f.read_bytes()).hexdigest()
    f=next((tmp_path/'views').glob('*.json'));f.write_bytes(f.read_bytes()+b' ')
    with pytest.raises(ValueError):p.verify(tmp_path/'views')

def test_invalid_public_batch_fails_before_creating_directory(tmp_path):
    import copy
    a=local('adapter');p=local('public_views');e=a.generate(17,{'finish':'extrapolate'},2,4)
    e['test'][0]['input'][0][0]=False
    with pytest.raises(ValueError):p.export(e,tmp_path/'bad',0)
    assert not (tmp_path/'bad').exists()

def test_default_program_is_exact_and_variants_execute():
    a=local('adapter');assert a.program({'finish':'extrapolate'})==(HOME/'reference.rkt').read_text()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for finish in a.SETTINGS:
            e=a.generate(17,{'finish':finish},2,4)
            for p in e['train']+e['test']:assert apply(e['program_solution'],p['input'])==p['output']
    finally:bridge.close()

def test_two_demonstrations_refute_one_step_palette_shortcut():
    a=local('adapter');e=a.generate(2,{'finish':'extrapolate'},2,4)
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,_,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        bad=(HOME/'workspace/parametric/next_palette.rkt').read_text()
        assert any(apply(bad,p['input'])!=p['output']for p in e['train']), 'One-step palette rival survives both demos'
    finally:bridge.close()
