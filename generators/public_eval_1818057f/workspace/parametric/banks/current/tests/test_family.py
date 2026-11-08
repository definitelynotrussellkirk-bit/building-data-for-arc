from pathlib import Path
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1]

def engine():
    path=HOME/'workspace/parametric/family.py'
    assert path.exists(), 'cross family implementation missing'
    spec=importlib.util.spec_from_file_location('cross_family_test',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_all_original_labels():
    m=engine();data=ROOT/'shared/data/raw';p=json.loads((data/'arc-agi_evaluation_challenges.json').read_text())['1818057f'];gold=json.loads((data/'arc-agi_evaluation_solutions.json').read_text())['1818057f']
    for pair in p['train']:assert m.solve(pair['input'],'all')==pair['output']
    for pair,out in zip(p['test'],gold):assert m.solve(pair['input'],'largest') is not None and m.solve(pair['input'],'all')==out

def test_plus_ignores_diagonals_and_allows_long_arms():
    m=engine()
    g=[[2,4,2,2,2],[4,4,4,4,4],[4,4,4,2,2],[2,2,2,2,2],[2,2,2,2,2]]
    want=[[2,8,2,2,2],[8,8,8,4,4],[4,8,4,2,2],[2,2,2,2,2],[2,2,2,2,2]]
    assert m.solve(g,'all')==want

def test_detection_is_simultaneous_for_overlapping_crosses():
    m=engine();g=[[4]*3 for _ in range(4)]
    assert m.solve(g,'all')==[[4,8,4],[8,8,8],[8,8,8],[4,8,4]]

def test_no_cross_is_identity_and_boundary_has_no_virtual_neighbors():
    m=engine()
    for g in [[[4]],[[4,4],[4,4]],[[2,4,2],[4,4,4],[2,2,2]]]:
        for v in ['all','largest']:assert m.solve(g,v)==g

def test_largest_cross_bearing_component_not_largest_any_component():
    m=engine();g=[[2]*17 for _ in range(13)]
    for r,c in [(2,2),(1,2),(3,2),(2,1),(2,3),(7,10),(6,10),(8,10),(7,9),(7,11),(7,12),(7,13)]:g[r][c]=4
    # The longer unrelated line has no plus; it must not suppress the real winner.
    for c in range(1,16):g[11][c]=4
    out=m.solve(g,'largest')
    assert out[2][2]==4 and out[7][10]==8 and out[11]==g[11]
    assert sum(x==8 for row in out for x in row)==5

@pytest.mark.parametrize('seed',range(8))
def test_matched_inputs_independent_counts_and_stress(seed):
    m=engine();a=m.generate(seed,{'selection':'all'},6,4);b=m.generate(seed,{'selection':'largest'},2,4)
    assert [p['input'] for p in a['train'][:2]]==[p['input'] for p in b['train']]
    assert [p['input'] for p in a['test']]==[p['input'] for p in b['test']]
    for d in range(2,7):assert m.generate(seed,{'selection':'all'},d,4)['train']==a['train'][:d]
    for q in range(1,5):assert m.generate(seed,{'selection':'all'},2,q)['test']==a['test'][:q]
    assert len({json.dumps(p['input']) for sp in ['train','test'] for p in a[sp]})==10
    stress=a['test'][-1]['input'];assert len(stress)==len(stress[0])==30
    assert sum(x==4 for row in stress for x in row)>100
    assert any(x==4 for x in stress[0]+stress[-1])
    frozen=m.generate(seed,{'selection':'all'},6,4);a['test'][0]['input'][0][0]=9
    assert m.generate(seed,{'selection':'all'},6,4)==frozen

@pytest.mark.parametrize('kwargs',[{'seed':True},{'demos':1},{'demos':7},{'queries':0},{'queries':5},{'queries':True},{'settings':{'selection':2}},{'settings':{'selection':'all','extra':0}}])
def test_invalid_controls(kwargs):
    m=engine();args={'seed':0,'settings':{'selection':'all'},'demos':2,'queries':4};args.update(kwargs)
    with pytest.raises(ValueError):m.generate(**args)

@pytest.mark.parametrize('grid',[[],[[1],[1,2]],[[True]],[[10]],[[1.0]],[[1]*31]*3])
def test_malformed_grid(grid):
    with pytest.raises(ValueError):engine().solve(grid,'all')

def test_minimum_lessons_refute_declared_rivals():
    m=engine()
    for seed in range(8):
        for v in ['all','largest']:
            ep=m.generate(seed,{'selection':v},2,4)
            for rival in m.RIVALS:
                fits=all(m.solve(p['input'],v,rival)==p['output'] for p in ep['train'])
                changed=any(m.solve(p['input'],v,rival)!=p['output'] for p in ep['test'])
                assert not(fits and changed),(seed,v,rival)

def test_present_hides_private_and_shuffles_before_prefix():
    m=engine();a=m.present(17,{'selection':'largest'},2,4,presentation_seed=73)
    assert m.present(17,{'selection':'largest'},2,1,presentation_seed=73)['public'][0]==a['public'][0]
    assert all(set(v)=={'train','test'} and set(v['test'][0])=={'input'} for v in a['public'])

def test_query_geometry_is_not_a_fixed_template_count_menu():
    m=engine();sizes=set();backgrounds=set()
    for seed in range(24):
        ep=m.generate(seed,{'selection':'largest'},2,4)
        for pair in ep['test']:
            p=m.parse(pair['input']);sizes.add(max(map(len,p['bearing'])))
            backgrounds.add(pair['input'][1][1])
    assert len(sizes)>8
    assert len(backgrounds)>4

def test_protected_racket_matches_all_original_labels():
    from arcpuzzles.parametric_worker import _real_evaluator
    data=ROOT/'shared/data/raw';p=json.loads((data/'arc-agi_evaluation_challenges.json').read_text())['1818057f'];gold=json.loads((data/'arc-agi_evaluation_solutions.json').read_text())['1818057f']
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert identity['protected'] is True
        pairs=p['train']+[{'input':x['input'],'output':y} for x,y in zip(p['test'],gold)]
        for pair in pairs:assert apply((HOME/'reference.rkt').read_text(),pair['input'])==pair['output']
    finally:bridge.close()

def test_adapter_relocates_using_only_declared_native_resources(tmp_path):
    import shutil
    base=HOME/'workspace/parametric';assert (base/'adapter.py').exists(), 'native adapter missing'
    contract=json.loads((base/'promotion.json').read_text())
    for name in [contract['adapter'],*contract['resources']]:shutil.copyfile(ROOT/name,tmp_path/Path(name).name)
    spec=importlib.util.spec_from_file_location('relocated_cross',tmp_path/'adapter.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    ep=a.generate(17,{'selection':'all'},2,4)
    assert ep['program_solution']==(HOME/'reference.rkt').read_text() and len(ep['test'])==4

def test_ordinary_api_is_deterministic_and_canonical():
    path=HOME/'generator.py';assert path.exists(), 'ordinary generator missing'
    spec=importlib.util.spec_from_file_location('ordinary_cross',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert m.PROGRAM==(HOME/'reference.rkt').read_text()
    for index in range(4):
        g=m.generate(0,index);assert m.generate(0,index)==g and m.self_check(g)==[]
        assert m.rule_mirror(g)==engine().solve(g,'all')
    with pytest.raises(ValueError):m.generate(0,True)
