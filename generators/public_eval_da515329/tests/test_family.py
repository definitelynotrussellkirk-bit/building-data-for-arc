"""Original fixtures are author-private; tests catch radius/turn/clipping defects."""
from pathlib import Path
import copy
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'

def load(name='engine'):
    p=BASE/(name+'.py')
    assert p.exists(), 'missing implementation '+name
    s=importlib.util.spec_from_file_location('_spiral_test_'+name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def cross(h,w,r,c,k=1,color=8):
    g=[[0]*w for _ in range(h)]
    for t in range(1,k+1):
        for dr,dc in [(-1,0),(0,1),(1,0),(0,-1)]:g[r+t*dr][c+t*dc]=color
    return g

def test_every_supplied_label_and_nonmutation():
    m=load();originals=json.loads((HOME/'tests/originals.json').read_text())
    for split in originals.values():
        for p in split:
            g=copy.deepcopy(p['input'])
            assert m.solve(g,'clockwise')==p['output']
            assert g==p['input']

def test_three_cell_radius_has_inward_elbow_not_square_spiral():
    m=load();g=cross(22,22,9,9,3)
    info=m.analyze(g)
    assert info=={'center':[9,9],'arm_length':3,'color':8}
    out=m.solve(g,'clockwise')
    assert out[6][11]==8 and out[7][11]==8 and out[7][14]==8
    assert out[6][12]==0 and out[8][10]==0

def test_ray_reenters_after_leaving_canvas():
    # Official radius-three case has an isolated lower-right corner from a
    # later contour segment; stopping each ray on first exit loses it.
    m=load();out=m.solve(cross(22,22,9,9,3),'clockwise')
    assert out[21][21]==8 and out[20][21]==0 and out[21][20]==0

def test_radius_one_and_two_share_spacing_two_geometry():
    m=load()
    assert m.solve(cross(13,17,5,7,1),'clockwise')==m.solve(cross(13,17,5,7,2),'clockwise')

def test_counterclockwise_is_horizontal_reflection_conjugate():
    m=load();g=cross(19,23,7,10,4,6)
    reflected=[row[::-1] for row in g]
    assert m.solve(g,'counterclockwise')==[row[::-1] for row in m.solve(reflected,'clockwise')]
    assert m.solve(g,'clockwise')!=m.solve(g,'counterclockwise')

@pytest.mark.parametrize('g',[[],[[True]],[[1.0]],[[10]],[[0]],[[1,0],[0]],[[8,8],[0,0]]])
def test_invalid_grammar_fails_closed(g):
    with pytest.raises(ValueError):load().solve(g,'clockwise')

def test_engine_matches_relocatable_base():
    assert (HOME/'generator.py').read_bytes()==(BASE/'engine.py').read_bytes()

def test_all_counts_matched_input_prefixes_distinct_queries():
    a=load('adapter');e=load()
    for seed in range(8):
        bank=a.generate(seed,{'turn':'clockwise'},6,4)
        assert len({json.dumps(p['input']) for s in ('train','test') for p in bank[s]})==10
        other=a.generate(seed,{'turn':'counterclockwise'},6,4)
        for split in ('train','test'):
            assert [p['input'] for p in bank[split]]==[p['input'] for p in other[split]]
        for n in range(2,7):
            ep=a.generate(seed,{'turn':'clockwise'},n,4)
            assert ep['train']==bank['train'][:n] and ep['test']==bank['test']
            assert a.generate(seed,{'turn':'clockwise'},n,1)['test']==bank['test'][:1]
        assert e.analyze(bank['train'][0]['input'])['arm_length']==1
        assert e.analyze(bank['train'][1]['input'])['arm_length']>=3
        assert any(x['output']!=y['output'] for x,y in zip(bank['train'][:2],other['train'][:2]))
        stress=bank['test'][3]
        assert (len(stress['input']),len(stress['input'][0]))==(30,30)
        assert sum(v!=0 for row in stress['output'] for v in row)>300

def test_program_default_is_exact_canonical():
    a=load('adapter')
    assert a.program({'turn':'clockwise'})==(HOME/'reference.rkt').read_text()
    assert a.program({'turn':'clockwise'})==(BASE/'canonical.rkt').read_text()
    assert a.program({'turn':'counterclockwise'})!=a.program({'turn':'clockwise'})

@pytest.mark.parametrize('kw',[
    {'seed':True},{'seed':-1},{'seed':1.5},{'demos':True},{'demos':1},{'demos':7},
    {'queries':False},{'queries':0},{'queries':5},{'settings':{}},
    {'settings':{'turn':'clockwise','private':0}},{'settings':{'turn':'bad'}}])
def test_invalid_requests_are_rejected(kw):
    args={'seed':0,'settings':{'turn':'clockwise'},'demos':2,'queries':4};args.update(kw)
    with pytest.raises(ValueError):load('adapter').generate(**args)
