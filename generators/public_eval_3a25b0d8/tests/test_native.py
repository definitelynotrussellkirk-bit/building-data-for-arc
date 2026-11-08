"""Region transfer contracts, including overlapping figure bounding boxes."""
from pathlib import Path
import importlib.util
import json
import sys
import copy
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').exists())

def load():
    path=HOME/'workspace/parametric/banks/bank0/workspace/parametric/adapter.py'
    assert path.exists(),'region adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('_region_test_adapter',path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m

def test_every_original_train_and_test_gold():
    a=load();p=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['3a25b0d8']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['3a25b0d8']
    for pair in p['train']+[dict(input=q['input'],output=o) for q,o in zip(p['test'],gold)]:
        g=[[int(v) for v in row] for row in pair['input']]
        expected=[[int(v) for v in row] for row in pair['output']]
        assert a.impl.solve(g)==expected

def test_default_bytes_and_setting_neutral_stream():
    a=load();assert a.program({'transfer_scope':'all'})==(HOME/'reference.rkt').read_text()
    p=a.generate(17,{'transfer_scope':'all'},2,4);q=a.generate(17,{'transfer_scope':'expanded_only'},2,4)
    assert [x['input'] for s in ('train','test') for x in p[s]]==[x['input'] for s in ('train','test') for x in q[s]]
    assert all(x['output']!=y['output'] for x,y in zip(p['train'],q['train']))

@pytest.mark.parametrize('demos',[2,3,6])
def test_deterministic_independent_counts_and_stress(demos):
    a=load();p=a.generate(43,{'transfer_scope':'all'},demos,4)
    assert p==a.generate(43,{'transfer_scope':'all'},demos,4)
    assert p['test']==a.generate(43,{'transfer_scope':'all'},2,4)['test']
    assert len(p['train'])==demos and len(p['test'])==4
    assert len({json.dumps(x['input']) for s in ('train','test') for x in p[s]})==demos+4
    g=p['test'][3]['input'];assert (len(g),len(g[0]))==(30,30)
    facts=a.impl.analyse(g);cells=facts['source_cells']+facts['target_cells']
    assert max(r for r,c in cells)-min(r for r,c in cells)>=26
    assert max(c for r,c in cells)-min(c for r,c in cells)>=26
    assert len(cells)>250

@pytest.mark.parametrize('seed,demos,queries,settings',[
 (True,2,4,{'transfer_scope':'all'}),(-1,2,4,{'transfer_scope':'all'}),
 (1,1,4,{'transfer_scope':'all'}),(1,7,4,{'transfer_scope':'all'}),(1,True,4,{'transfer_scope':'all'}),
 (1,2,1,{'transfer_scope':'all'}),(1,2,5,{'transfer_scope':'all'}),
 (1,2,4,{}),(1,2,4,{'transfer_scope':'BAD'}),(1,2,4,{'transfer_scope':'all','secret':1})])
def test_invalid_requests(seed,demos,queries,settings):
    a=load()
    with pytest.raises(ValueError):a.generate(seed,settings,demos,queries)

def fixture():
    g=[[0]*20 for _ in range(10)]
    for r in range(1,8):
        for c in list(range(1,8))+list(range(11,18)):g[r][c]=2
    g[2][3]=3
    for r in (4,5):
        for c in (3,4):g[r][c]=5
    for c in (12,13,14):g[2][c]=0
    g[5][14]=0
    return g

def test_hand_derived_spatial_correspondence_and_area_condition():
    a=load();g=fixture();before=copy.deepcopy(g)
    expected=[[2]*7,[2,3,3,3,2,2,2],[2]*7,[2]*7,[2,2,2,5,2,2,2],[2]*7,[2]*7]
    assert a.impl.solve(g)==expected
    expected[4][3]=0
    assert a.impl.solve(g,'expanded_only')==expected
    assert g==before

def test_equal_area_is_not_expansion():
    a=load();g=fixture()
    g[2][12]=g[2][14]=2
    assert a.impl.solve(g,'expanded_only')[1][2]==0

def test_public_one_query_and_strict_metadata_projection():
    a=load();p=a.generate(17,{'transfer_scope':'all'},3,4)
    views=a.impl.public_turns(p,99)
    assert len(views)==4 and all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)
    q=copy.deepcopy(p);q['settings']={'secret':1};q['program_solution']='PRIVATE';q['seed']=42
    for x in q['test']:x['output']=[[9]];x['hidden']=True
    for x in q['train']:x['hidden']=True
    assert views==a.impl.public_turns(q,99)
    assert views[:1]==a.impl.public_turns(p,99,stop_after=1)
    assert len({json.dumps(a.impl.public_turns(p,i)[0]['test']) for i in range(16)})>1

def test_finite_rivals_do_not_survive_then_change_queries():
    a=load();rivals=['source_scan','target_scan','source_area','target_area','reverse','numeric_colors','guide_copy','first_color','nonshrunk','shrunk','always']
    for seed in range(32):
        for scope in ['all','expanded_only']:
            x=a.generate(seed,{'transfer_scope':scope},2,4)
            for rival in rivals:
                survives=all(a.impl.solve(p['input'],scope,rival)==p['output'] for p in x['train'])
                assert not survives or all(a.impl.solve(p['input'],scope,rival)==p['output'] for p in x['test']), (seed,scope,rival)

def test_center_order_is_not_pixel_scan_order():
    a=load();x=a.generate(17,{'transfer_scope':'all'},2,4)
    assert any(a.impl.solve(p['input'],'all','source_scan')!=p['output'] for p in x['train'])
    assert any(a.impl.solve(p['input'],'all','target_scan')!=p['output'] for p in x['train'])

def test_large_scene_preserves_overlapping_bbox_isolation_challenge():
    a=load();g=a.impl.sample(17,103);f=a.impl.analyse(g)
    x=a.impl.bbox(f['source_cells']);y=a.impl.bbox(f['target_cells'])
    assert max(x[0],y[0])<=min(x[2],y[2]) and max(x[1],y[1])<=min(x[3],y[3])
    assert a.impl.solve(g)!=f['source']

def test_simultaneously_scanning_both_figures_is_also_rejected():
    a=load();ep=a.generate(17,{'transfer_scope':'all'},2,4)
    assert any(a.impl.solve(p['input'],'all','both_scan')!=p['output'] for p in ep['train'])


def test_base_generator_works_when_relocated_as_flat_runtime_module(tmp_path):
    import shutil
    path=tmp_path/'puzzle_generators/per_puzzle'/(HOME.name+'.py')
    path.parent.mkdir(parents=True)
    shutil.copyfile(HOME/'generator.py',path)
    spec=importlib.util.spec_from_file_location('_relocated_'+HOME.name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    assert module.generate(29,0)==load().impl.sample(29,0)
    assert module.check_invariants(module.generate(29,3))==[]
