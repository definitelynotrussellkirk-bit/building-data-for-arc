from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

TASK='public_eval_97d7923e'
ROOT=Path(__file__).resolve().parents[3]
if not (ROOT/'shared/runtime').is_dir():
    raise FileNotFoundError(f'No copied repository/runtime root for {__file__}')
HOME=ROOT/'generators'/TASK


def load(path, tag='module'):
    assert path.is_file(), f'Missing implementation: {path}'
    name='_p97d_'+tag+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def adapter(): return load(HOME/'workspace/parametric/adapter.py','adapter')


@pytest.fixture(scope='module')
def engine(): return load(HOME/'workspace/parametric/engine.py','engine')


def originals():
    raw=ROOT/'shared/data/raw'
    item=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['97d7923e']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['97d7923e']
    return item['train']+[dict(input=p['input'],output=o) for p,o in zip(item['test'],gold)]


def test_reference_and_native_copy_exist():
    assert (HOME/'reference.rkt').is_file()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()


@pytest.mark.parametrize('index',range(4))
def test_all_original_python_labels(engine,index):
    pair=originals()[index]
    assert engine.solve(pair['input'],'rank_only')==pair['output']


def test_all_original_protected_racket_labels():
    from arcpuzzles.parametric_worker import _real_evaluator
    import arc_repl.racket_bridge as racket_bridge
    runtime=Path(racket_bridge.__file__).resolve().parents[1]
    apply,identity,bridge=_real_evaluator(runtime)
    try:
        assert identity['backend']=='racket' and identity['protected']
        program=(HOME/'reference.rkt').read_text()
        for pair in originals(): assert apply(program,pair['input'])==pair['output']
    finally: bridge.close()


@pytest.mark.parametrize('seed',[0,1,17,43,127,2**63-1])
def test_counts_prefixes_matched_inputs_and_stress(adapter,seed):
    base=adapter.generate(seed,{'relay_mode':'rank_only'},6,4)
    relay=adapter.generate(seed,{'relay_mode':'selected_longest'},6,4)
    inputs=lambda e:[p['input'] for split in ('train','test') for p in e[split]]
    assert inputs(base)==inputs(relay)
    assert len({json.dumps(g,separators=(',',':')) for g in inputs(base)})==10
    for setting,episode in [('rank_only',base),('selected_longest',relay)]:
        for d in range(2,7):
            sub=adapter.generate(seed,{'relay_mode':setting},d,4)
            assert sub['train']==episode['train'][:d] and sub['test']==episode['test']
        for q in range(1,5):
            assert adapter.generate(seed,{'relay_mode':setting},2,q)['test']==episode['test'][:q]
        assert episode['program_solution']==adapter.program({'relay_mode':setting})
    assert any(a['output']!=b['output'] for a,b in zip(base['train'][:2],relay['train'][:2]))
    assert all(a['output']!=b['output'] for a,b in zip(base['test'],relay['test']))
    q=relay['test'][-1]
    assert len(q['input'])==len(q['output'])==30
    assert len(q['input'][0])==len(q['output'][0])==30
    assert sum(v!=0 for row in q['input'] for v in row)>=120
    assert sum(a!=b for ra,rb in zip(q['input'],q['output']) for a,b in zip(ra,rb))>=20


@pytest.mark.parametrize('setting',['rank_only','selected_longest'])
def test_two_demo_prefix_refutes_all_declared_rivals(adapter,engine,setting):
    for seed in range(16):
        ep=adapter.generate(seed,{'relay_mode':setting},2,4)
        for rival in engine.RIVALS:
            assert any(engine.solve(p['input'],setting,rival)!=p['output'] for p in ep['train']), (seed,setting,rival)


@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(-1,2,4),(2**63,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,False),(0,2,0),(0,2,5)])
def test_invalid_counts(adapter,seed,demos,queries):
    with pytest.raises(ValueError): adapter.generate(seed,{'relay_mode':'rank_only'},demos,queries)


@pytest.mark.parametrize('settings',[{},None,{'relay_mode':'bad'},{'relay_mode':True},{'relay_mode':'rank_only','extra':0}])
def test_invalid_settings(adapter,settings):
    with pytest.raises(ValueError): adapter.program(settings)


