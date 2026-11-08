from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent

def load():
    p=HERE/'family.py'; s=importlib.util.spec_from_file_location('_t699_family',p)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m); return m

def test_canonical_program_is_exact_authority():
    m=load(); assert m.program({'passes':1}) == (HERE/'canonical.rkt').read_text()

def test_cascade_requires_second_pass_and_third_pass_is_different():
    m=load(); g=[[0]*5 for _ in range(5)]
    for r,c in [(0,1),(2,3),(3,0),(4,3)]: g[r][c]=6
    one=m.apply_pass(g); two=m.apply_pass(one); three=m.apply_pass(two)
    assert one[1][2]==6
    assert one[2][1]==0 and two[2][1]==6
    assert two[3][2]==0 and three[3][2]==6

def test_generated_episode_is_distinct_matched_and_teaching_complete():
    m=load()
    a=m.generate(31,{'passes':1},2,4); b=m.generate(31,{'passes':2},2,4)
    assert [p['input'] for p in a['train']+a['test']] == [p['input'] for p in b['train']+b['test']]
    xs=[json.dumps(p['input'],separators=(',',':')) for p in a['train']+a['test']]
    assert len(xs)==len(set(xs))==6
    assert b['certificate']['surviving_settings']==[{'passes':2}]
    assert b['certificate']['surviving_rivals']==[]

def test_large_query_has_substantive_30_square_cascade_content():
    m=load(); ep=m.generate(7,{'passes':2},6,4); p=ep['test'][-1]
    g=p['input']; one=m.apply_pass(g); two=m.apply_pass(one)
    assert (len(g),len(g[0]))==(30,30)
    assert sum(v!=0 for row in g for v in row)>=80
    assert sum(one[r][c]!=two[r][c] for r in range(30) for c in range(30))>=10

def test_bad_requests_fail_closed():
    m=load()
    for args in [(True,{'passes':1},3,4),(0,{'passes':3},3,4),(0,{'passes':1,'x':0},3,4),(0,{'passes':1},1,4),(0,{'passes':1},3,3)]:
        with pytest.raises((TypeError,ValueError)): m.generate(*args)

def test_base_generator_honors_pair_count_dimensions_and_rejects_unknown_controls():
    import importlib.util
    p=HERE.parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('_base699',p); assert s and s.loader
    mod=importlib.util.module_from_spec(s); s.loader.exec_module(mod)
    g=mod.generate(3,0,grid_h=12,grid_w=14,n_pairs=4,palette_size=4,n_distinct_colors=4)
    assert (len(g),len(g[0]))==(12,14)
    cells={v:[] for row in g for v in row if v}
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v: cells.setdefault(v,[]).append((r,c))
    assert len(cells)==4 and all(len(ps)==2 for ps in cells.values())
    assert all(abs(a[0]-b[0])==2 and abs(a[1]-b[1])==2 for a,b in cells.values())
    with pytest.raises(ValueError): mod.generate(0,0,typo_axis=1)
