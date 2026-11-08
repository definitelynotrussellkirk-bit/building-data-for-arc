import importlib.util
import json
from pathlib import Path
import shutil
import pytest

HOME=Path(__file__).resolve().parents[1]

def load(path,name='dock_test_adapter'):
    assert path.is_file(),f'Missing implementation: {path.name}'
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def adapter():return load(HOME/'workspace/parametric/adapter.py')

def fixture():
    g=[[0]*20 for _ in range(20)]
    for r,c,v in [(8,9,1),(8,10,1),(9,11,2),(10,11,2),(11,9,3),(11,10,3),(9,8,4),(10,8,4)]:g[r][c]=v
    for r,c in [(1,1),(1,2),(1,3),(1,4),(2,2),(2,3)]:g[r][c]=2
    for r in (15,16):
        for c in (4,5,6,7):g[r][c]=1
    for r in (17,18):
        for c in (17,18):g[r][c]=5
    return g

def hub():
    g=[[0]*20 for _ in range(20)]
    for r,c,v in [(8,9,1),(8,10,1),(9,11,2),(10,11,2),(11,9,3),(11,10,3),(9,8,4),(10,8,4)]:g[r][c]=v
    return g

def test_literal_neck_alignment_erasure_and_opposite_slots():
    a=adapter();g=fixture();out=hub()
    for r,c in [(8,13),(9,12),(9,13),(10,12),(10,13),(11,13)]:out[r][c]=2
    for r in range(4,8):
        for c in (9,10):out[r][c]=1
    assert a.G.solve(g,'matching')==out
    other=hub()
    for r,c in [(8,6),(9,6),(9,7),(10,6),(10,7),(11,6)]:other[r][c]=2
    for r in range(12,16):
        for c in (9,10):other[r][c]=1
    assert a.G.solve(g,'opposite')==other
    assert g==fixture()

def test_all_original_gold_and_default_exact_reference():
    a=adapter();root=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())
    d=json.loads((root/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['2c181942']
    s=json.loads((root/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['2c181942']
    for p in d['train']+[dict(x,output=y) for x,y in zip(d['test'],s)]:assert a.G.solve(p['input'],'matching')==p['output']
    assert a.program({'docking':'matching'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert (HOME/'reference.rkt').read_bytes()==(HOME/'workspace/parametric/canonical.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,17,43,127])
def test_matched_prefix_stability_novelty_and_teaching(seed):
    a=adapter();e=a.generate(seed,{'docking':'matching'},6,4);f=a.generate(seed,{'docking':'opposite'},6,4)
    assert [p['input'] for s in ('train','test') for p in e[s]]==[p['input'] for s in ('train','test') for p in f[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in e[s]})==10
    for value,ep in [('matching',e),('opposite',f)]:
        for d in range(2,7):
            sub=a.generate(seed,{'docking':value},d,4);assert sub['train']==ep['train'][:d] and sub['test']==ep['test']
        for q in range(1,5):assert a.generate(seed,{'docking':value},2,q)['test']==ep['test'][:q]
        for rival in a.G.RIVALS:assert any(a.G.solve(p['input'],value,rival)!=p['output'] for p in ep['train'][:2]),rival
        for split in ('train','test'):
            for p in ep[split]:assert a.G.self_check(p['input'])==[]
        g=ep['test'][-1]['input'];assert len(g)==30 and len(g[0])==30
        bg=a.G.parse(g)['background'];cells=[(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x!=bg]
        assert min(r for r,c in cells)==min(c for r,c in cells)==0
        assert max(r for r,c in cells)==max(c for r,c in cells)==29
        assert len(cells)>80

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'demos':1},{'demos':7},{'queries':0},{'queries':5},{'queries':True},{'settings':{}},{'settings':{'docking':'no'}},{'settings':{'docking':'matching','extra':1}}])
def test_request_validation(kwargs):
    a=adapter();args=dict(seed=0,settings={'docking':'matching'},demos=2,queries=4);args.update(kwargs)
    with pytest.raises((ValueError,TypeError)):a.generate(**args)

def test_hidden_presentation_is_shuffled_and_count_independent():
    a=adapter();indices=set()
    for seed in range(8):
        b=a.present(seed,{'docking':'opposite'},2,4,presentation_seed=12)
        c=a.present(seed,{'docking':'opposite'},2,1,presentation_seed=12)
        assert b['public'][:1]==c['public'];indices.add(b['private']['source_indices'][0])
        for v in b['public']:assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
        b['public'][0]['train'][0]['input'][0][0]=99
        assert c==a.present(seed,{'docking':'opposite'},2,1,presentation_seed=12)
    assert len(indices)>1

def test_native_resources_survive_relocation(tmp_path):
    src=HOME/'workspace/parametric'
    for name in ['adapter.py','engine.py','canonical.rkt']:shutil.copyfile(src/name,tmp_path/name)
    assert load(tmp_path/'adapter.py','relocated_docking').generate(17,{'docking':'opposite'},2,4)==adapter().generate(17,{'docking':'opposite'},2,4)

@pytest.mark.parametrize('g',[[],[[True]],[[0,1],[0]],[[10]],[[0]*31],[[0]]])
def test_bad_or_out_of_grammar_grids_rejected(g):
    assert adapter().G.self_check(g)
    with pytest.raises(ValueError):adapter().G.solve(g,'matching')

def test_offcenter_edge_is_not_a_neck_and_ambiguous_orientations_fail():
    a=adapter()
    # The fork has two adjacent extreme-side cells, but they are not centered
    # across its height. Only the bottom two-cell stem is the docking neck.
    fork=[[7,0,0,7],[7,7,7,7],[0,7,7,0]]
    up=a.G.orientations(fork,0,0)
    assert up==[fork]
    with pytest.raises(ValueError,match='ambiguous'):
        a.G.orient([[7,7],[7,0]],0,0)

def test_conflicting_docked_piece_cells_rejected_before_labels():
    a=adapter();g=fixture()
    for r in (1,2):
        for c in range(1,9):g[r][c]=0
    for r in (15,16):
        for c in range(4,12):g[r][c]=0
    for color,r0,c0 in [(2,1,1),(1,15,4)]:
        for c in range(8):g[r0][c0+c]=color
        for c in (3,4):g[r0+1][c0+c]=color
    with pytest.raises(ValueError,match='overlap'):a.G.parse(g)