def test_public_projection_is_shuffled_private_and_count_independent(adapter):
    first_positions=set()
    for seed in range(24):
        full=adapter.present(seed,{'relay_mode':'rank_only'},2,4,presentation_seed=7)
        one=adapter.present(seed,{'relay_mode':'rank_only'},2,1,presentation_seed=7)
        assert one['public']==full['public'][:1]
        first_positions.add(full['private']['source_indices'][0])
        for view in full['public']:
            assert set(view)=={'train','test'} and len(view['test'])==1
            assert set(view['test'][0])=={'input'}
        altered=deepcopy(full)
        altered['private']['settings']={'secret':True};altered['private']['program']='secret'
        for p in altered['private']['source_pairs']: p['output']=[[9]]
        assert full['public']==adapter.present(seed,{'relay_mode':'rank_only'},2,4,presentation_seed=7)['public']
    assert len(first_positions)>1


def test_native_resources_survive_relocation(adapter,tmp_path):
    source=HOME/'workspace/parametric'
    for name in ('adapter.py','engine.py','canonical.rkt'):
        shutil.copy2(source/name,tmp_path/name)
    moved=load(tmp_path/'adapter.py','relocated')
    assert moved.generate(17,{'relay_mode':'rank_only'},2,4)==adapter.generate(17,{'relay_mode':'rank_only'},2,4)


@pytest.mark.parametrize('bad',[[],[[True]],[[0,1],[0]],[[10]],[[0]*31],[[1]*31 for _ in range(10)]])
def test_bad_grids_are_rejected(engine,bad):
    assert engine.self_check(bad)
    with pytest.raises((ValueError,TypeError,IndexError)): engine.solve(bad,'rank_only')


def test_stage_b_consumes_stage_a_and_racket_counterfactual(adapter,engine):
    from arcpuzzles.parametric_worker import _real_evaluator
    pair=adapter.generate(17,{'relay_mode':'selected_longest'},2,4)['test'][0]
    state=adapter.intermediate(pair['input'],{'relay_mode':'selected_longest'})
    assert state['selected_wires'] and state['winner_color'] is not None
    assert state['raw_longest_color']!=state['winner_color']
    wrong=engine.solve(pair['input'],'selected_longest','relay_longest_candidate')
    assert wrong!=pair['output']
    import arc_repl.racket_bridge as racket_bridge
    runtime=Path(racket_bridge.__file__).resolve().parents[1]
    apply,_,bridge=_real_evaluator(runtime)
    try:
        assert apply(adapter.program({'relay_mode':'selected_longest'}),pair['input'])==pair['output']
        assert apply(adapter.counterfactual_program({'relay_mode':'selected_longest'}),pair['input'])==wrong
    finally: bridge.close()


def test_ordinary_generator_contract_and_rule_mirror():
    gen=load(HOME/'generator.py','generator')
    for difficulty,index in [(None,0),('medium',1),('hard',3)]:
        g=gen.generate(seed=29,sample_index=index,difficulty=difficulty)
        assert gen.self_check(g)==[]
        assert gen.rule_mirror(g)==load(HOME/'workspace/parametric/engine.py','ordinary_engine').solve(g,'rank_only')
    with pytest.raises(ValueError): gen.generate(seed=0,sample_index=0,difficulty='impossible')


def test_self_audit_cli_is_directly_runnable():
    script=HOME/'workspace/parametric/self_audit.py'
    env=dict(os.environ);env.pop('PYTHONPATH',None)
    completed=subprocess.run([sys.executable,str(script),'--help'],cwd=ROOT,env=env,text=True,capture_output=True,timeout=30,check=False)
    assert completed.returncode==0, completed.stderr
    assert 'usage:' in completed.stdout.lower()
    code=f"import runpy; m=runpy.run_path({str(script)!r},run_name='_audit_smoke'); import arcpuzzles.parametric_worker; print(m['TASK'])"
    imported=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=env,text=True,capture_output=True,timeout=30,check=False)
    assert imported.returncode==0, imported.stderr
    assert imported.stdout.strip()==HOME.name
