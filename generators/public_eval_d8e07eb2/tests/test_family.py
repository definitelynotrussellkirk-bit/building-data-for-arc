"""Behavioral tests; original parity is explicitly six of seven, never relabeled."""
from pathlib import Path
import copy
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]

def load():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(), 'Implement the native adapter'
    s=importlib.util.spec_from_file_location('_d8_tests',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def manual(kind):
    # Independent 2x2 literal shape fixture. Tile rows 7..8 / 11..12;
    # columns 2..3 / 6..7. Header 0..3, separators 4 and 14, footer 15..16.
    shapes=[[[1,8],[1,1]], [[4,4],[4,8]], [[5,5],[8,5]], [[7,8],[8,7]]]
    selected={'row':[0,1],'col':[0,2],'no_line':[0,3]}[kind]
    g=[[8]*10 for _ in range(17)]
    g[4]=[6]*10;g[14]=[6]*10
    for i,shape in enumerate(shapes):
        for r,row in enumerate(shape):
            for c,v in enumerate(row):g[7+4*(i//2)+r][2+4*(i%2)+c]=v
    for j,i in enumerate(selected):
        for r,row in enumerate(shapes[i]):
            for c,v in enumerate(row):g[1+r][2+4*j+c]=v
    out=copy.deepcopy(g)
    for i in selected:
        for r in range(6+4*(i//2),10+4*(i//2)):
            for c in range(1+4*(i%2),5+4*(i%2)):
                if out[r][c]==8:out[r][c]=3
    win=kind!='no_line'
    if win:
        for r in range(4):out[r]=[3 if v==8 else v for v in out[r]]
    for r in (15,16):out[r]=[3 if win else 2]*10
    return g,out

@pytest.mark.parametrize('kind',['row','col','no_line'])
def test_manual_geometry_and_status(kind):
    g,want=manual(kind);before=copy.deepcopy(g)
    assert load().solve(g,'color_shape')==want
    assert g==before

def originals():
    retained=HOME/'evidence/original-rule-recovery/originals.json'
    if retained.is_file():
        parent=json.loads(retained.read_text())
        gold=[pair['output'] for pair in parent['test']]
    else:
        parent=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['d8e07eb2']
        gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['d8e07eb2']
    rows=[]
    for split in ('train','test'):
        for i,p in enumerate(parent[split]):
            out=p.get('output',gold[i] if split=='test' else None)
            rows.append((split,i,[[int(v) for v in row] for row in p['input']],[[int(v) for v in row] for row in out]))
    return rows

@pytest.mark.parametrize('split,index,g,want',originals(),ids=[f'{s}-{i}' for s,i,_,_ in originals()])
def test_all_supplied_original_labels(split,index,g,want):
    actual=load().solve(g,'color_shape')
    if (split,index)==('train',0):
        differences=[(r,c,v,want[r][c]) for r,row in enumerate(actual) for c,v in enumerate(row) if v!=want[r][c]]
        assert differences==[(1,7,1,2),(1,8,1,2),(1,9,1,3),(2,7,3,2),(2,8,1,2),(2,9,3,2),(3,7,1,3),(3,8,1,2),(3,9,1,3)]
    else:
        assert actual==want

def test_canonical_identity():
    m=load()
    assert m.program({'match':'color_shape'}).encode()==(HOME/'reference.rkt').read_bytes()
    assert m.program({'match':'shape_only'})!=m.program({'match':'color_shape'})
    assert m._core.RULE_TASK_ID=='ee_d8e07eb2'

@pytest.mark.parametrize('seed',[0,1,17,43,127])
def test_full_episode_contract(seed):
    m=load()
    for nd in (4,5,6):
        a=m.generate(seed,{'match':'color_shape'},nd,4)
        b=m.generate(seed,{'match':'shape_only'},nd,4)
        assert [p['input'] for sp in ('train','test') for p in a[sp]]==[p['input'] for sp in ('train','test') for p in b[sp]]
        assert any(p['output']!=q['output'] for p,q in zip(a['train'],b['train']))
        assert len(a['train'])==nd and len(a['test'])==4
        for ep in (a,b):
            assert len({json.dumps(p['input']) for sp in ('train','test') for p in ep[sp]})==nd+4
            assert any(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
            for n in (1,2,3,4):assert m.generate(seed,{'match': 'color_shape' if ep is a else 'shape_only'},nd,n)['test']==ep['test'][:n]
        assert a['test']==m.generate(seed,{'match':'color_shape'},4,4)['test']
        for mode in m.SETTINGS:
            ep=a if mode=='color_shape' else b
            for rival in m.RIVALS:
                if all(m.solve(p['input'],mode,rival=rival)==p['output'] for p in ep['train']):
                    assert all(m.solve(p['input'],mode,rival=rival)==p['output'] for p in ep['test']),rival

@pytest.mark.parametrize('args',[(True,{'match':'color_shape'},4,4),(-1,{'match':'color_shape'},4,4),(0,{'match':'color_shape'},True,4),(0,{'match':'color_shape'},3,4),(0,{'match':'color_shape'},7,4),(0,{'match':'color_shape'},4,0),(0,{'match':'color_shape'},4,5),(0,{'match':False},4,4),(0,{'match':'color_shape','extra':0},4,4)])
def test_invalid_requests(args):
    with pytest.raises((TypeError,ValueError)):load().generate(*args)

@pytest.mark.parametrize('g',[[],[[True]],[[1.0]],[[1],[1,2]],[[10]],[[8]*5 for _ in range(5)]])
def test_invalid_grid(g):
    with pytest.raises(ValueError):load().solve(g)

def test_public_privacy_and_full_bank_prefix():
    m=load();ep=m.generate(43,{'match':'shape_only'},4,4)
    views=m.public_views(ep,presentation_seed=4)
    assert len(views)==4 and all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)
    assert views[:1]==m.public_views(ep,presentation_seed=4,limit=1)
    other=copy.deepcopy(ep);other['settings']={'hidden':'secret'};other['program_solution']='changed'
    for p in other['test']:p['output']=[[9]]
    assert m.public_views(other,presentation_seed=4)==views
    assert len({json.dumps(m.public_views(ep,presentation_seed=i,limit=1)[0]['test']) for i in range(32)})==4
    with pytest.raises(ValueError):m.public_views(m.generate(0,{'match':'color_shape'},4,1),presentation_seed=0)

def test_base_only_relocation(tmp_path):
    import shutil
    p=tmp_path/'base.py';shutil.copyfile(HOME/'generator.py',p)
    s=importlib.util.spec_from_file_location('_d8_relocated',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    g=m.generate(17,0,difficulty=None);assert m.generate(17,0)==g and m.self_check(g)==[]
    assert m.generate(17,1)!=g

def test_native_resource_relocation(tmp_path):
    import shutil
    home=tmp_path/'generators'/HOME.name
    shutil.copytree(HOME/'workspace/parametric',home/'workspace/parametric')
    p=home/'workspace/parametric/adapter.py';s=importlib.util.spec_from_file_location('_d8_native_relocated',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    assert m.program({'match':'color_shape'}).encode()==(HOME/'reference.rkt').read_bytes()
    lesson=m.generate(11,{'match':'shape_only'},4,4)
    assert len(lesson['test'])==4
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/kernel.py').read_bytes()

def test_query_geometry_is_not_fixed_by_query_index():
    m=load()
    positions=set()
    for seed in range(32):
        ep=m.generate(seed,{'match':'color_shape'},4,4)
        positions.update(i for i,p in enumerate(ep['test']) if len(p['input'])==len(p['input'][0])==30)
    assert positions=={0,1,2,3}
