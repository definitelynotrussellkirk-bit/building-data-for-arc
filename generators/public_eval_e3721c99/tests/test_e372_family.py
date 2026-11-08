"""Public parent topology/legend family: independent literal and original checks."""
from pathlib import Path
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1]
def load():
    p=HOME/'workspace/parametric/adapter.py'
    assert p.is_file(),'The topology adapter must be implemented'
    spec=importlib.util.spec_from_file_location('e372_test_adapter',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_all_original_labels():
    m=load();p=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['e3721c99']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['e3721c99']
    pairs=p['train']+[{'input':q['input'],'output':a} for q,a in zip(p['test'],gold)]
    for pair in pairs:
        g=[[int(v) for v in row] for row in pair['input']]
        answer=[[int(v) for v in row] for row in pair['output']]
        assert m.solve(g,'exact')==answer

@pytest.mark.parametrize('mask,count',[
    ([[1,1,1],[1,0,1],[1,1,1]],1),
    ([[1,1,1],[1,0,0],[1,1,1]],0),
    ([[0,1,1],[1,0,1],[1,1,1]],1),
    ([[1,1,1,1,1],[1,0,1,0,1],[1,1,1,1,1]],2),
    ([[1,1,1,1],[1,0,0,1],[1,1,1,1]],1),
    ([[1,1],[1,1]],0),
])
def test_enclosed_four_connected_regions(mask,count):
    m=load();cells=[(r,c) for r,row in enumerate(mask) for c,v in enumerate(row) if v]
    assert len(m.holes(cells))==count

def test_exact_default_bytes():
    assert load().program({'lookup':'exact'}).encode()==(HOME/'reference.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,17,43,144])
def test_sampler_counts_prefixes_settings_and_stress(seed):
    m=load()
    full=m.generate(seed,{'lookup':'exact'},2,4)
    for demos in range(2,7):
        a=m.generate(seed,{'lookup':'exact'},demos,4);b=m.generate(seed,{'lookup':'nearest_lower'},demos,4)
        assert len(a['train'])==demos and a['test']==full['test']
        assert all(p['input']==q['input'] for sp in ('train','test') for p,q in zip(a[sp],b[sp]))
        assert any(p['output']!=q['output'] for p,q in zip(a['train'],b['train']))
        assert len({json.dumps(p['input']) for sp in ('train','test') for p in a[sp]})==demos+4
        assert len(a['test'][3]['input'])==len(a['test'][3]['input'][0])==30
        assert sum(v!=0 for row in a['test'][3]['input'] for v in row)>150
        for n in range(1,5):assert m.generate(seed,{'lookup':'exact'},demos,n)['test']==full['test'][:n]

@pytest.mark.parametrize('args',[(True,{'lookup':'exact'},2,4),(0,{'lookup':'exact'},True,4),(0,{'lookup':'exact'},2,False),(0,{'lookup':'exact'},1,4),(0,{'lookup':'exact'},7,4),(0,{'lookup':'exact'},2,0),(0,{'lookup':'exact'},2,5),(0,{'lookup':'invalid'},2,4),(0,{'lookup':'exact','extra':1},2,4)])
def test_bad_requests_fail_closed(args):
    with pytest.raises((TypeError,ValueError)):load().generate(*args)

def test_public_turn_is_masked_and_order_is_private():
    m=load();e=m.generate(17,{'lookup':'nearest_lower'},2,4)
    v=m.public_views(e,presentation_seed=7)
    assert len(v)==4 and all(set(x)=={'train','test'} and len(x['test'])==1 and set(x['test'][0])=={'input'} for x in v)
    assert m.public_views(e,presentation_seed=7,limit=1)==v[:1]
    e['program_solution']='hidden';e['settings']={'secret':1};e['seed']=100
    for p in e['test']:p['output']=[[9]]
    assert m.public_views(e,presentation_seed=7)==v
    assert len({json.dumps(m.public_views(e,presentation_seed=i)[0]['test']) for i in range(32)})==4

def test_legend_palette_not_fixed_to_hole_rank():
    m=load();e=m.generate(17,{'lookup':'exact'},2,4)
    mappings=[m.parse(p['input'])[0] for p in e['train']]
    ordered=[[d[k] for k in sorted(d)] for d in mappings]
    assert any(v==sorted(v) for v in ordered)
    assert any(v==sorted(v,reverse=True) for v in ordered)

@pytest.mark.parametrize('bad',[[],[[True]],[[1],[2,3]],[[10]],[[1.0]]])
def test_bad_grids_are_rejected(bad):
    with pytest.raises(ValueError):load().solve(bad)


def test_base_generator_runs_when_only_generator_file_is_relocated(tmp_path):
    import shutil
    target=tmp_path/'puzzle_generators/per_puzzle'/HOME.name/'generator.py'
    target.parent.mkdir(parents=True)
    shutil.copyfile(HOME/'generator.py',target)
    spec=importlib.util.spec_from_file_location('isolated_base_'+HOME.name,target)
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    a=base.generate(29,0);b=base.generate(29,0)
    assert a==b and base.self_check(a)==[]
    assert base.generate(29,6)!=a
    expected=load().solve(a,load().SETTINGS[0])
    assert expected and len(expected)==len(a)
