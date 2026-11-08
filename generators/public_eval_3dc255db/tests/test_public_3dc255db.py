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
    spec = importlib.util.spec_from_file_location("tested_3dc255db", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def test_original_labels(a):
    data = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["3dc255db"]
    gold = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["3dc255db"]
    for split in ("train", "test"):
        for i,p in enumerate(data[split]):
            assert a.solve(p["input"], "all_rays") == (p["output"] if split == "train" else gold[i])

def test_default_exact_source(a):
    assert a.program({"selection":"all_rays"}) == (HOME/"reference.rkt").read_text()
    assert (HOME/"reference.rkt").read_bytes() == (HOME/"workspace/parametric/canonical.rkt").read_bytes()

@pytest.mark.parametrize("s", [None, {}, {"selection":"bad"}, {"selection":True}, {"selection":"all_rays","extra":1}])
def test_bad_settings(a,s):
    with pytest.raises(ValueError):a.program(s)

@pytest.mark.parametrize("field,value", [("seed",True),("seed",-1),("demos",1),("demos",7),("queries",0),("queries",5),("queries",1.0)])
def test_bad_request(a,field,value):
    kw=dict(seed=0,settings={"selection":"all_rays"},demos=2,queries=4);kw[field]=value
    with pytest.raises(ValueError):a.generate(**kw)

def test_matched_streams_prefixes_and_boundary(a):
    for seed in (0,17,43):
        short=a.generate(seed,{"selection":"all_rays"},2,4)
        assert short==a.generate(seed,{"selection":"all_rays"},2,4)
        assert short['train']==a.generate(seed,{"selection":"all_rays"},6,4)['train'][:2]
        other=a.generate(seed,{"selection":"longest_visible"},2,4)
        for sp in ('train','test'):assert [p['input']for p in short[sp]]==[p['input']for p in other[sp]]
        for n in (1,2,3,4):assert a.generate(seed,{"selection":"all_rays"},2,n)['test']==short['test'][:n]
        inputs=[p['input']for sp in ('train','test')for p in short[sp]]
        assert len({json.dumps(g)for g in inputs})==6
        g=short['test'][-1]['input'];assert len(g)==len(g[0])==30
        assert sum(v!=0 for row in g for v in row)>60

def test_public_projection_private_invariance(a):
    ep=a.generate(17,{'selection':'longest_visible'},2,4)
    original=a.public_turn(ep,0,presentation_seed=7)
    changed=copy.deepcopy(ep);changed['settings']={'secret':99};changed['program_solution']='secret';changed['seed']=999
    for p in changed['train']:p['private']='secret'
    for p in changed['test']:p['output']=[[9]];p['private']='secret'
    assert a.public_turn(changed,0,presentation_seed=7)==original
    assert set(original)=={'train','test'} and len(original['test'])==1 and set(original['test'][0])=={'input'}
    assert {a.query_order(s)[0] for s in range(64)}=={0,1,2,3}

def test_wrong_intermediate_changes_constructive_case(a):
    ep=a.generate(17,{'selection':'longest_visible'},2,4)
    assert any(a.counterfactual(p['input'])!=p['output']for p in ep['train']+ep['test'])
    info=a.causal_intermediate(ep['train'][0]['input'])
    assert info['selected_index'] != info['pre_ejection_selected_index']
    assert info['visible_lengths'][info['selected_index']]==max(info['visible_lengths'])

def test_ship_direction_and_clipping_literals(a):
    g=a.scene(5,0)
    desc=a.descriptors(g)
    assert len(desc)>=2 and all(d['payload_count']>0 for d in desc)
    out=a.solve(g,'all_rays')
    for d in desc:
        assert all(out[r][c]==d['payload_color'] for r,c in d['ray_cells'])
        assert all(out[r][c]==0 for r,c in d['payload_cells'])

def test_two_demo_teaching_refutes_declared_rivals(a):
    for seed in range(16):
        for mode in a.MODES:
            ep=a.generate(seed,{'selection':mode},2,4)
            for rival in a.RIVALS:
                if all(a.rival(p['input'],rival)==p['output'] for p in ep['train']):
                    assert all(a.rival(p['input'],rival)==p['output'] for p in ep['test'])

def test_production_api_metadata_and_rejection(a):
    spec=importlib.util.spec_from_file_location('g3dc',HOME/'generator.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    assert g.RULE_TASK_ID=='ee_3dc255db' and g.AXES=={}
    for i in range(10):assert g.self_check(g.generate(17,i))==[]
    with pytest.raises(ValueError):g.generate(17,0,imaginary=1)
    assert g.self_check([[True]])
