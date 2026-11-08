import copy
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]
@pytest.fixture(scope="module")
def a():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(), 'native packing adapter is not implemented'
    s=importlib.util.spec_from_file_location('tested_e8686506',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_all_supplied_labels_and_colored_uniqueness(a):
    d=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['e8686506']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['e8686506']
    for split in ('train','test'):
        for i,p in enumerate(d[split]):
            assert a.solve(p['input'],'assemble')==(p['output']if split=='train'else gold[i])
            assert a.color_solution_count(p['input'],limit=2)==1

def test_hand_derived_inventory_placement(a):
    # One rectangular frame, a horizontal green domino, and a red singleton.
    g=[[1,1,1,1,1,0,0,0],[1,0,0,0,1,0,3,3],[1,1,1,1,1,0,0,0],[0,0,0,0,0,0,0,0],[2,0,0,0,0,0,0,0]]
    # Two colored fillings are possible; the API must expose, not hide, this ambiguity.
    assert a.color_solution_count(g,limit=2)==2

def test_no_cover_is_rejected(a):
    g=[[1,1,1,1,0,0],[1,0,0,1,0,0],[1,1,1,1,0,0],[0,0,0,0,0,0],[2,0,0,0,0,0]]
    with pytest.raises(ValueError,match='cover'):a.solve(g,'assemble')

def test_default_exact_source(a):
    assert a.program({'selection':'assemble'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('s',[None,{}, {'selection':'other'},{'selection':True},{'selection':'assemble','extra':1}])
def test_bad_settings(a,s):
    with pytest.raises(ValueError):a.program(s)

@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('demos',True),('demos',1),('demos',7),('queries',0),('queries',5),('queries',1.0)])
def test_bad_requests(a,field,value):
    kw=dict(seed=0,settings={'selection':'assemble'},demos=2,queries=4);kw[field]=value
    with pytest.raises(ValueError):a.generate(**kw)

def test_matched_count_independent_determinism_and_no_mutation(a):
    for seed in (0,17,43):
        ep=a.generate(seed,{'selection':'assemble'},2,4)
        assert ep==a.generate(seed,{'selection':'assemble'},2,4)
        longer=a.generate(seed,{'selection':'assemble'},6,4)
        assert ep['train']==longer['train'][:2] and ep['test']==longer['test']
        other=a.generate(seed,{'selection':'largest_inserted'},2,4)
        for sp in ('train','test'):assert [p['input']for p in ep[sp]]==[p['input']for p in other[sp]]
        before=copy.deepcopy(ep)
        for p in ep['train']+ep['test']:
            assert a.color_solution_count(p['input'],limit=2)==1
            a.solve(p['input'],'assemble')
        assert ep==before
        assert len({json.dumps(p['input'])for p in ep['train']+ep['test']})==6
        for q in range(1,5):assert a.generate(seed,{'selection':'assemble'},2,q)['test']==ep['test'][:q]
        stress=ep['test'][-1]['input'];assert len(stress)==len(stress[0])==30
        bg=a.describe(stress)['background']
        assert sum(v!=bg for row in stress for v in row)>=160
        assert all(any(v!=bg for v in edge)for edge in (stress[0],stress[-1],[r[0]for r in stress],[r[-1]for r in stress]))

def test_public_view_hides_answers_future_and_settings(a):
    ep=a.generate(17,{'selection':'largest_inserted'},2,4);before=a.public_turn(ep,0,presentation_seed=7)
    current=a.query_order(7)[0];ep['settings']={'private':True};ep['seed']=-99;ep['program_solution']='secret'
    for p in ep['train']:p['private']='secret'
    for i,p in enumerate(ep['test']):
        p['output']={'secret':True}
        if i!=current:p['input']='future'
    assert a.public_turn(ep,0,presentation_seed=7)==before
    assert set(before)=={'train','test'} and len(before['test'])==1 and set(before['test'][0])=={'input'}
    assert len({a.query_order(i)[0]for i in range(32)})>1
    with pytest.raises(ValueError):a.public_turn(ep,True)

def test_source_largest_is_not_assembled_largest(a):
    ep=a.generate(17,{'selection':'largest_inserted'},2,4)
    assert any(a.counterfactual(p['input'])!=p['output']for p in ep['train'])

def test_production_api_metadata_and_rejection(a):
    s=importlib.util.spec_from_file_location('ge8tested',HOME/'generator.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
    assert g.GENERATOR_ID=='public_eval_e8686506' and g.AXES=={}
    for i in range(10):assert g.self_check(g.generate(17,i))
    with pytest.raises(ValueError):g.generate(17,0,phantom=3)
    assert not g.self_check([[True]])

def test_all_standalone_programs_execute_through_protected_racket(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert identity['backend']=='racket' and identity['protected'] is True
        g=a.scene(17,0)
        for mode in a.MODES:assert apply(a.program({'selection':mode}),g)==a.solve(g,mode)
        assert apply((HOME/'workspace/parametric/wrong_order.rkt').read_text(),g)==a.counterfactual(g)
    finally:bridge.close()

def test_all_supported_demo_slots_have_unique_colored_filling(a):
    for seed in range(16):
        for i in range(10):assert a.color_solution_count(a.scene(seed,i),limit=2)==1, (seed,i)

def test_mirror_shortcuts_are_taught_in_two_demos(a):
    for seed in range(16):
        ep=a.generate(seed,{'selection':'assemble'},2,4)
        for rival in ('horizontal_flip','vertical_flip'):
            assert any(a.rival(p['input'],rival)!=p['output']for p in ep['train']), (seed,rival)

def test_retained_ambiguous_inventory_is_not_silently_certified(a):
    f=json.loads((HOME/'workspace/parametric/regression-ambiguity.json').read_text())
    assert a.color_solution_count(f['input'],limit=2)==2
    assert f['solutions'][0]!=f['solutions'][1]

def test_reusable_audit_retains_demonstration_only_ambiguity(a):
    s=importlib.util.spec_from_file_location('audite8tested',HOME/'workspace/parametric/audit.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    f=json.loads((HOME/'workspace/parametric/regression-flip.json').read_text())
    findings=m.teaching_failures(a,f['train'],[f['query']])
    assert 'horizontal_flip' in {x['rival']for x in findings}

def test_retained_rival_programs_are_executable_not_just_text(a):
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        g=a.scene(17,0);out=a.solve(g,'assemble')
        assert apply((HOME/'workspace/parametric/mirror_rival.rkt').read_text(),g)==[row[::-1]for row in out]
        assert apply((HOME/'workspace/parametric/reverse_inventory.rkt').read_text(),g)==out
    finally:bridge.close()


def test_witness_serialization_passes_frozen_intake_schema(a):
    # Regression: a full runtime identity in the schema's minimal marker is rejected.
    import hashlib
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    path=HOME/'workspace/parametric/audit.py'
    spec=importlib.util.spec_from_file_location('witness_contract_test_'+HOME.name,path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    assert hasattr(audit,'witness_document'), 'audit lacks schema-safe witness serialization'
    setting={'selection':a.MODES[1]};episode=a.generate(17,setting,2,4)
    pair=next(p for p in episode['train']+episode['test'] if a.counterfactual(p['input'])!=p['output'])
    dep=json.loads((HOME/'workspace/parametric/causal-description.json').read_text())
    identity={'backend':'racket','protected':True,'schema':'arc-protected-racket-runtime-v1','binary_sha256':'a'*64}
    binding={'task_id':HOME.name,'files':[]}
    case={'input':pair['input'],'settings':setting,'intermediate_value':a.causal_intermediate(pair['input']),
          'output':pair['output'],'program':episode['program_solution'],
          'counterfactual_output':a.counterfactual(pair['input']),
          'counterfactual_program':(HOME/'workspace/parametric/wrong_order.rkt').read_text(),'ablation':'wrong_order'}
    before=copy.deepcopy((binding,dep,identity,case))
    witness=audit.witness_document(binding,dep,identity,[case])
    key=json.dumps(setting,sort_keys=True,separators=(',',':'))
    qualification={'source_binding':binding,'programs':{key:hashlib.sha256(case['program'].encode()).hexdigest()}}
    result=validate_sequential_witness({'sequential_dependency':{**dep,'witness_path':'witness.json'}},qualification,
                                     lambda _:json.dumps(witness).encode())
    assert result['status']=='source_bound_reviewer_reported' and result['cases']==1
    assert witness['runtime_identity']==identity
    assert (binding,dep,identity,case)==before
    with pytest.raises(ValueError):audit.witness_document(binding,dep,{**identity,'protected':False},[case])
