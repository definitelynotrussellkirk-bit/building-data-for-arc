"""Regression expectations are original gold or independently constructed grids."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def f():
    path = HOME/'workspace/parametric/family.py'
    assert path.is_file(), 'periodic-strip implementation is missing'
    spec = importlib.util.spec_from_file_location('test_periodic_family', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def original_pairs():
    root = next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())
    data = json.loads((root/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['135a2760']
    sol = json.loads((root/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['135a2760']
    return data['train'] + [dict(input=p['input'], output=o) for p,o in zip(data['test'],sol)]

def test_original_labels(f):
    for pair in original_pairs():
        assert f.solve(pair['input'], 'restore') == pair['output']

def test_literal_corruption_and_marking(f):
    inp = [[int(x) for x in s] for s in ['3333333333333','3222222222223','3213131333123','3222222222223','3333333333333']]
    expected = copy.deepcopy(inp); expected[2][8] = 1
    marked = copy.deepcopy(inp); marked[2][8] = 2
    assert f.solve(inp, 'restore') == expected
    assert f.solve(inp, 'mark_errors') == marked
    assert f.analyze(inp)[0]['period'] == 2
    assert inp[2][8] == 3

@pytest.mark.parametrize('seed', [0,1,17,43])
def test_counts_matched_inputs_prefixes_and_stress(f, seed):
    full = f.generate(seed, {'repair_mode':'restore'}, 6,4)
    other = f.generate(seed, {'repair_mode':'mark_errors'},6,4)
    for mode in ('restore','mark_errors'):
        for demos in range(2,7):
            for queries in range(1,5):
                ep = f.generate(seed, {'repair_mode':mode},demos,queries)
                ref = full if mode=='restore' else other
                assert ep['train']==ref['train'][:demos]
                assert ep['test']==ref['test'][:queries]
                assert ep['program_solution']==f.program({'repair_mode':mode})
    for split in ('train','test'):
        assert [p['input'] for p in full[split]]==[p['input'] for p in other[split]]
    grids = [p['input'] for split in ('train','test') for p in full[split]]
    assert len({json.dumps(g) for g in grids})==10
    assert len(grids[-1])==len(grids[-1][0])==30
    facts = f.analyze(grids[-1]); assert len(facts)>=3
    assert sum(len(x['corrections']) for x in facts)>=3
    assert full['train'][0]['output']!=other['train'][0]['output']

@pytest.mark.parametrize('args',[(True,{},2,4),(1,{'repair_mode':'restore'},1,4),(1,{'repair_mode':'restore'},7,4),(1,{'repair_mode':'restore'},2,0),(1,{'repair_mode':'restore'},2,5),(1,{'repair_mode':'restore'},True,4),(1,{'repair_mode':'unknown'},2,4),(1,{'repair_mode':'restore','leak':1},2,4)])
def test_bad_requests_rejected(f,args):
    with pytest.raises((ValueError,TypeError)): f.generate(*args)

@pytest.mark.parametrize('grid',[[],[[0],[0,1]],[[True]],[[10]],[[1.0]]])
def test_malformed_grid_rejected(f,grid):
    with pytest.raises(ValueError): f.solve(grid,'restore')

def test_public_view_ignores_private_fields(f):
    ep=f.generate(17,{'repair_mode':'restore'},3,4)
    view=f.public_turn(ep,0,123)
    changed=copy.deepcopy(ep); changed['settings']={'secret':True}; changed['seed']=999
    changed['program_solution']='SECRET'
    for p in changed['test']: p['output']=[[7]]
    assert f.public_turn(changed,0,123)==view
    assert set(view)=={'train','test'} and len(view['test'])==1
    assert set(view['test'][0])=={'input'}
    observed={json.dumps(f.public_turn(ep,0,s)['test'][0]['input']) for s in range(16)}
    assert len(observed)>1
    for turn in range(4): assert len(f.public_turn(ep,turn,123)['test'])==1

def test_finite_rivals_do_not_survive_two_demos_and_change_queries(f):
    for seed in range(16):
        for mode in ('restore','mark_errors'):
            ep=f.generate(seed,{'repair_mode':mode},2,4)
            for rival in f.RIVALS:
                fits=all(f.rival_solve(p['input'],mode,rival)==p['output'] for p in ep['train'])
                if fits: assert all(f.rival_solve(p['input'],mode,rival)==p['output'] for p in ep['test']), (seed,mode,rival)

def test_canonical_copy_and_generator_contract(f):
    assert f.program({'repair_mode':'restore'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()
    spec=importlib.util.spec_from_file_location('periodic_generator_test',HOME/'generator.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    grid=mod.generate(17,0)
    assert not mod.self_check(grid)
    assert mod.RULE_TASK_ID=='ee_135a2760'
    with pytest.raises((TypeError,ValueError)): mod.generate(1,0,typo=True)

def test_public_projection_strips_pair_level_private_fields(f):
    ep=f.generate(1,{'repair_mode':'restore'},2,4)
    baseline=f.public_turn(ep,0,17)
    ep['train'][0]['settings']={'answer_hint':9}
    ep['train'][0]['program']='PRIVATE'
    ep['test'][0]['future_input']=[[8]]
    assert f.public_turn(ep,0,17)==baseline
