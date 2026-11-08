from pathlib import Path
import importlib.util
import json
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def load(name):
    path=HOME / name
    assert path.is_file(), f'missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location('_water_'+path.stem, path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('i', range(4))
def test_official_labels(i):
    m=load('generator.py')
    p=ROOT/'shared/data/raw'
    data=json.loads((p/'arc-agi_evaluation_challenges.json').read_text())['28a6681f']
    gold=json.loads((p/'arc-agi_evaluation_solutions.json').read_text())['28a6681f']
    pair=(data['train']+[{'input':data['test'][0]['input'],'output':gold[0]}])[i]
    assert m.solve(pair['input'])==pair['output']

def test_nearest_descent_tie_is_left_and_solid_is_fixed():
    m=load('generator.py')
    g=[[0,1,0,0,0],[0,2,0,0,0],[2,2,0,2,2],[2,2,2,2,2]]
    assert m.solve(g)==[[0,0,0,0,0],[1,2,0,0,0],[2,2,0,2,2],[2,2,2,2,2]]

def test_largest_pool_counts_after_gravity():
    m=load('generator.py')
    g=[[1,0,2,1,1],[0,0,2,0,0],[2,2,2,2,2]]
    assert m.solve(g,'largest_pool')==[[0,0,2,0,0],[0,0,2,1,1],[2,2,2,2,2]]

def test_contract_and_all_supported_counts():
    a=load('workspace/parametric/adapter.py')
    assert a.program({'mode':'settle'})==(HOME/'reference.rkt').read_text()
    for seed in (0,17,43):
        bank=None
        for n in range(3,7):
            e=a.generate(seed,{'mode':'settle'},n,4)
            f=a.generate(seed,{'mode':'largest_pool'},n,4)
            assert len(e['train'])==n and len(e['test'])==4
            assert [p['input']for s in ('train','test')for p in e[s]]==[p['input']for s in ('train','test')for p in f[s]]
            ids=[json.dumps(p['input'])for s in ('train','test')for p in e[s]]
            assert len(set(ids))==len(ids)
            assert bank is None or e['test']==bank
            bank=e['test']
            assert len(bank[-1]['input'])==len(bank[-1]['input'][0])==30
            for mode,ep in [('settle',e),('largest_pool',f)]:
                assert a.teaching_audit(ep,mode)['query_disagreeing_survivors']==[]

@pytest.mark.parametrize('args',[(True,{'mode':'settle'},3,4),(0,{'mode':'settle'},2,4),(0,{'mode':'settle'},3,3),(0,{'mode':'other'},3,4),(0,{'mode':'settle','extra':1},3,4)])
def test_invalid_requests_fail_closed(args):
    with pytest.raises(ValueError):load('workspace/parametric/adapter.py').generate(*args)

def test_each_racket_source_is_one_balanced_rule():
    from puzzle_generators.rule_wrap import strip_rule_wrapper, strip_line_comments
    paths=[HOME/'reference.rkt', *sorted((HOME/'workspace/parametric').glob('*.rkt'))]
    for path in paths:
        assert strip_rule_wrapper(strip_line_comments(path.read_text())).lstrip().startswith('(lambda')

def test_volume_solids_idempotence_across_generated_terrains():
    m=load('generator.py')
    for seed in range(16):
        g=m.generate(seed,seed,difficulty='hard')
        out=m.solve(g)
        assert sum(r.count(1)for r in g)==sum(r.count(1)for r in out)
        assert all(out[r][c]==v for r,row in enumerate(g)for c,v in enumerate(row)if v not in (0,1))
        assert m.solve(out)==out
        assert not m.self_check(g)

def test_public_turn_hides_private_and_future_fields():
    a=load('workspace/parametric/adapter.py');t=load('workspace/parametric/audit.py')
    ep=a.generate(0,{'mode':'settle'},3,4)
    original=t.turn_bytes(ep,0)
    ep['settings']={'secret':True};ep['program_solution']='secret'
    ep['train'][0]['private']='secret';ep['test'][0]['output']=[[9]]
    ep['test'][1]['input']=[[7]]
    assert t.turn_bytes(ep,0)==original
    assert set(json.loads(original))=={'train','test'}
    assert len(json.loads(original)['test'])==1

def test_seed25_lesson_rejects_eight_connected_pool_shortcut():
    a=load('workspace/parametric/adapter.py')
    ep=a.generate(25,{'mode':'largest_pool'},3,4)
    assert 'eight_connected_pool' not in a.teaching_audit(ep,'largest_pool')['survivors']


def test_witness_serializer_meets_native_return_contract():
    from hashlib import sha256
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    t=load('workspace/parametric/audit.py')
    assert callable(getattr(t,'make_witness',None)), 'missing contract-aware witness serializer'
    # Literal one-cell programs: structural-schema unit test, not a qualification.
    program='(rule! (lambda (g) (recolor g 0 1)))'
    case={'settings':{'mode':'unit'},'input':[[0]],'output':[[1]],'counterfactual_output':[[0]],
          'program':program,'counterfactual_program':'(rule! (lambda (g) g))',
          'intermediate_value':0,'ablation':'skip_a'}
    preflight={'source_binding':{'task_id':'unit','files':[]},'programs':{
        '{"mode":"unit"}':sha256(program.encode()).hexdigest()}}
    identity={'backend':'racket','protected':True,'binary_sha256':'full-identity-retained'}
    description={'step_a':'Read input color','intermediate':'Color zero','step_b':'Recolor to one',
                 'why_b_depends_on_a':'Illustrative schema fixture only'}
    w=t.make_witness(preflight,identity,description,case)
    progress={'sequential_dependency':{**description,'witness_path':'unit.json'}}
    checked=validate_sequential_witness(progress,preflight,lambda path:json.dumps(w).encode())
    assert checked['status']=='source_bound_reviewer_reported'
    assert w['racket_identity']==identity
