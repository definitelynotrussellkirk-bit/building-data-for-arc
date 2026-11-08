"""Behavioral regressions: crop/phase, reflection, counts, labels, and privacy."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

def load(path):
    assert path.is_file(), f'Missing implementation: {path.name}'
    name='_test_'+str(abs(hash(str(path))))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def adapter():return load(HOME/'workspace/parametric/adapter.py')

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()

def test_literal_crop_phase_and_center(adapter):
    g=[[7,7,7,7],[7,1,7,7],[7,1,1,7],[7,7,7,7]]
    a=adapter.family.solve(g,'translation')
    assert len(a)==12 and len(a[0])==12
    assert [row[4:8] for row in a[4:8]]==[[9,7,9,7],[9,9,9,9],[9,7,9,7],[9,9,9,9]]
    assert a[0][:4]==[0,7,0,7]
    b=adapter.family.solve(g,'alternating_mirror')
    assert [row[4:8] for row in b[4:8]]==[[9,7,7,9],[9,9,9,9],[9,9,9,9],[9,7,7,9]]

@pytest.mark.parametrize('setting',['translation','alternating_mirror'])
def test_racket_hand_fixture(adapter,evaluator,setting):
    g=[[7,7,7,7],[7,1,7,7],[7,1,1,7],[7,7,7,7]]
    assert evaluator(adapter.program({'tiling':setting}),g)==adapter.family.solve(g,setting)

def test_all_originals(adapter,evaluator):
    c=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['eee78d87']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['eee78d87']
    for p in c['train']+[dict(input=p['input'],output=o) for p,o in zip(c['test'],gold)]:
        assert evaluator(adapter.program({'tiling':'translation'}),p['input'])==p['output']
        assert adapter.family.solve(p['input'],'translation')==p['output']

def test_canonical_bytes_and_resources(adapter,tmp_path):
    assert adapter.program({'tiling':'translation'}).encode()==(HOME/'reference.rkt').read_bytes()
    import shutil
    target=tmp_path/'parametric';shutil.copytree(HOME/'workspace/parametric',target,ignore=shutil.ignore_patterns('__pycache__'))
    standalone=load(target/'adapter.py')
    assert standalone.program({'tiling':'translation'})==adapter.program({'tiling':'translation'})
    assert standalone.generate(17,{'tiling':'translation'},2,4)==adapter.generate(17,{'tiling':'translation'},2,4)

@pytest.mark.parametrize('seed',[0,1,17,31,43])
def test_counts_prefix_matched_inputs_and_identification(adapter,seed):
    lessons=[adapter.generate(seed,{'tiling':s},6,4) for s in adapter.family.SETTINGS]
    for full,s in zip(lessons,adapter.family.SETTINGS):
        inputs=[p['input'] for sp in ('train','test') for p in full[sp]]
        assert len({json.dumps(g) for g in inputs})==10
        for d in range(2,7):
            for q in range(1,5):
                e=adapter.generate(seed,{'tiling':s},d,q)
                assert e['train']==full['train'][:d] and e['test']==full['test'][:q]
        assert all(not all(adapter.family.rival(p['input'],s,r)==p['output'] for p in full['train'][:2]) for r in adapter.family.RIVALS)
        assert any(len(p['output'])==30 and len(p['output'][0])==30 for p in full['test'])
    for sp in ('train','test'): assert [p['input'] for p in lessons[0][sp]]==[p['input'] for p in lessons[1][sp]]

def test_query_order_not_fixed(adapter):
    positions={next(i for i,p in enumerate(adapter.generate(seed,{'tiling':'translation'},2,4)['test']) if len(p['input'])==13) for seed in range(32)}
    assert positions=={0,1,2,3}

def test_projection_private_invariance_and_isolation(adapter):
    e=adapter.generate(17,{'tiling':'translation'},2,4);public=adapter.public_view(e,0)
    changed=copy.deepcopy(e);changed.update(settings={'secret':8},seed=9,program_solution='hidden')
    for p in changed['test']:p['output']=[[8]]
    changed['test'][1:]=[{'input':[[1]],'output':[[2]]}]
    assert adapter.public_view(changed,0)==public
    assert set(public)=={'train','test'} and set(public['test'][0])=={'input'}
    public['train'][0]['input'][0][0]=99
    assert adapter.generate(17,{'tiling':'translation'},2,4)==e

@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(-1,2,4),(2**63,2,4),(0,1,4),(0,7,4),(0,True,4),(0,2,0),(0,2,5),(0,2,1.0)])
def test_invalid_counts(adapter,seed,demos,queries):
    with pytest.raises(ValueError):adapter.generate(seed,{'tiling':'translation'},demos,queries)

@pytest.mark.parametrize('settings',[{}, {'tiling':True},{'tiling':'unknown'},{'tiling':'translation','extra':1}])
def test_settings_fail_closed(adapter,settings):
    with pytest.raises(ValueError):adapter.generate(0,settings,2,4)

@pytest.mark.parametrize('grid',[[],[[7]],[[True,7],[7,1]],[[7,1],[7]],[[10,7],[7,1]]])
def test_bad_grid_rejected(adapter,grid):
    with pytest.raises(ValueError):adapter.family.solve(grid,'translation')


@pytest.mark.parametrize('difficulty',[None,'easy','medium','hard'])
def test_ordinary_generator_protocol(adapter,evaluator,difficulty):
    generator=load(HOME/'generator.py')
    g=generator.generate(17,0,difficulty=difficulty)
    assert type(g) is list and all(type(row) is list for row in g)
    assert g==generator.generate(17,0,difficulty=difficulty)
    assert g!=generator.generate(17,1,difficulty=difficulty)
    assert generator.self_check(g)==[]
    assert generator.rule_mirror(g)==evaluator((HOME/'reference.rkt').read_text(),g)
    assert generator.RULE_TASK_ID=='ee_'+HOME.name.removeprefix('public_eval_')


def test_ordinary_generator_relocated(tmp_path):
    import shutil
    target=tmp_path/'isolated-home';target.mkdir()
    for n in ('generator.py','reference.rkt'):shutil.copy2(HOME/n,target/n)
    shutil.copytree(HOME/'workspace/parametric',target/'workspace/parametric',ignore=shutil.ignore_patterns('__pycache__'))
    original=load(HOME/'generator.py');relocated=load(target/'generator.py')
    assert relocated.generate(43,7,difficulty='hard')==original.generate(43,7,difficulty='hard')
    assert relocated.self_check(relocated.generate(0,0))==[]

@pytest.mark.parametrize('seed,index,difficulty,overrides',[(True,0,None,{}),(0,True,None,{}),(-1,0,None,{}),(0,-1,None,{}),(0,0,'unknown',{}),(0,0,None,{'bogus':1})])
def test_ordinary_generator_rejects_unsupported_controls(seed,index,difficulty,overrides):
    generator=load(HOME/'generator.py')
    with pytest.raises((ValueError,TypeError)):generator.generate(seed,index,difficulty=difficulty,**overrides)
