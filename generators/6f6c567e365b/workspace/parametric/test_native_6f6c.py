from __future__ import annotations
import importlib.util, json, sys, hashlib
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent

def load():
    p=HERE/'family.py'; s=importlib.util.spec_from_file_location('_t6f_family',p)
    assert s and s.loader
    m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m); return m

def test_canonical_program_is_exact_authority():
    m=load(); text=(HERE/'canonical.rkt').read_text()
    assert m.program({'gallery_mode':'cumulative'}) == text
    assert hashlib.sha256(text.encode()).hexdigest() == '33361398d469a728c0dc9cf6e18334879d3ed11c694bc04ca6e5d1f1a061e87c'

def test_hand_script_is_cumulative_and_projection_uses_final_cue():
    m=load()
    crop=[[5,6,7],[8,9,5]]
    keys=[1,3]
    states=m.script_states(crop,keys)
    assert states[1] == [[8,5],[9,6],[5,7]]
    assert states[2] == [[5,8],[6,9],[7,5]]
    assert m.final_cue_color(crop,keys) == 5
    projected=m.project_color(crop,5)
    assert projected == [[5,0,0],[0,0,5]]

def test_generated_episode_is_distinct_matched_and_teaching_complete():
    m=load()
    a=m.generate(17,{'gallery_mode':'cumulative'},3,4)
    b=m.generate(17,{'gallery_mode':'final_cue_projection'},3,4)
    assert [p['input'] for p in a['train']+a['test']] == [p['input'] for p in b['train']+b['test']]
    xs=[json.dumps(p['input'],separators=(',',':')) for p in a['train']+a['test']]
    assert len(xs)==len(set(xs))==7
    assert b['certificate']['surviving_settings']==[{'gallery_mode':'final_cue_projection'}]
    assert b['certificate']['surviving_rivals']==[]
    assert all(p['output']==m.label(p['input'],'final_cue_projection') for p in b['train']+b['test'])

def test_large_query_is_lawful_30_square_and_outputs_fit_arc_limit():
    m=load(); ep=m.generate(23,{'gallery_mode':'final_cue_projection'},6,4)
    p=ep['test'][-1]; g=p['input']; out=p['output']
    assert (len(g),len(g[0]))==(30,30)
    assert len(out)<=30 and len(out[0])<=30
    assert any(g[0][c] for c in (0,29))
    assert sum(v!=0 for row in g for v in row)>=24

def test_bad_requests_fail_closed():
    m=load()
    for args in [
        (True,{'gallery_mode':'cumulative'},3,4),
        (0,{'gallery_mode':'bad'},3,4),
        (0,{'gallery_mode':'cumulative','x':1},3,4),
        (0,{'gallery_mode':'cumulative'},1,4),
        (0,{'gallery_mode':'cumulative'},3,3),
    ]:
        with pytest.raises((TypeError,ValueError)): m.generate(*args)

def test_base_generator_honors_exact_controls_and_uses_asymmetric_multicolor_motif():
    import importlib.util
    p=HERE.parents[1]/'generator.py'
    s=importlib.util.spec_from_file_location('_base6f',p); assert s and s.loader
    mod=importlib.util.module_from_spec(s); s.loader.exec_module(mod)
    g=mod.generate(5,0,grid_h=14,grid_w=16,n_codes=4,palette_size=3,n_distinct_colors=3)
    assert (len(g),len(g[0]))==(14,16)
    assert sum(v!=0 for v in g[0])==4 and all(v==0 for v in g[1])
    colors={v for row in g[2:] for v in row if v}
    assert len(colors)==3
    keys,crop=load()._parse(g)
    assert any(load().transform(crop,k)!=crop for k in keys)
    with pytest.raises(ValueError): mod.generate(0,0,typo_axis=1)
