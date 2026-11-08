from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
P = HOME / 'workspace/parametric'

def load(path, name):
    assert path.is_file(), f'missing authored source: {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def adapter():
    return load(P/'adapter.py', 'placement_adapter_test')

@pytest.fixture(scope='module')
def evaluator():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply, identity, bridge = _real_evaluator(ROOT/'shared/runtime')
    assert identity['protected'] is True
    yield apply
    bridge.close()

@pytest.mark.parametrize('split,index', [('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_reference_matches_each_original_label(evaluator, split, index):
    # A horizontal-axis repair or a rightmost tie-break fails these fixtures.
    assert (HOME/'reference.rkt').is_file(), 'reference rule has not been authored'
    parent = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['247ef758']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['247ef758']
    pair = parent[split][index]
    expected = pair['output'] if split=='train' else gold[index]
    assert evaluator((HOME/'reference.rkt').read_text(), pair['input']) == expected

def test_opposite_markers_and_source_priority_on_hand_fixture(adapter, evaluator):
    grid=[[0]*14 for _ in range(10)]
    for r in range(10):grid[r][3]=2
    for r in range(10):grid[r][4]=grid[r][-1]=9
    for c in range(4,14):grid[0][c]=grid[-1][c]=9
    # Earlier high-color singleton overrides later low-color 3x3 square.
    grid[0][0]=7
    for r in range(2,5):
        for c in range(3):grid[r][c]=1
    for r,col in [(4,7),(5,1)]:grid[r][4]=grid[r][-1]=col
    for c,col in [(8,7),(9,1)]:grid[0][c]=grid[-1][c]=col
    # A mismatched duplicate row marker must not create another copy.
    grid[7][4]=7;grid[7][-1]=5
    canonical=adapter.predict(grid,{'overlap_priority':'source_order'})
    alternate=adapter.predict(grid,{'overlap_priority':'largest_first'})
    assert canonical[4][8]==7 and alternate[4][8]==1
    assert canonical[7][8]==0 and alternate[7][8]==0
    assert all(canonical[r][c]==0 for r in range(5) for c in range(3))
    assert evaluator(adapter.program({'overlap_priority':'source_order'}),grid)==canonical
    assert evaluator(adapter.program({'overlap_priority':'largest_first'}),grid)==alternate

def test_default_exact_and_independent_resource(adapter):
    assert adapter.program({'overlap_priority':'source_order'}).encode() == (HOME/'reference.rkt').read_bytes()
    assert (P/'canonical.rkt').read_bytes() == (HOME/'reference.rkt').read_bytes()

@pytest.mark.parametrize('demos',[2,3,6])
def test_count_determinism_and_matched_inputs(adapter, demos):
    a = adapter.generate(17,{'overlap_priority':'source_order'},demos,4)
    b = adapter.generate(17,{'overlap_priority':'largest_first'},demos,4)
    assert a == adapter.generate(17,{'overlap_priority':'source_order'},demos,4)
    assert len(a['train'])==demos and len(a['test'])==4
    inputs=[p['input'] for sp in ('train','test') for p in a[sp]]
    assert inputs==[p['input'] for sp in ('train','test') for p in b[sp]]
    assert len({json.dumps(g) for g in inputs})==demos+4
    assert a['test']==adapter.generate(17,{'overlap_priority':'source_order'},2,4)['test']
    assert any(x['output']!=y['output'] for x,y in zip(a['train'],b['train']))
    g=next(p['input'] for p in a['test'] if len(p['input'])==len(p['input'][0])==30);assert len(g)==len(g[0])==30
    bg=max(range(10),key=lambda x:sum(row.count(x) for row in g))
    assert sum(v!=0 for row in g for v in row)>=100
    for rr,cc in [(0,0),(0,15),(15,0),(15,15)]:
        assert sum(g[r][c]!=0 for r in range(rr,rr+15) for c in range(cc,cc+15))>=12

@pytest.mark.parametrize('kwargs',[dict(seed=True),dict(seed=-1),dict(demos=1),dict(demos=7),dict(demos=True),dict(queries=0),dict(queries=5),dict(settings={'overlap_priority':'invalid'}),dict(settings={'overlap_priority':'source_order','extra':0})])
def test_rejects_invalid_native_requests(adapter, kwargs):
    request=dict(seed=0,settings={'overlap_priority':'source_order'},demos=2,queries=4);request.update(kwargs)
    with pytest.raises((ValueError,TypeError)): adapter.generate(**request)

def test_standalone_generator_relocated(tmp_path):
    path=tmp_path/'isolated_generator.py'
    assert (HOME/'generator.py').is_file(), 'standalone generator not authored'
    path.write_bytes((HOME/'generator.py').read_bytes())
    gen=load(path,'relocated_placement_generator')
    assert gen.RULE_TASK_ID=='ee_247ef758'
    grid=gen.generate(23,103)
    assert len(grid)==len(grid[0])==30
    assert gen.self_check(grid)==[]

def test_sampler_mirror_copy_stays_exact():
    assert (HOME/'generator.py').is_file(), 'generator missing'
    assert (HOME/'generator.py').read_bytes()==(P/'sampler.py').read_bytes()

def test_declared_rivals_do_not_survive_two_demo_lessons():
    audit=load(P/'audit.py','placement_audit_test')
    result=audit.audit(range(4),(2,3,6))
    assert result['failures']==[]
    assert result['episodes']==24

def test_area_order_reverses_and_ties_across_structures(adapter):
    # A fixed 'dense-looking shape wins' policy must not replace measured area.
    signs=set();ties=0
    for seed in range(32):
        g=adapter.sampler.sample(seed,101)
        _,parts=adapter.sampler.records(g)
        sparse=next(p for p in parts if p['bbox_area']==25)
        square=next(p for p in parts if p['bbox_area']==9)
        signs.add((square['area']>sparse['area'])-(square['area']<sparse['area']))
        ties+=square['area']==sparse['area']
    assert signs=={-1,0,1}
    assert ties>0

def test_large_scene_retains_substantive_stamps_after_area_reversal(adapter):
    for mode in ('source_order','largest_first'):
        pair=adapter.generate(24,{'overlap_priority':mode},2,4)['test'][3]
        sep,_=adapter.sampler.records(pair['input'])
        assert sum(pair['output'][r][c]!=0 for r in range(1,29) for c in range(sep+2,29))>=75
