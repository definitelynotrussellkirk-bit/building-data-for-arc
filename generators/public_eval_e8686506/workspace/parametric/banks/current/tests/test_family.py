from pathlib import Path
import importlib.util
import json
import copy
import shutil
import pytest
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def load(path, name='test_assembly_adapter'):
    assert path.is_file(), f'Missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture(scope='module')
def a():
    return load(HOME/'workspace/parametric/adapter.py')

@pytest.mark.parametrize('index', range(3))
def test_original_labels_not_rotated_or_recolored(a,index):
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['e8686506']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['e8686506']
    pairs=data['train']+[dict(input=p['input'],output=o) for p,o in zip(data['test'],gold)]
    assert a.G.solve(pairs[index]['input'],'assemble')==pairs[index]['output']

def test_default_is_exact_reference_and_local_resource(a):
    assert a.program({'render':'assemble'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,2,17,43,127])
def test_matched_distinct_deterministic_prefixes(a,seed):
    e=a.generate(seed,{'render':'assemble'},6,4)
    other=a.generate(seed,{'render':'first_cavity_piece'},6,4)
    assert [p['input'] for k in ('train','test') for p in e[k]]==[p['input'] for k in ('train','test') for p in other[k]]
    assert len({json.dumps(p['input']) for k in ('train','test') for p in e[k]})==10
    for d in range(2,7):
        assert a.generate(seed,{'render':'assemble'},d,4)['train']==e['train'][:d]
    for q in range(1,5):
        assert a.generate(seed,{'render':'assemble'},2,q)['test']==e['test'][:q]
    assert all(x['output']!=y['output'] for x,y in zip(e['test'],other['test']))
    e['test'][0]['input'][0][0]=-1
    assert all(v>=0 for row in a.generate(seed,{'render':'assemble'},6,4)['test'][0]['input'] for v in row)

@pytest.mark.parametrize('seed',range(8))
def test_minimum_lessons_refute_query_changing_rivals(a,seed):
    for mode in ('assemble','first_cavity_piece'):
        e=a.generate(seed,{'render':mode},2,4)
        for rival in a.G.RIVALS:
            survives=all(a.G.solve(p['input'],mode,rival=rival)==p['output'] for p in e['train'])
            changes=any(a.G.solve(p['input'],mode,rival=rival)!=p['output'] for p in e['test'])
            assert not(survives and changes),(seed,mode,rival)

def test_stress_is_not_only_padding_and_tiling_unique(a):
    e=a.generate(17,{'render':'assemble'},2,4)
    g=e['test'][3]['input']; assert (len(g),len(g[0]))==(30,30)
    info=a.G.analyze(g)
    occupied=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=info['bg']]
    assert len(occupied)>=90
    assert max(r for r,c in occupied)-min(r for r,c in occupied)>=25
    assert max(c for r,c in occupied)-min(c for r,c in occupied)>=25
    assert a.G.unique_colored_tiling(g)

def test_public_first_turn_and_permutation(a):
    indices=set()
    for seed in range(8):
        b=a.present(seed,{'render':'assemble'},2,4,presentation_seed=73)
        assert a.present(seed,{'render':'assemble'},2,1,presentation_seed=73)['public'][0]==b['public'][0]
        indices.add(b['private']['source_indices'][0])
        for view in b['public']:
            assert set(view)=={'train','test'} and len(view['test'])==1
            assert set(view['test'][0])=={'input'}
    assert len(indices)>1

@pytest.mark.parametrize('args',[(True,{},2,4),(0,{'render':'bad'},2,4),(0,{'render':'assemble','extra':1},2,4),(0,{'render':'assemble'},1,4),(0,{'render':'assemble'},7,4),(0,{'render':'assemble'},2,0),(0,{'render':'assemble'},2,5)])
def test_invalid_requests_rejected(a,args):
    with pytest.raises((ValueError,TypeError)):a.generate(*args)

@pytest.mark.parametrize('grid',[[],[[]],[[True]],[[10]],[[0],[0,1]],[[0.0]]])
def test_malformed_grids_rejected(a,grid):
    with pytest.raises((ValueError,TypeError)):a.G.solve(grid,'assemble')

def test_relocated_adapter_needs_only_declared_resources(a,tmp_path):
    contract=json.loads((HOME/'workspace/parametric/promotion.json').read_text())
    for src in [contract['adapter'],*contract['resources']]:
        shutil.copyfile(ROOT/src,tmp_path/Path(src).name)
    b=load(tmp_path/'adapter.py','relocated_assembly_adapter')
    assert b.generate(43,{'render':'first_cavity_piece'},2,4)==a.generate(43,{'render':'first_cavity_piece'},2,4)

def test_two_demo_lesson_requires_global_not_only_local_fit(a):
    # A locally legal tile must sometimes be rejected by the rest of the packing.
    e=a.generate(17,{'render':'first_cavity_piece'},2,4)
    assert any(len(a.G.local_first_candidates(p['input']))>1 for p in e['train'])
