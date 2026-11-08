import importlib.util
import json
from pathlib import Path
import pytest
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def load():
    path = HOME / 'workspace/parametric/prototype.py'
    assert path.exists(), 'translation-only packing family has not been implemented'
    spec = importlib.util.spec_from_file_location('packing_family_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

@pytest.mark.parametrize('split,index', [('train',0),('train',1),('test',0),('test',1)])
def test_all_official_labels(split,index):
    m = load()
    data = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['5dbc8537']
    gold = json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['5dbc8537']
    pair = data[split][index]
    want = pair['output'] if split == 'train' else gold[index]
    assert m.solve(pair['input']) == want

def test_exact_cover_rejects_incompatible_inventory():
    m=load()
    with pytest.raises(ValueError,match='cover'):
        m.pack([[9,0,0,9]], [[[2]]], 0)

def test_exact_cover_detects_two_distinct_tilings():
    m=load()
    with pytest.raises(ValueError,match='ambiguous'):
        m.pack([[0,0]], [[[2]],[[3]]], 0, require_unique=True)

def test_exact_cover_allows_identical_piece_permutations():
    m=load()
    out,records=m.pack([[0,0]],[[[2]],[[2]]],0,require_unique=True)
    assert out == [[2,2]]
    assert len(records)==2

def test_racket_reference_exists_and_has_rule():
    p=HOME/'reference.rkt'
    assert p.exists(), 'missing general Racket reference'
    assert p.read_text().lstrip().startswith('(rule!')

def adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.exists(), 'missing native adapter'
    spec=importlib.util.spec_from_file_location('packing_adapter_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

@pytest.mark.parametrize('demos',[2,3,6])
def test_counts_neutral_inputs_and_unique_labels(demos):
    a=adapter();m=load()
    for seed in (0,17,43):
        x=a.generate(seed,{'frame_policy':'original'},demos,4)
        y=a.generate(seed,{'frame_policy':'first_placed_piece'},demos,4)
        assert len(x['train'])==demos and len(x['test'])==4
        assert [p['input'] for sp in ('train','test') for p in x[sp]] == [p['input'] for sp in ('train','test') for p in y[sp]]
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in x[sp]})==demos+4
        assert any(px['output']!=py['output'] for px,py in zip(x['train'],y['train']))
        for p in x['train']+x['test']:
            assert m.solve(p['input'],require_unique=True)==p['output']
        assert any(len(p['input'])==len(p['input'][0])==30 for p in x['test'])

def test_exact_canonical_bytes_and_sampler_copy():
    a=adapter()
    assert a.program({'frame_policy':'original'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/sampler.py').read_bytes()

@pytest.mark.parametrize('args',[(True,{'frame_policy':'original'},2,4),(0,{},2,4),(0,{'frame_policy':'bad'},2,4),(0,{'frame_policy':'original','secret':1},2,4),(0,{'frame_policy':'original'},1,4),(0,{'frame_policy':'original'},7,4),(0,{'frame_policy':'original'},2,0),(0,{'frame_policy':'original'},2,True)])
def test_invalid_requests_rejected(args):
    with pytest.raises((ValueError,TypeError)):
        adapter().generate(*args)

def test_demo_count_does_not_change_query_bank():
    a=adapter()
    x=a.generate(19,{'frame_policy':'original'},2,4)
    y=a.generate(19,{'frame_policy':'original'},6,4)
    assert x['train']==y['train'][:2]
    assert x['test']==y['test']

def audit_module():
    path=HOME/'workspace/parametric/audit.py'
    assert path.exists(), 'missing executable finite-rival auditor'
    spec=importlib.util.spec_from_file_location('packing_audit_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def test_two_demonstrations_reject_harmful_declared_shortcuts():
    report=audit_module().audit(range(8),(2,3,6))
    assert report['status']=='passed'
    assert report['episodes']==72
    assert report['harmful_survivors']==[]

def test_generator_relocation(tmp_path):
    import subprocess,sys,os
    dst=tmp_path/'generator.py';dst.write_bytes((HOME/'generator.py').read_bytes())
    code="import importlib.util; s=importlib.util.spec_from_file_location('relocated', 'generator.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); g=m.generate(17,103); assert len(g)==len(g[0])==30; print('relocated-ok')"
    result=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,text=True,capture_output=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert 'relocated-ok' in result.stdout

def test_sampler_varies_inventory_count_and_piece_geometry():
    a=adapter();m=load();counts=set();geometries=set()
    for seed in range(16):
        g=a.SAMPLER.generate(seed,0)
        _,_,_,pieces=m.parse(g)
        counts.add(len(pieces))
        geometries.add(tuple(sorted((len(p),len(p[0])) for p in pieces)))
        m.solve(g,require_unique=True)
    assert len(counts)>=2
    assert len(geometries)>=4


def test_last_placed_uses_solved_destination_not_source_order():
    # Sources are 3 then 2 in scan order; solved placement order is 2 then 3.
    g=[[0]*12 for _ in range(10)]
    for r in range(6):g[r][:4]=[9]*4
    g[1][1:3]=[0,0];g[3][1]=g[4][1]=0
    g[0][7]=g[1][7]=3;g[7][7:9]=[2,2]
    want=[[3,3,3,3],[3,2,2,3],[3,3,3,3],[3,3,3,3],[3,3,3,3],[3,3,3,3]]
    assert load().solve(g,'last_placed_piece',require_unique=True)==want


def test_last_setting_is_taught_with_two_demos_and_keeps_matched_queries():
    a=adapter()
    for seed in (0,17,43):
        episodes=[a.generate(seed,{'frame_policy':s},2,4) for s in ('original','first_placed_piece','last_placed_piece')]
        assert len({json.dumps([p['output'] for p in ep['train']]) for ep in episodes})==3
        assert all([p['input'] for p in ep['train']+ep['test']]==[p['input'] for p in episodes[0]['train']+episodes[0]['test']] for ep in episodes)
