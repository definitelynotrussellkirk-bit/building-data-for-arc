"""Official-label, generated-family, public-projection and causal regressions."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]


def load(name):
    path=HOME/'workspace/parametric'/(name+'.py')
    assert path.is_file(), f'missing implementation {path.name}'
    key='_t3e_'+name
    spec=importlib.util.spec_from_file_location(key,path)
    module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def official():
    return json.loads((HOME/'tests/fixtures/official.json').read_text())


def test_reference_exists():
    assert (HOME/'reference.rkt').is_file(), 'general canonical Racket rule missing'


@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_original_python_labels(official,split,index):
    p=official[split][index]
    assert load('family').solve(p['input'],'source')==p['output']


def test_original_protected_racket_labels(official):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        assert identity['backend']=='racket' and identity['protected']
        program=(HOME/'reference.rkt').read_text()
        for pairs in official.values():
            for p in pairs:
                assert apply(program,p['input'])==p['output']
    finally:bridge.close()


@pytest.mark.parametrize('seed',[0,17,43])
def test_constructive_scene_round_trip(seed):
    f=load('family')
    for index,shape in [(0,(14,17)),(1,(18,20)),(5,(24,27)),(103,(30,30))]:
        scene=f.make_scene(seed,index,*shape)
        data=f.parse(scene['input'])
        assert data['sequence']==scene['sequence']
        assert [b['color'] for b in data['route']]==scene['sequence']
        assert f.solve(scene['input'],'source')==scene['source_output']
        assert f.solve(scene['input'],'destination')==scene['destination_output']
        assert scene['source_output']!=scene['destination_output']
        assert f.self_check_scene(scene)==[]


@pytest.mark.parametrize('seed',[0,17,43])
def test_parametric_counts_matching_and_boundary(seed):
    a=load('adapter')
    for demos in (2,3,6):
        episodes=[a.generate(seed,{'bridge_color':v},demos,4) for v in ('source','destination')]
        assert [p['input'] for p in episodes[0]['train']+episodes[0]['test']]==[p['input'] for p in episodes[1]['train']+episodes[1]['test']]
        for episode in episodes:
            assert len(episode['train'])==demos and len(episode['test'])==4
            assert episode['private_query_bank']==episode['test']
            assert len({json.dumps(p['input']) for p in episode['train']+episode['test']})==demos+4
            q=episode['test'][-1]
            assert len(q['input'])==len(q['input'][0])==30
            assert len(q['output'])==len(q['output'][0])==30
        assert all(p['output']!=q['output'] for p,q in zip(episodes[0]['train'],episodes[1]['train']))


@pytest.mark.parametrize('bad',[True,1.5,'2',-1,None])
def test_seed_rejection(bad):
    with pytest.raises(ValueError):load('adapter').generate(bad,{'bridge_color':'source'},2,4)


@pytest.mark.parametrize('field,bad',[('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',2.0)])
def test_count_rejection(field,bad):
    args=dict(seed=0,settings={'bridge_color':'source'},demos=2,queries=4);args[field]=bad
    with pytest.raises(ValueError):load('adapter').generate(**args)


@pytest.mark.parametrize('settings',[{},None,{'bridge_color':'bad'},{'bridge_color':True},{'bridge_color':'source','extra':1}])
def test_setting_rejection(settings):
    with pytest.raises(ValueError):load('adapter').program(settings)


def test_default_program_and_public_projection_are_private():
    a=load('adapter')
    assert a.program({'bridge_color':'source'})==(HOME/'reference.rkt').read_text()
    full=a.generate(43,{'bridge_color':'destination'},2,4)
    short=a.generate(43,{'bridge_color':'destination'},2,1)
    assert short['test']==full['test'][:1]
    assert {a.presentation_order(s)[0] for s in range(32)}=={0,1,2,3}
    for i in range(4):
        view=a.public_view(full,i)
        assert a.public_view(short,i)==view
        altered=deepcopy(full);altered.update(seed='secret',settings={'secret':True},program_solution='secret')
        for j,p in enumerate(altered['private_query_bank']):
            p['output']=[[9]]
            if i!=j:p['input']=[[7]]
        assert a.public_view(altered,i)==view
        assert set(view)=={'train','test'} and len(view['test'])==1 and set(view['test'][0])=={'input'}


def test_generated_racket_parity():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load('adapter');apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        for seed in (0,17):
            for setting in ('source','destination'):
                e=a.generate(seed,{'bridge_color':setting},2,4)
                for p in e['train']+e['test']:
                    assert apply(e['program_solution'],p['input'])==p['output'],(seed,setting)
    finally:bridge.close()


def test_finite_rivals_refuted_by_two_demos():
    a,rivals=load('adapter'),load('rivals')
    for seed in range(8):
        for setting in ('source','destination'):
            e=a.generate(seed,{'bridge_color':setting},2,4)
            names=set(rivals.predict(e['train'][0]['input'],setting))
            for p in e['train']:
                predictions=rivals.predict(p['input'],setting)
                names={n for n in names if predictions[n]==p['output']}
            assert not names,(seed,setting,names)


def test_wrong_route_racket_witness():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load('adapter');p=a.generate(17,a.causal_settings(),2,4)['test'][-1]
    apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        assert apply(a.program(a.causal_settings()),p['input'])==p['output']
        assert apply(a.counterfactual_program(),p['input'])!=p['output']
    finally:bridge.close()


def test_audit_tool_smoke(tmp_path):
    report=load('audit').run_audit(tmp_path/'audit',seeds=[0],racket_seeds=[])
    assert report['status']=='passed' and not report['findings']
    assert report['episodes']==6 and report['public_turns']==8


def test_canonical_generator_is_self_contained_when_relocated(tmp_path):
    import os,shutil,subprocess
    from reviewer_support import find_root
    shutil.copy2(HOME/'generator.py',tmp_path/'generator.py')
    code="""import json, generator\ng=generator.generate(29,3,height=14,width=17)\nassert not generator.self_check(g)\nprint(json.dumps({'shape':[len(g),len(g[0])],'output':generator.rule_mirror(g)}))\n"""
    env=dict(os.environ,PYTHONPATH=str(find_root(__file__)/'shared/runtime'),PYTHONDONTWRITEBYTECODE='1')
    proc=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,env=env,text=True,capture_output=True,timeout=30)
    assert proc.returncode==0,proc.stderr
    result=json.loads(proc.stdout);assert result['shape']==[14,17] and len(result['output'])==14
