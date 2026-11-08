import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

@pytest.fixture(scope="module")
def a():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "native adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("tested_71e489b6", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def test_original_labels(a):
    data = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["71e489b6"]
    gold = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["71e489b6"]
    for split in ("train", "test"):
        for i,p in enumerate(data[split]):
            assert a.solve(p["input"], "all_rims") == (p["output"] if split == "train" else gold[i])

def test_literal_single_hole_and_no_mutation(a):
    g=[[1,1,1,1,1],[1,1,1,1,1],[1,1,0,1,1],[1,1,1,1,1],[1,1,1,1,1]]
    before=copy.deepcopy(g)
    assert a.solve(g,"all_rims")==[[1,1,1,1,1],[1,7,7,7,1],[1,7,0,7,1],[1,7,7,7,1],[1,1,1,1,1]]
    assert g==before

def test_solid_zero_cavity_not_a_thin_defect(a):
    g=[[1]*8 for _ in range(8)]
    for r in range(2,6):
        for c in range(2,6):g[r][c]=0
    assert a.solve(g,"all_rims")==g

def test_default_exact_source(a):
    assert a.program({"selection":"all_rims"})==(HOME/"reference.rkt").read_text()
    assert (HOME/"reference.rkt").read_bytes()==(HOME/"workspace/parametric/canonical.rkt").read_bytes()

@pytest.mark.parametrize("s",[None,{}, {"selection":"invalid"},{"selection":True},{"selection":"all_rims","extra":1}])
def test_bad_settings(a,s):
    with pytest.raises(ValueError):a.program(s)

@pytest.mark.parametrize("field,value",[("seed",True),("seed",-1),("demos",True),("demos",1),("demos",7),("queries",0),("queries",5),("queries",1.0)])
def test_bad_request(a,field,value):
    kw=dict(seed=0,settings={"selection":"all_rims"},demos=3,queries=4);kw[field]=value
    with pytest.raises(ValueError):a.generate(**kw)

def test_matched_streams_prefixes_and_boundary(a):
    for seed in (0,17,43):
        short=a.generate(seed,{"selection":"all_rims"},3,4)
        assert short==a.generate(seed,{"selection":"all_rims"},3,4)
        long=a.generate(seed,{"selection":"all_rims"},6,4)
        assert short['train']==long['train'][:3] and short['test']==long['test']
        other=a.generate(seed,{"selection":"largest_rim"},3,4)
        for sp in ('train','test'):assert [p['input']for p in short[sp]]==[p['input']for p in other[sp]]
        for n in (1,2,3,4):assert a.generate(seed,{"selection":"all_rims"},3,n)['test']==short['test'][:n]
        inputs=[p['input']for sp in ('train','test')for p in short[sp]]
        assert len({json.dumps(g)for g in inputs})==7
        g=short['test'][-1]['input'];assert len(g)==len(g[0])==30
        assert sum(v!=0 for row in g for v in row)>600

def test_public_projection_private_invariance(a):
    ep=a.generate(17,{'selection':'largest_rim'},3,4)
    original=a.public_turn(ep,0,presentation_seed=7)
    changed=copy.deepcopy(ep);changed['settings']={'secret':99};changed['program_solution']='secret';changed['seed']=999
    for p in changed['train']:p['private']='secret'
    for p in changed['test']:p['output']=[[9]];p['private']='secret'
    assert a.public_turn(changed,0,presentation_seed=7)==original
    assert set(original)=={'train','test'} and len(original['test'])==1 and set(original['test'][0])=={'input'}
    seen={json.dumps(a.public_turn(ep,0,presentation_seed=s)['test'][0]['input'])for s in range(32)}
    assert len(seen)>1
    with pytest.raises(ValueError):a.public_turn(ep,True)

def test_wrong_selection_changes_constructive_case(a):
    ep=a.generate(17,{'selection':'largest_rim'},3,4)
    assert any(a.counterfactual(p['input'])!=p['output']for p in ep['train']+ep['test'])

def test_two_demo_support(a):
    assert len(a.generate(0,{'selection':'all_rims'},2,4)['train'])==2

def test_cell_count_tie_not_bbox_area(a):
    g=[[1]*15 for _ in range(15)]
    for r,c in [(3,3),(3,6)]+[(9,c)for c in range(3,8)]:g[r][c]=0
    out=a.solve(g,'largest_rim')
    assert {(r,c)for r in range(15)for c in range(15)if out[r][c]==7}=={
        (2,2),(2,3),(2,4),(2,5),(2,6),(2,7),(3,2),(3,4),(3,5),(3,7),
        (4,2),(4,3),(4,4),(4,5),(4,6),(4,7)}
    assert a.rival(g,'largest_bbox')!=out

