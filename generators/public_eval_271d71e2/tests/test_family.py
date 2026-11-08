"""Behavioral regression tests; original labels and literal fixtures are independent."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import shutil
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').exists())
NATIVE=HOME/'workspace/parametric'

def load(path=NATIVE/'adapter.py'):
    assert path.is_file(), 'missing native adapter implementation'
    spec=importlib.util.spec_from_file_location('_271d71e2_test_adapter',path)
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);return a

@pytest.fixture(scope='module')
def a():return load()

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['protected'] is True
    yield apply
    bridge.close()

def originals():
    raw=ROOT/'shared/data/raw'
    c=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['271d71e2']
    s=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['271d71e2']
    return c['train']+[dict(input=x['input'],output=y) for x,y in zip(c['test'],s)]

def test_sources_exist_before_using_claim_labels():
    assert (HOME/'reference.rkt').is_file(), 'general reference still needs authoring'
    assert (NATIVE/'adapter.py').is_file()

@pytest.mark.parametrize('index',range(4))
def test_all_original_labels(index,a,evaluator):
    p=originals()[index]
    assert a.predict(p['input'])==p['output']
    assert evaluator(a.program(a.DEFAULT),p['input'])==p['output']

def test_default_is_exact_and_native_copy_matches(a):
    assert a.program(a.DEFAULT).encode()==(HOME/'reference.rkt').read_bytes()==(NATIVE/'canonical.rkt').read_bytes()

def test_capacity_limited_motion_literal(a,evaluator):
    g=[[6]*9 for _ in range(6)]
    # One 3x4 black frame at columns 4..7; mobile rail 3, fixed rail 0.
    for r in range(1,4):
        g[r][0]=g[r][3]=9
        for c in range(4,8):g[r][c]=0
    g[2][5:7]=[5,5]
    want=[[6]*9 for _ in range(6)]
    for r in range(1,4):
        want[r][0]=want[r][1]=9
        for c in range(2,6):want[r][c]=0
    want[2][3:5]=[7,7]
    for k in range(4):
        gg=a.rotate(g,k);yy=a.rotate(want,k)
        assert a.predict(gg)==yy
        assert evaluator(a.program(a.DEFAULT),gg)==yy

@pytest.mark.parametrize('seed',[0,1,17,43])
def test_counts_prefix_and_matched_inputs(seed,a):
    full={v:a.generate(seed,{'motion_policy':v},6,4) for v in a.PARAMETERS['motion_policy']}
    for v,e in full.items():
        for d in range(2,7):
            for q in range(1,5):
                x=a.generate(seed,{'motion_policy':v},d,q)
                assert x['train']==e['train'][:d] and x['test']==e['test'][:q]
                assert len({json.dumps(p['input']) for s in ('train','test') for p in x[s]})==d+q
    assert [p['input'] for s in ('train','test') for p in full['all_moves'][s]]==[p['input'] for s in ('train','test') for p in full['longest_move'][s]]

def test_two_demo_rivals_rejected(a,evaluator):
    for seed in [0,17]:
        e=a.generate(seed,{'motion_policy':'longest_move'},2,4)
        for name,source in a.rival_programs().items():
            labels=[evaluator(source,p['input']) for p in e['train']]
            assert labels==[a.predict(p['input'],name) for p in e['train']]
            assert labels!=[p['output'] for p in e['train']],(seed,name)

def test_large_query_and_direction_coverage(a):
    e=a.generate(17,{'motion_policy':'longest_move'},2,4)
    p=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
    occupied={(r,c) for r,row in enumerate(p['input']) for c,v in enumerate(row) if v!=6}
    assert min(r for r,c in occupied)==min(c for r,c in occupied)==0
    assert max(r for r,c in occupied)==max(c for r,c in occupied)==29
    assert len({(r//15,c//15) for r,c in occupied})==4
    frames=a.analyze(p['input'])
    assert len(frames)>=4
    d=[f['distance'] for f in frames];assert d.count(max(d))==1
    assert a.predict(p['input'],'longest_move')!=a.predict(p['input'],'max_gap')

def test_public_view_ignores_all_private_and_extra_pair_fields(a):
    e=a.generate(0,{'motion_policy':'longest_move'},3,4);want=a.public_turn(e,0)
    x=deepcopy(e);x['private']={'secret':99};x['program_solution']='secret'
    for p in x['train']:p['answer_hint']='secret'
    for p in x['test']:p['output']=[[9]];p['secret']='secret'
    x['test'][1:]=[{'input':[[8]],'output':[[8]]}]*3
    assert a.public_turn(x,0)==want
    assert set(want)=={'train','test'} and set(want['test'][0])=={'input'}
    want['train'][0]['input'][0][0]=9
    assert e==a.generate(0,{'motion_policy':'longest_move'},3,4)

def test_native_folder_is_relocatable(a,tmp_path):
    shutil.copytree(NATIVE,tmp_path/'native',ignore=shutil.ignore_patterns('__pycache__'))
    other=load(tmp_path/'native/adapter.py')
    assert other.generate(17,other.DEFAULT,2,4)==a.generate(17,a.DEFAULT,2,4)

@pytest.mark.parametrize('args',[(True,{},2,4),(0,{'motion_policy':'bad'},2,4),(0,{'motion_policy':'all_moves','extra':1},2,4),(0,{'motion_policy':'all_moves'},1,4),(0,{'motion_policy':'all_moves'},7,4),(0,{'motion_policy':'all_moves'},2,0),(0,{'motion_policy':'all_moves'},2,5),(0,{'motion_policy':'all_moves'},2,True)])
def test_invalid_requests_rejected(args,a):
    with pytest.raises(ValueError):a.generate(*args)

def test_base_stream_does_not_cycle_at_four(a):
    spec=importlib.util.spec_from_file_location('_271d_base',HOME/'generator.py')
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    assert g.RULE_TASK_ID=='ee_271d71e2'
    draws=[g.generate(17,i) for i in range(8)]
    assert len({json.dumps(x) for x in draws})==8

def test_winner_can_stop_at_either_rail_or_fuel(a):
    reasons=set();travels=set()
    for seed in range(8):
        for p in a.generate(seed,{'motion_policy':'longest_move'},6,4)['train']:
            f=max(a.analyze(p['input']),key=lambda x:x['distance'])
            reasons.add('fuel' if f['fuel']<f['gap'] else 'rail');travels.add(f['distance'])
    assert reasons=={'fuel','rail'}
    assert len(travels)>=4
