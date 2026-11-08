"""Public-parent and constructed-family regressions (author-private gold)."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]

def load(name):
    path = HOME / 'workspace/parametric' / (name + '.py')
    assert path.is_file(), f'missing implementation {path.name}'
    spec = importlib.util.spec_from_file_location('_t221_' + name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def official():
    return json.loads((HOME/'tests/fixtures/official.json').read_text())

def test_reference_exists():
    assert (HOME/'reference.rkt').is_file(), 'general canonical Racket rule is missing'

@pytest.mark.parametrize('split,index', [('train',0),('train',1),('test',0),('test',1)])
def test_original_python_labels(official, split, index):
    family = load('family')
    p = official[split][index]
    assert family.solve(p['input'], 'slice') == p['output']

def test_original_protected_racket_labels(official):
    assert (HOME/'reference.rkt').is_file(), 'general canonical Racket rule is missing'
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    root = find_root(__file__)
    apply, identity, bridge = _real_evaluator(root/'shared/runtime')
    try:
        assert identity['backend'] == 'racket' and identity['protected']
        for pairs in official.values():
            for p in pairs:
                assert apply((HOME/'reference.rkt').read_text(),p['input']) == p['output']
    finally:
        bridge.close()

def test_component_extension_selects_objects_not_color():
    family = load('family')
    g = [[8]*14 for _ in range(12)]
    g[0][5:8] = [4]*3
    for r,c in [(3,0),(4,0),(5,0),(5,1),(6,2),(7,1),(8,1)]: g[r][c] = 2
    out = family.solve(g, 'component')
    assert [out[r][c] for r,c in [(3,0),(4,0),(5,0),(5,1)]] == [3]*4
    assert [out[r][c] for r,c in [(6,2),(7,1),(8,1)]] == [2]*3
    assert out[4][2] == 8  # no filling a background gap
    assert family.solve(g, 'slice')[3][0] == 2

@pytest.mark.parametrize('seed', [0,17,43])
def test_counts_matched_inputs_and_distinct_queries(seed):
    adapter = load('adapter')
    for demos in (2,3,6):
        episodes = [adapter.generate(seed, {'extension':s}, demos, 4) for s in ('slice','component')]
        for e in episodes:
            assert len(e['train']) == demos and len(e['test']) == 4
            grids = [p['input'] for k in ('train','test') for p in e[k]]
            assert len({json.dumps(g) for g in grids}) == len(grids)
            stress=next(p['input'] for p in e['test'] if len(p['input'])==len(p['input'][0])==30)
            assert sum(v != load('family').frame(stress)['bg']
                       for row in stress for v in row) >= 100
        assert [[p['input'] for p in e['train']+e['test']] for e in episodes][0] == [p['input'] for p in episodes[1]['train']+episodes[1]['test']]
        assert any(a['output'] != b['output'] for a,b in zip(episodes[0]['train'],episodes[1]['train']))

@pytest.mark.parametrize('bad', [True,1.5,'2',-1,None])
def test_strict_seed_rejection(bad):
    with pytest.raises(ValueError): load('adapter').generate(bad, {'extension':'slice'},2,4)

@pytest.mark.parametrize('field,bad', [('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',2.0)])
def test_strict_count_rejection(field,bad):
    args = dict(seed=0, settings={'extension':'slice'}, demos=2, queries=4)
    args[field] = bad
    with pytest.raises(ValueError): load('adapter').generate(**args)

@pytest.mark.parametrize('settings', [{},{'extension':'other'},{'extension':True},{'extension':'slice','x':1},None])
def test_strict_settings_rejection(settings):
    with pytest.raises(ValueError): load('adapter').program(settings)

def test_default_program_and_prefix_public_privacy():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    from copy import deepcopy
    a = load('adapter')
    assert a.program({'extension':'slice'}) == (HOME/'reference.rkt').read_text()
    full = a.generate(43, {'extension':'component'},2,4)
    short = a.generate(43, {'extension':'component'},2,1)
    assert short['test'] == full['test'][:1]
    assert short['private_query_bank'] == full['test']
    orders = {tuple(a.presentation_order(s)) for s in range(24)}
    assert len({o[0] for o in orders}) == 4
    for seed in range(4):
        i = a.presentation_order(seed)[0]
        view = a.public_view(full,i)
        assert a.public_view(short,i) == view
        assert set(view)=={'train','test'} and len(view['test'])==1
        assert set(view['test'][0])=={'input'}
        hidden = deepcopy(full)
        hidden.update(seed=999,settings={'secret':True},program_solution='not a program')
        for p in hidden['test']: p['output'] = [[9]]
        assert a.public_view(hidden,i) == view
        assert public_challenge_bytes(view) == public_challenge_bytes(a.public_view(full,i))
        assert len(public_challenge_id(view)) == 64


def test_generated_protected_racket_all_sides():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a, f = load('adapter'), load('family')
    apply, _, bridge = _real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        for side in range(4):
            g = f.sample(73, side, 14, 16, side=side)
            for setting in ('slice','component'):
                assert apply(a.program({'extension':setting}),g) == f.solve(g,setting)
    finally:
        bridge.close()


def test_generator_public_api_strict():
    path=HOME/'generator.py'
    assert path.is_file(), 'canonical generator missing'
    spec=importlib.util.spec_from_file_location('_g221', path)
    gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
    g=gen.generate(4,0,height=30,width=30,side=3)
    assert len(g)==30 and len(g[0])==30 and not gen.self_check(g)
    assert gen.observe_overrides(g)=={'height':30,'width':30,'side':3}
    for kwargs in ({'height':True},{'width':'20'},{'side':4},{'nonsense':2}):
        with pytest.raises(ValueError):gen.generate(0,0,**kwargs)


def test_finite_rivals_are_refuted_by_two_demos():
    a, rivals = load('adapter'), load('rivals')
    for seed in range(8):
        for setting in ('slice','component'):
            e=a.generate(seed,{'extension':setting},2,4)
            candidates=set(rivals.predict(e['train'][0]['input'],setting))
            for p in e['train']:
                outputs=rivals.predict(p['input'],setting)
                candidates={name for name in candidates if outputs[name]==p['output']}
            assert not candidates, (seed,setting,candidates)


def test_causal_wrong_component_mask_changes_output():
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    a = load('adapter')
    assert hasattr(a, 'counterfactual_program'), 'causal ablation must be executable'
    p=next(p for p in a.generate(17,{'extension':'component'},2,4)['test']
           if len(p['input'])==len(p['input'][0])==30)
    apply,_,bridge=_real_evaluator(find_root(__file__)/'shared/runtime')
    try:
        assert apply(a.counterfactual_program(),p['input']) != p['output']
    finally: bridge.close()


def test_audit_runner_emits_valid_public_only_files(tmp_path):
    audit = load('audit')
    report = audit.run_audit(tmp_path/'audit', seeds=[0], racket_seeds=[])
    assert report['status']=='passed' and report['findings']==[]
    assert report['episodes']==6
    assert report['public_turns']==8
    for p in (tmp_path/'audit/public').glob('*.json'):
        v=json.loads(p.read_text())
        assert set(v)=={'train','test'} and len(v['test'])==1
        assert set(v['test'][0])=={'input'}


def test_generator_is_self_contained_when_only_generator_is_relocated(tmp_path):
    """The ordinary owner runtime maps generator.py, not task workspaces."""
    import os
    import shutil
    import subprocess
    from reviewer_support import find_root
    shutil.copy2(HOME/'generator.py', tmp_path/'generator.py')
    program = """import json, generator
g = generator.generate(29, 3, height=14, width=16)
assert not generator.self_check(g)
print(json.dumps({'shape': [len(g), len(g[0])], 'output': generator.rule_mirror(g)}))
""".replace('14',str(14)).replace('16',str(16))
    env = dict(os.environ, PYTHONPATH=str(find_root(__file__)/'shared/runtime'),
               PYTHONDONTWRITEBYTECODE='1')
    proc=subprocess.run([sys.executable,'-c',program],cwd=tmp_path,env=env,
                        text=True,capture_output=True,timeout=30)
    assert proc.returncode==0, proc.stderr
    result=json.loads(proc.stdout)
    assert result['shape']==[14,16]
    assert len(result['output'])==14