def test_future_queries_and_answer_changes_do_not_change_current_turn(a):
    ep=a.generate(43,{'selection':'all_rims'},3,4);before=a.public_turn(ep,0,presentation_seed=3)
    current=a.query_order(3)[0]
    for i,p in enumerate(ep['test']):
        p['output']=[[9]]
        if i!=current:p['input']=[[8]]
    assert a.public_turn(ep,0,presentation_seed=3)==before
    with pytest.raises(ValueError):a.public_turn(a.generate(43,{'selection':'all_rims'},3,1),0)

def test_teaching_audit_exposes_fitting_wrong_rule(a):
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(), 'reusable audit is missing'
    s=importlib.util.spec_from_file_location('audit71tested',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    g=[[1]*5 for _ in range(5)];g[2][2]=0
    train=[{'input':g,'output':a.solve(g,'largest_rim')}]
    test=a.generate(17,{'selection':'largest_rim'},2,4)['test']
    findings=m.teaching_failures(a,train,test)
    assert 'largest_defect_first' in {x['rival']for x in findings}

def test_sampler_covers_parent_scale_and_both_field_balances(a):
    scenes=[a.scene(17,i)for i in range(10)]
    assert min(len(g)for g in scenes)<=16
    assert any(sum(x==0 for row in g for x in row)>len(g)*len(g[0])/2 for g in scenes)

def test_production_api_metadata_and_rejection():
    s=importlib.util.spec_from_file_location('g71tested',HOME/'generator.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
    assert g.GENERATOR_ID=='public_eval_71e489b6'
    assert g.AXES=={} and isinstance(g.INVARIANTS,list) and g.SUMMARY
    for i in range(10):assert g.self_check(g.generate(17,i)) == []
    with pytest.raises(ValueError):g.generate(17,0,imaginary=1)
    assert isinstance(g.self_check([[True]]), list) and g.self_check([[True]])

def test_cardinal_vs_diagonal_is_taught_in_two_demos(a):
    for seed in range(32):
        ep=a.generate(seed,{'selection':'largest_rim'},2,4)
        assert any(a.rival(p['input'],'eight_connected_largest')!=p['output']for p in ep['train'])


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


def test_smallest_rim_selects_after_outlines_merge(a):
    assert 'smallest_rim' in a.MODES, 'complementary smallest-rim setting is missing'
    g=[[1]*15 for _ in range(15)]
    # Two single-cell defects make a merged 16-cell rim; a later solitary defect has 8.
    for r,c in ((3,3),(3,6),(10,10)):g[r][c]=0
    before=copy.deepcopy(g)
    out=a.solve(g,'smallest_rim')
    assert {(r,c) for r,row in enumerate(out) for c,v in enumerate(row) if v==7} == {
        (9,9),(9,10),(9,11),(10,9),(10,11),(11,9),(11,10),(11,11)}
    assert g==before
    assert a.program({'selection':'smallest_rim'}) != a.program({'selection':'all_rims'})


def test_smallest_rim_row_major_ties_and_empty_result(a):
    assert 'smallest_rim' in a.MODES
    g=[[1]*10 for _ in range(10)];g[2][2]=0;g[7][7]=0
    out=a.solve(g,'smallest_rim')
    assert out[1][1]==7 and out[6][6]==1
    assert a.solve([[1]*5 for _ in range(5)],'smallest_rim')==[[1]*5 for _ in range(5)]


def test_smallest_rim_two_demos_defeat_position_shortcuts(a):
    assert 'smallest_rim' in a.MODES
    for seed in range(32):
        episode=a.generate(seed,{'selection':'smallest_rim'},2,4)
        for name in ('first_rim','last_rim','all_rims','largest_rim'):
            assert any(a.rival(p['input'],name)!=p['output'] for p in episode['train']), (seed,name)


def test_base_self_check_follows_findings_contract_without_mutation():
    s=importlib.util.spec_from_file_location('g71findings',HOME/'generator.py')
    g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
    valid=g.generate(17,0);before=copy.deepcopy(valid)
    assert g.self_check(valid)==[], 'worker requires [] for a valid sample, not True'
    assert valid==before
    for bad in ([[True]], [[1,0],[1]], [], [[1]*5 for _ in range(5)]):
        findings=g.self_check(bad)
        assert isinstance(findings,list) and findings
