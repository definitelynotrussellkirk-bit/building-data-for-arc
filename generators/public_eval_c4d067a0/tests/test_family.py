"""Public parent and relational registration regressions; gold is private."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]

def load(name):
    path=HOME/'workspace/parametric'/(name+'.py')
    assert path.is_file(), f'missing implementation {path.name}'
    spec=importlib.util.spec_from_file_location('_tc4_'+name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def official():return json.loads((HOME/'tests/fixtures/official.json').read_text())

def test_reference_exists():
    assert (HOME/'reference.rkt').is_file(), 'general canonical Racket rule missing'

@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0)])
def test_original_python_labels(official,split,index):
    p=official[split][index]
    assert load('family').solve(p['input'],'all')==p['output']


def test_original_protected_racket_labels(official):
    assert (HOME/'reference.rkt').is_file(), 'general canonical Racket rule missing'
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        assert identity['backend']=='racket' and identity['protected']
        for pairs in official.values():
            for p in pairs:assert apply((HOME/'reference.rkt').read_text(),p['input'])==p['output']
    finally:bridge.close()

@pytest.mark.parametrize('seed',[0,17,43])
def test_generated_registration_matches_constructive_truth(seed):
    f=load('family')
    assert hasattr(f,'make_scene'),'constructive sampler missing'
    for index,shape in [(0,(16,20)),(1,(22,26)),(102,(26,28)),(103,(30,30))]:
        scene=f.make_scene(seed,index,*shape);found=f.infer(scene['input'])
        for key in ('origin','pitch','block_size','pattern'):
            assert found[key]==scene[key],(key,seed,index)
        assert sorted(found['seed_cells'])==sorted(scene['seed_cells'])
        assert f.solve(scene['input'],'all')==f.render(scene['input'],scene)
        assert f.solve(scene['input'],'all')!=f.solve(scene['input'],'anchored_components')


def test_ambiguous_registration_is_rejected():
    f=load('family');g=[[8]*23 for _ in range(22)]
    for r,color in [(1,1),(3,1),(5,2)]:
        for c in (1,3):g[r][c]=color
    for c in (9,13):
        for rr in (10,11):
            for cc in (c,c+1):g[rr][cc]=1
    with pytest.raises(ValueError,match='registration'):f.infer(g)

@pytest.mark.parametrize('seed',[0,17,43])
def test_parametric_counts_matching_and_30x30(seed):
    a=load('adapter')
    for demos in (2,3,6):
        es=[a.generate(seed,{'completion':x},demos,4) for x in ('all','anchored_components')]
        assert [p['input'] for p in es[0]['train']+es[0]['test']]==[p['input'] for p in es[1]['train']+es[1]['test']]
        for e in es:
            assert len(e['train'])==demos and len(e['test'])==4
            assert len({json.dumps(p['input']) for p in e['train']+e['test']})==demos+4
            q=e['test'][-1];assert len(q['input'])==len(q['input'][0])==30
            assert len(q['output'])==len(q['output'][0])==30
            assert e['private_query_bank']==e['test']
        assert any(p['output']!=q['output'] for p,q in zip(es[0]['train'],es[1]['train']))
        f=load('family');data=f.infer(es[0]['test'][-1]['input'])
        assert data['origin'][0]+(len(data['pattern'])-1)*data['pitch']+data['block_size']==30
        assert data['origin'][1]+(len(data['pattern'][0])-1)*data['pitch']+data['block_size']==30

@pytest.mark.parametrize('bad',[True,1.5,'2',-1,None])
def test_seed_rejection(bad):
    with pytest.raises(ValueError):load('adapter').generate(bad,{'completion':'all'},2,4)

@pytest.mark.parametrize('field,bad',[('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',2.0)])
def test_count_rejection(field,bad):
    args=dict(seed=0,settings={'completion':'all'},demos=2,queries=4);args[field]=bad
    with pytest.raises(ValueError):load('adapter').generate(**args)

@pytest.mark.parametrize('settings',[{},None,{'completion':'bad'},{'completion':True},{'completion':'all','extra':1}])
def test_setting_rejection(settings):
    with pytest.raises(ValueError):load('adapter').program(settings)


def test_default_and_one_query_projection():
    from copy import deepcopy
    a=load('adapter')
    assert a.program({'completion':'all'})==(HOME/'reference.rkt').read_text()
    e=a.generate(43,{'completion':'anchored_components'},2,4)
    one=a.generate(43,{'completion':'anchored_components'},2,1)
    assert one['test']==e['test'][:1]
    assert {a.presentation_order(s)[0] for s in range(32)}=={0,1,2,3}
    for i in range(4):
        v=a.public_view(e,i);assert a.public_view(one,i)==v
        altered=deepcopy(e);altered.update(seed='secret',program_solution='secret',settings={'hidden':True})
        for j,p in enumerate(altered['private_query_bank']):
            p['output']=[[9]]
            if i!=j:p['input']=[[8]]
        assert a.public_view(altered,i)==v
        assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}


def test_generated_racket_parity():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load('adapter');apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        for seed in (0,17):
            for setting in ('all','anchored_components'):
                e=a.generate(seed,{'completion':setting},2,4)
                for p in e['train']+e['test']:
                    assert apply(e['program_solution'],p['input'])==p['output'],(seed,setting)
    finally:bridge.close()


def test_canonical_generator_and_strict_controls():
    p=HOME/'generator.py';assert p.is_file(),'canonical generator missing'
    spec=importlib.util.spec_from_file_location('_gc4',p)
    gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
    g=gen.generate(0,0,height=30,width=30)
    assert len(g)==30 and len(g[0])==30 and not gen.self_check(g)
    assert gen.observe_overrides(g)=={'height':30,'width':30}
    for kwargs in ({'height':True},{'width':'20'},{'extra':1}):
        with pytest.raises(ValueError):gen.generate(0,0,**kwargs)


def test_finite_rivals_refuted_with_two_demos():
    a,rivals=load('adapter'),load('rivals')
    for seed in range(8):
        for setting in ('all','anchored_components'):
            e=a.generate(seed,{'completion':setting},2,4)
            names=set(rivals.predict(e['train'][0]['input'],setting))
            for p in e['train']:
                predictions=rivals.predict(p['input'],setting)
                names={n for n in names if predictions[n]==p['output']}
            assert not names,(seed,setting,names)


def test_wrong_registration_racket_witness():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load('adapter');assert hasattr(a,'counterfactual_program'),'causal ablation missing'
    p=a.generate(17,{'completion':'anchored_components'},2,4)['test'][-1]
    apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:assert apply(a.counterfactual_program(),p['input'])!=p['output']
    finally:bridge.close()


def test_audit_tool_smoke(tmp_path):
    report=load('audit').run_audit(tmp_path/'audit',seeds=[0],racket_seeds=[])
    assert report['status']=='passed' and not report['findings']
    assert report['episodes']==6 and report['public_turns']==8
    for p in (tmp_path/'audit/public').glob('*.json'):
        v=json.loads(p.read_text());assert set(v)=={'train','test'}
        assert len(v['test'])==1 and set(v['test'][0])=={'input'}


def test_generator_is_self_contained_when_only_generator_is_relocated(tmp_path):
    """The ordinary owner runtime maps generator.py, not task workspaces."""
    import os
    import shutil
    import subprocess
    from reviewer_support import find_root
    shutil.copy2(HOME/'generator.py', tmp_path/'generator.py')
    program = """import json, generator
g = generator.generate(29, 3, height=16, width=20)
assert not generator.self_check(g)
print(json.dumps({'shape': [len(g), len(g[0])], 'output': generator.rule_mirror(g)}))
""".replace('16',str(16)).replace('20',str(20))
    env = dict(os.environ, PYTHONPATH=str(find_root(__file__)/'shared/runtime'),
               PYTHONDONTWRITEBYTECODE='1')
    proc=subprocess.run([sys.executable,'-c',program],cwd=tmp_path,env=env,
                        text=True,capture_output=True,timeout=30)
    assert proc.returncode==0, proc.stderr
    result=json.loads(proc.stdout)
    assert result['shape']==[16,20]
    assert len(result['output'])==16
