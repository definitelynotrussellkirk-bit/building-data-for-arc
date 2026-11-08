import copy
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'

def load(name='model',path=None):
    path=path or BASE/(name+'.py')
    assert path.is_file(),f'missing implementation: {path.name}'
    spec=importlib.util.spec_from_file_location('_holes_'+name+str(path).encode().hex(),path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

@pytest.mark.parametrize('index',range(4))
def test_originals(index):
    p=json.loads((HOME/'tests/fixtures/originals.json').read_text())['pairs'][index]
    assert load().solve(p['input'])==p['output']

def literal():
    # Top-edge legend: 2->3, 3->4, 6->6. Red holes of size 1 and 2;
    # a gray hole has no key and must stay black. Outer black is not filled.
    g=[[0]*16 for _ in range(10)]
    g[0][5:8]=[2,3,6];g[1][5:8]=[3,4,6]
    for c0,w,color in [(0,3,2),(5,4,2),(12,3,5)]:
        for r in range(4,7):
            for c in range(c0,c0+w):
                if r in (4,6) or c in (c0,c0+w-1):g[r][c]=color
    return g

def test_literal_holes_mapping_and_largest_per_color():
    m=load();g=literal();all_want=copy.deepcopy(g);largest=copy.deepcopy(g)
    all_want[5][1]=3
    for c in (6,7):all_want[5][c]=3;largest[5][c]=3
    assert m.solve(g,'all')==all_want
    assert m.solve(g,'largest_per_color')==largest

def test_legend_is_read_inward_on_all_four_edges():
    m=load();g=literal();want=copy.deepcopy(g);want[5][1]=3;want[5][6]=want[5][7]=3
    for _ in range(4):
        assert m.solve(g)==want
        g=[list(row) for row in zip(*g[::-1])];want=[list(row) for row in zip(*want[::-1])]

def test_open_region_does_not_become_a_hole():
    m=load();g=literal();g[4][1]=0;out=m.solve(g)
    assert out[5][1]==0 and out[5][6]==out[5][7]==3

def test_largest_ties_all_fill_across_distinct_objects():
    m=load();g=literal();g[4][8]=g[5][8]=g[6][8]=0;g[5][7]=2
    # Now both red holes are singletons in separate components.
    out=m.solve(g,'largest_per_color')
    assert out[5][1]==out[5][6]==3

def test_diagonal_boundary_encloses_a_four_connected_hole():
    m=load();g=[[0]*11 for _ in range(10)];g[0][5:8]=[2,3,6];g[1][5:8]=[3,4,6]
    for r,c in [(4,2),(5,1),(5,3),(6,2)]:g[r][c]=2
    want=copy.deepcopy(g);want[5][2]=3
    assert m.solve(g)==want

@pytest.mark.parametrize('demos',[3,4,6])
def test_count_determinism_matched_inputs_and_substantive_stress(demos):
    a=load('adapter');m=load()
    for seed in (0,17,43):
        x=a.generate(seed,{'fill_scope':'all'},demos,4)
        y=a.generate(seed,{'fill_scope':'largest_per_color'},demos,4)
        assert x==a.generate(seed,{'fill_scope':'all'},demos,4)
        assert len(x['train'])==demos and len(x['test'])==4
        inputs=lambda e:[p['input'] for split in ('train','test') for p in e[split]]
        assert inputs(x)==inputs(y) and len({json.dumps(g) for g in inputs(x)})==demos+4
        assert x['train'][0]['output']!=y['train'][0]['output']
        assert x['train'][:3]==a.generate(seed,{'fill_scope':'all'},3,4)['train']
        stress=[p['input'] for p in a.BANKS[0].generate(seed,{'fill_scope':'all'},3,4)['test'] if len(p['input'])==len(p['input'][0])==30]
        assert len(stress)==1
        data=m.analyze(stress[0]);bg=data['background']
        cells=[(r,c) for r,row in enumerate(stress[0]) for c,v in enumerate(row) if v!=bg]
        assert min(r for r,c in cells)==min(c for r,c in cells)==0
        assert max(r for r,c in cells)==max(c for r,c in cells)==29
        assert len(cells)>=100 and len(data['regions'])>=6

@pytest.mark.parametrize('field,value',[('seed',True),('seed',-1),('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',True)])
def test_invalid_requests(field,value):
    args={'seed':17,'settings':{'fill_scope':'all'},'demos':3,'queries':4};args[field]=value
    with pytest.raises(ValueError):load('adapter').generate(**args)

@pytest.mark.parametrize('settings',[{}, {'fill_scope':'bad'},{'fill_scope':True},{'fill_scope':'all','extra':0}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):load('adapter').generate(0,settings,2,4)

def test_program_default_is_exact_reference():
    a=load('adapter')
    assert a.program({'fill_scope':'all'})==(HOME/'reference.rkt').read_text()
    assert a.program({'fill_scope':'largest_per_color'})!=a.program({'fill_scope':'all'})

def test_generator_standalone_and_no_mutation(tmp_path):
    import random
    source=HOME/'generator.py';assert source.is_file()
    target=tmp_path/'alone.py';target.write_bytes(source.read_bytes());m=load('alone',target)
    state=random.getstate()
    for i in range(4):
        g=m.generate(17,i,difficulty='medium');before=copy.deepcopy(g)
        assert m.self_check(g)==[] and m.solve(g)==load().solve(g)
        assert g==before
    assert state==random.getstate()

def test_originals_in_protected_racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(HOME.parents[1]/'shared/runtime')
    try:
        assert identity['protected'] is True
        for p in json.loads((HOME/'tests/fixtures/originals.json').read_text())['pairs']:
            assert apply((HOME/'reference.rkt').read_text(),p['input'])==p['output']
    finally:bridge.close()

def test_finite_rival_teaching_and_counts():
    report=load('audit').audit([0,17,31],[3,4,6])
    assert report['status']=='passed' and report['failures']==[]
    assert report['episodes']==18 and report['pairs']==150
    assert report['max_size_episodes']==18 and len(report['rivals'])>=18

def test_sampler_spans_all_edges_and_preserves_topology():
    m=load();edges=set();backgrounds=set()
    for seed in range(16):
        for i in range(4):
            g=m.scene(seed,i,query=True);assert m.self_check(g)==[]
            data=m.analyze(g);backgrounds.add(data['background']);box=data['legend']['bbox']
            if data['legend']['horizontal']:edges.add('top' if box[0]==0 else 'bottom')
            else:edges.add('left' if box[1]==0 else 'right')
            assert len(data['regions'])>=6
            assert any(r['color'] not in data['legend']['mapping'] for r in data['regions'])
            assert any(r['area']!=r['bbox_area'] for r in data['regions'])
    assert edges=={'top','bottom','left','right'} and len(backgrounds)>=8

def test_minimum_lesson_excludes_hole_box_painting_regression():
    audit=load('audit')
    for seed in (0,17,31):
        setting={'fill_scope':'largest_per_color'};e=audit.a.generate(seed,setting,3,4)
        assert any(audit.predict(p['input'],'paint_hole_boxes',setting)!=p['output'] for p in e['train'])
