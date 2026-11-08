"""Behavioral contracts: no source-grid lookup, strict types, masks and privacy."""
from pathlib import Path
import importlib.util
import json
import sys
import copy
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').exists())

def load():
    path = HOME / 'workspace/parametric/adapter.py'
    assert path.exists(), 'native adapter has not been implemented'
    spec = importlib.util.spec_from_file_location('stencil_test_adapter', path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod

def test_original_pairs_python_claims():
    a = load()
    parent = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['58f5dbd5']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['58f5dbd5']
    for p in parent['train'] + [dict(input=p['input'], output=o) for p,o in zip(parent['test'],gold)]:
        assert a.impl.solve([[int(v) for v in r] for r in p['input']]) == [[int(v) for v in r] for r in p['output']]

def test_default_program_exact_and_alternate_changes_labels():
    a = load()
    assert a.program({'stencil_mode':'cutout'}) == (HOME/'reference.rkt').read_text()
    x = a.generate(17, {'stencil_mode':'cutout'}, 2, 4)
    y = a.generate(17, {'stencil_mode':'emboss'}, 2, 4)
    assert [p['input'] for s in ('train','test') for p in x[s]] == [p['input'] for s in ('train','test') for p in y[s]]
    assert all(p['output'] != q['output'] for p,q in zip(x['train'],y['train']))

@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_distinct_determinism_and_large_query(demos):
    a = load(); x = a.generate(43, {'stencil_mode':'cutout'}, demos, 4)
    assert x == a.generate(43, {'stencil_mode':'cutout'}, demos, 4)
    assert len(x['train']) == demos and len(x['test']) == 4
    grids = [p['input'] for s in ('train','test') for p in x[s]]
    assert len({json.dumps(g) for g in grids}) == demos + 4
    assert len(x['test'][3]['input']) == len(x['test'][3]['input'][0]) == 30
    assert x['test'] == a.generate(43, {'stencil_mode':'cutout'}, 2, 4)['test']
    for g in grids:
        assert 1<=len(g)<=30 and 1<=len(g[0])<=30
        assert all(len(r)==len(g[0]) and all(type(v) is int and 0<=v<=9 for v in r) for r in g)

@pytest.mark.parametrize('seed,demos,queries,settings',[
    (True,2,4,{'stencil_mode':'cutout'}),(-1,2,4,{'stencil_mode':'cutout'}),
    (1,1,4,{'stencil_mode':'cutout'}),(1,7,4,{'stencil_mode':'cutout'}),
    (1,True,4,{'stencil_mode':'cutout'}),(1,2,1,{'stencil_mode':'cutout'}),
    (1,2,5,{'stencil_mode':'cutout'}),(1,2,4,{'stencil_mode':'bad'}),
    (1,2,4,{}),(1,2,4,{'stencil_mode':'cutout','extra':1})])
def test_reject_invalid_requests(seed,demos,queries,settings):
    a=load()
    with pytest.raises(ValueError): a.generate(seed,settings,demos,queries)

def test_hand_derived_mask_border_and_input_immutability():
    a=load();g=[[0]*13 for _ in range(8)]
    for r in range(1,6):
        for c in range(1,6): g[r][c]=2
    for r,c in [(0,0),(0,2),(1,1),(2,0)]:g[r+2][c+9]=2
    original=copy.deepcopy(g)
    expected=[[0]*7,[0,2,2,2,2,2,0],[0,2,0,2,0,2,0],[0,2,2,0,2,2,0],[0,2,0,2,2,2,0],[0,2,2,2,2,2,0],[0]*7]
    assert a.impl.solve(g)==expected
    assert g==original

def test_public_one_at_a_time_is_private_invariant():
    a=load();x=a.generate(17,{'stencil_mode':'cutout'},3,4)
    v=a.impl.public_turns(x,918)
    assert len(v)==4 and all(set(z)=={'train','test'} and len(z['test'])==1 and set(z['test'][0])=={'input'} for z in v)
    y=copy.deepcopy(x);y['settings']={'secret':True};y['program_solution']='SECRET';y['seed']=999
    for p in y['test']:p['output']=[[9]]
    assert v==a.impl.public_turns(y,918)
    assert v[:1]==a.impl.public_turns(x,918,stop_after=1)
    assert len({json.dumps(a.impl.public_turns(x,s)[0]['test']) for s in range(16)})>1

def test_public_strips_pair_level_private_fields():
    a=load();x=a.generate(17,{'stencil_mode':'cutout'},2,4)
    x['train'][0]['private']='must not appear'
    assert set(a.impl.public_turns(x,0)[0]['train'][0]) == {'input','output'}

def test_bounded_finite_rivals_rejected_by_minimum_lesson():
    a=load()
    rivals=['flip_lr','flip_ud','rotate_180','next_color','solid_interior','empty_interior','source_order','numeric_order']
    for seed in range(32):
        for mode in ['cutout','emboss']:
            x=a.generate(seed,{'stencil_mode':mode},2,4)
            for rival in rivals:
                survives=all(a.impl.solve(p['input'],mode,rival)==p['output'] for p in x['train'])
                assert not survives or all(a.impl.solve(p['input'],mode,rival)==p['output'] for p in x['test']), (seed,mode,rival)


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


def test_extended_rival_implementations_are_behaviorally_distinct():
    a = load()
    rivals = [
        'transpose', 'anti_transpose', 'rotate_90', 'rotate_270',
        'largest_8', 'outline', 'area_order', 'color_parity',
    ]
    grids = [a.impl.sample(seed, index) for seed in range(8) for index in (0, 1, 100, 101, 102, 103)]
    for rival in rivals:
        assert any(
            a.impl.solve(grid, mode, rival) != a.impl.solve(grid, mode)
            for grid in grids
            for mode in a.impl.MODES
        ), rival


def test_extended_minimum_lessons_reject_harmful_rivals_through_seed_63():
    a = load()
    rivals = [
        'flip_lr', 'flip_ud', 'rotate_180', 'transpose', 'anti_transpose',
        'rotate_90', 'rotate_270', 'next_color', 'solid_interior',
        'empty_interior', 'source_order', 'numeric_order', 'area_order',
        'largest_8', 'outline', 'color_parity',
    ]
    for seed in range(64):
        for mode in a.impl.MODES:
            episode = a.generate(seed, {'stencil_mode': mode}, 2, 4)
            for rival in rivals:
                survives = all(a.impl.solve(pair['input'], mode, rival) == pair['output'] for pair in episode['train'])
                assert not survives or all(
                    a.impl.solve(pair['input'], mode, rival) == pair['output'] for pair in episode['test']
                ), (seed, mode, rival)
