from pathlib import Path
import importlib.util
import json
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def engine():
    path=HOME/'workspace/parametric/family.py'
    assert path.exists(), 'family implementation is missing'
    spec=importlib.util.spec_from_file_location('cut_family_test',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def test_all_original_labels():
    m=engine(); data=ROOT/'shared/data/raw'
    p=json.loads((data/'arc-agi_evaluation_challenges.json').read_text())['4a21e3da']
    gold=json.loads((data/'arc-agi_evaluation_solutions.json').read_text())['4a21e3da']
    for pair in p['train']:
        assert m.solve(pair['input'],'all')==pair['output']
    for pair,out in zip(p['test'],gold):
        assert m.solve(pair['input'],'all')==out

def test_hand_single_cut_keeps_ray_pixels_and_docks_groups():
    m=engine()
    g=[[1]*9 for _ in range(8)]
    g[0][4]=2
    for r,c in [(2,2),(3,2),(4,3),(2,4),(4,4),(3,6),(4,6),(4,7)]:g[r][c]=7
    want=[[1]*9 for _ in range(8)]
    for r in [0,1,3]:want[r][4]=2
    for r,c in [(2,4),(4,4),(0,0),(1,0),(2,1),(0,7),(1,7),(1,8)]:want[r][c]=7
    assert m.solve(g,'all')==want

def test_two_edge_markers_delete_unmarked_corner_sector():
    m=engine();g=[[1]*11 for _ in range(11)];g[0][5]=2;g[5][10]=2
    for r,c in [(3,3),(3,7),(7,3),(7,7),(4,5),(6,5),(5,4),(5,6)]:g[r][c]=7
    out=m.solve(g,'all')
    assert out[0][0]==out[0][10]==out[10][10]==7
    assert out[10][0]==1
    assert out[4][5]==out[6][5]==7

@pytest.mark.parametrize('seed',range(8))
def test_counts_prefixes_matched_inputs_and_no_aliasing(seed):
    m=engine();a=m.generate(seed,{'selection':'all'},6,4);b=m.generate(seed,{'selection':'largest'},2,1)
    assert [p['input'] for p in a['train'][:2]]==[p['input'] for p in b['train']]
    assert a['test'][0]['input']==b['test'][0]['input']
    for d in range(2,7):
        ep=m.generate(seed,{'selection':'largest'},d,4)
        assert ep['train'][:2]==b['train'] and ep['test'][:1]==b['test']
    assert len({json.dumps(p['input']) for s in ['train','test'] for p in a[s]})==10
    assert len(a['test'][-1]['input'])==len(a['test'][-1]['input'][0])==30
    original=m.generate(seed,{'selection':'all'},6,4)
    a['train'][0]['input'][0][0]=9
    assert m.generate(seed,{'selection':'all'},6,4)==original

@pytest.mark.parametrize('kwargs',[{'seed':True},{'demos':1},{'demos':7},{'queries':0},{'queries':5},{'queries':True},{'settings':{'selection':'bad'}},{'settings':{'selection':'all','leak':1}}])
def test_invalid_controls(kwargs):
    m=engine();args={'seed':0,'settings':{'selection':'all'},'demos':2,'queries':4};args.update(kwargs)
    with pytest.raises(ValueError):m.generate(**args)

@pytest.mark.parametrize('grid',[[],[[1],[1,2]],[[True]],[[10]],[[1.0]],[[1]*31]*3])
def test_reject_malformed_grid(grid):
    m=engine()
    with pytest.raises(ValueError):m.solve(grid,'all')

def test_minimum_lesson_refutes_declared_query_changing_rivals():
    m=engine()
    for seed in range(8):
        for value in ['all','largest']:
            ep=m.generate(seed,{'selection':value},2,4)
            for rival in m.RIVALS:
                fits=all(m.solve(p['input'],value,rival)==p['output'] for p in ep['train'])
                changed=any(m.solve(p['input'],value,rival)!=p['output'] for p in ep['test'])
                assert not(fits and changed),(seed,value,rival)

def test_counterfactual_changes_stress_and_present_is_private():
    m=engine();ep=m.generate(17,{'selection':'largest'},2,4)
    assert m.solve(ep['test'][-1]['input'],'largest','smallest_sector')!=ep['test'][-1]['output']
    p=m.present(17,{'selection':'largest'},2,4,presentation_seed=73)
    assert len(p['public'])==4
    assert m.present(17,{'selection':'largest'},2,1,presentation_seed=73)['public'][0]==p['public'][0]
    for v in p['public']:
        assert set(v)=={'train','test'} and set(v['test'][0])=={'input'}

def test_adapter_relocates_using_only_declared_native_resources(tmp_path):
    import shutil
    base=HOME/'workspace/parametric'
    assert (base/'adapter.py').exists(), 'native adapter missing'
    contract=json.loads((base/'promotion.json').read_text())
    for name in [contract['adapter'],*contract['resources']]:
        shutil.copyfile(ROOT/name,tmp_path/Path(name).name)
    spec=importlib.util.spec_from_file_location('relocated_cut',tmp_path/'adapter.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    ep=a.generate(17,{'selection':'all'},2,4)
    assert ep['program_solution']==(HOME/'reference.rkt').read_text()
    assert len(ep['test'])==4

def test_ordinary_api_is_deterministic_and_canonical():
    path=HOME/'generator.py';assert path.exists(), 'ordinary generator missing'
    spec=importlib.util.spec_from_file_location('ordinary_cut',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert m.PROGRAM==(HOME/'reference.rkt').read_text()
    for index in range(4):
        g=m.generate(0,index)
        assert m.generate(0,index)==g and m.self_check(g)==[]
        assert m.rule_mirror(g)==engine().solve(g,'all')
    with pytest.raises(ValueError):m.generate(0,True)

def test_protected_racket_matches_all_original_labels():
    from arcpuzzles.parametric_worker import _real_evaluator
    data=ROOT/'shared/data/raw';p=json.loads((data/'arc-agi_evaluation_challenges.json').read_text())['4a21e3da'];gold=json.loads((data/'arc-agi_evaluation_solutions.json').read_text())['4a21e3da']
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert identity['protected'] is True
        pairs=p['train']+[{'input':x['input'],'output':y} for x,y in zip(p['test'],gold)]
        for pair in pairs:assert apply((HOME/'reference.rkt').read_text(),pair['input'])==pair['output']
    finally:bridge.close()

def test_stress_artwork_itself_spans_canvas_not_only_markers():
    m=engine()
    for seed in range(32):
        g=m.generate(seed,{'selection':'largest'},2,4)['test'][-1]['input']
        cells={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==7}
        assert len(cells)>=140
        assert max(r for r,c in cells)-min(r for r,c in cells)+1>=28
        assert max(c for r,c in cells)-min(c for r,c in cells)+1>=28
        assert len({r for r,c in cells})>=20 and len({c for r,c in cells})>=20
