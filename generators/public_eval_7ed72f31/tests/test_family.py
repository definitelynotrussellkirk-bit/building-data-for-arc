import copy
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def f():
    path=HOME/'workspace/parametric/family.py'
    assert path.is_file(), 'marker-copy family is missing'
    spec=importlib.util.spec_from_file_location('test_marker_family',path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def original_pairs():
    root=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())
    data=json.loads((root/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['7ed72f31']
    sols=json.loads((root/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['7ed72f31']
    return data['train']+[dict(input=p['input'],output=o) for p,o in zip(data['test'],sols)]

def test_all_original_labels(f):
    for i,pair in enumerate(original_pairs()): assert f.solve(pair['input'],'reflect')==pair['output'], i

def test_point_center_is_not_shape_bbox_center(f):
    g=[[8]*7 for _ in range(7)]; g[3][3]=2
    for r,c in [(1,2),(2,1),(2,2)]: g[r][c]=4
    want=copy.deepcopy(g)
    for r,c in [(5,4),(4,5),(4,4)]: want[r][c]=4
    assert f.solve(g,'reflect')==want
    assert f.solve(g,'half_turn')==want

def test_line_axis_and_midpoint_are_distinct(f):
    g=[[0]*9 for _ in range(9)]
    for r in range(3,6): g[r][4]=2
    for r,c in [(2,2),(3,2),(3,3),(4,3)]: g[r][c]=7
    reflected=copy.deepcopy(g)
    for r,c in [(2,6),(3,6),(3,5),(4,5)]: reflected[r][c]=7
    turned=copy.deepcopy(g)
    for r,c in [(6,6),(5,6),(5,5),(4,5)]: turned[r][c]=7
    assert f.solve(g,'reflect')==reflected
    assert f.solve(g,'half_turn')==turned
    assert reflected[2][6]==7  # Copy beyond marker endpoints, not segment-clipped.

def test_even_marker_midpoint_and_diagonal_attachment(f):
    g=[[9]*10 for _ in range(10)]
    g[4][4]=g[4][5]=2
    g[3][3]=g[2][2]=6  # 8-neighbor-only chain to marker endpoint.
    want=copy.deepcopy(g); want[5][6]=want[6][7]=6
    assert f.solve(g,'half_turn')==want

@pytest.mark.parametrize('seed',[0,1,17,43])
def test_sampler_counts_prefixes_and_stress(f,seed):
    full=f.generate(seed,{'line_action':'reflect'},6,4)
    other=f.generate(seed,{'line_action':'half_turn'},6,4)
    for mode in f.MODES:
        ref=full if mode=='reflect' else other
        for demos in range(2,7):
            for queries in range(1,5):
                ep=f.generate(seed,{'line_action':mode},demos,queries)
                assert ep['train']==ref['train'][:demos]
                assert ep['test']==ref['test'][:queries]
    for split in ('train','test'):
        assert [p['input'] for p in full[split]]==[p['input'] for p in other[split]]
    grids=[p['input'] for sp in ('train','test') for p in full[sp]]
    assert len({json.dumps(g) for g in grids})==10
    stress=grids[-1]; assert len(stress)==len(stress[0])==30
    groups=f.analyze(stress)
    assert len(groups)>=6
    assert {x['kind'] for x in groups}=={'point','horizontal','vertical'}
    assert sum(len(x['source']) for x in groups)>=40
    assert full['train'][0]['output']!=other['train'][0]['output']

@pytest.mark.parametrize('args',[(True,{},2,4),(1,{'line_action':'reflect'},1,4),(1,{'line_action':'reflect'},7,4),(1,{'line_action':'reflect'},2,0),(1,{'line_action':'reflect'},2,5),(1,{'line_action':'reflect'},True,4),(1,{'line_action':'unknown'},2,4),(1,{'line_action':'reflect','leak':1},2,4)])
def test_bad_requests_rejected(f,args):
    with pytest.raises((ValueError,TypeError)): f.generate(*args)

@pytest.mark.parametrize('g',[[],[[0],[0,1]],[[True]],[[10]],[[1.0]]])
def test_malformed_grid_rejected(f,g):
    with pytest.raises(ValueError): f.solve(g,'reflect')

def test_bad_marker_rejected(f):
    g=[[0]*7 for _ in range(7)]
    g[3][3]=g[3][4]=g[4][4]=2; g[2][2]=5
    with pytest.raises(ValueError): f.analyze(g)

def test_public_view_has_no_private_leak(f):
    ep=f.generate(17,{'line_action':'reflect'},2,4)
    want=f.public_turn(ep,0,42); mut=copy.deepcopy(ep)
    mut['program_solution']='SECRET'; mut['seed']=-1; mut['settings']={'secret':True}
    for p in mut['test']: p['output']=[[7]]; p['hint']='hidden'
    for p in mut['train']: p['hint']='hidden'
    assert f.public_turn(mut,0,42)==want
    assert set(want)=={'train','test'} and len(want['test'])==1 and set(want['test'][0])=={'input'}
    assert len({json.dumps(f.public_turn(ep,0,s)) for s in range(16)})>1

def test_no_finite_query_changing_rival(f):
    for seed in range(32):
        for mode in f.MODES:
            ep=f.generate(seed,{'line_action':mode},2,4)
            for rival in f.RIVALS:
                fits=all(f.rival_solve(p['input'],mode,rival)==p['output'] for p in ep['train'])
                if fits: assert all(f.rival_solve(p['input'],mode,rival)==p['output'] for p in ep['test']), (seed,mode,rival)

def test_canonical_and_generator(f):
    assert f.program({'line_action':'reflect'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    spec=importlib.util.spec_from_file_location('marker_generator_test',HOME/'generator.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    g=mod.generate(7,0); assert not mod.self_check(g)
    assert mod.RULE_TASK_ID=='ee_7ed72f31'
    with pytest.raises((TypeError,ValueError)): mod.generate(1,0,typo=True)
