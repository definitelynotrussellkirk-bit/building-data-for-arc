"""Behavioral tests for frame detection and marker-relative template transfer."""
import importlib.util
import json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]


def load(name='prototype'):
    path=HOME/'workspace/parametric'/(name+'.py')
    assert path.exists(),f'missing {name} implementation'
    spec=importlib.util.spec_from_file_location('_a251_test_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('split,index',[('train',0),('train',1),('test',0)])
def test_all_official_labels(split,index):
    a=load();data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['a251c730']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['a251c730']
    pair=data[split][index]
    assert a.solve(pair['input'])==(pair['output'] if split=='train' else gold[index])


def offset_fixture():
    g=[[(7,8)[c%2] for c in range(24)] for _ in range(16)]
    for r in range(1,11):
        for c in range(1,11):g[r][c]=6 if r in (1,10) or c in (1,10) else 0
    for r in range(2,11):
        for c in range(14,23):g[r][c]=3 if r in (2,10) or c in (14,22) else 9
    for r,c in ((5,5),(8,8)):
        for dr,dc in ((-2,-1),(-2,0),(-1,-1),(-1,0)):g[r+dr][c+dc]=4
        g[r][c]=2
    g[7][18]=2
    return g


def test_unique_marker_not_bounding_box_center_anchors_transfer():
    want=[[3,3,3,3,3,3,3,3,3],
          [3,9,9,9,9,9,9,9,3],
          [3,9,9,9,9,9,9,9,3],
          [3,9,9,4,4,9,9,9,3],
          [3,9,9,4,4,9,9,9,3],
          [3,9,9,9,2,9,9,9,3],
          [3,9,9,9,9,9,9,9,3],
          [3,9,9,9,9,9,9,9,3],
          [3,3,3,3,3,3,3,3,3]]
    assert load().solve(offset_fixture())==want


def test_largest_scope_uses_distinct_template_not_repeat_count():
    g=offset_fixture()
    # Two copies of area-5 marker-2 template versus one area-3 marker-1 template.
    g[8][3]=1;g[7][2]=g[7][3]=5
    g[4][20]=1
    a=load();all_out=a.solve(g);large=a.solve(g,'largest_template')
    assert all_out[1][5:7]==[5,5]
    assert large[1][5:7]==[9,9]
    assert large[2][6]==1
    assert large[3][3:5]==[4,4]


@pytest.mark.parametrize('bad',[[],[[True]],[[1],[1,2]],[[10]],[[0]*31]])
def test_invalid_grids_rejected(bad):
    with pytest.raises(ValueError):load().solve(bad)


def test_unknown_scope_rejected():
    with pytest.raises(ValueError):load().solve(offset_fixture(),'nonsense')


@pytest.mark.parametrize('demos',[2,3,6])
def test_native_counts_inputs_and_boundary(demos):
    a=load('adapter')
    for seed in (0,17,43):
        xs=[a.generate(seed,{'transfer_scope':v},demos,4) for v in ('all_templates','largest_template')]
        assert len(xs[0]['train'])==demos and len(xs[0]['test'])==4
        assert [p['input'] for p in xs[0]['train']+xs[0]['test']]==[p['input'] for p in xs[1]['train']+xs[1]['test']]
        assert any(a['output']!=b['output'] for a,b in zip(xs[0]['train'],xs[1]['train']))
        assert len({json.dumps(p['input']) for p in xs[0]['train']+xs[0]['test']})==demos+4
        assert len(xs[0]['test'][3]['input'])==len(xs[0]['test'][3]['input'][0])==30
        for ep in xs:
            for p in ep['train']+ep['test']:
                assert len(p['output'])<=30 and len(p['output'][0])<=30


def test_native_canonical_exact_and_prefix_stability():
    a=load('adapter')
    assert a.program({'transfer_scope':'all_templates'})==(HOME/'reference.rkt').read_text()
    x=a.generate(7,{'transfer_scope':'largest_template'},2,4)
    y=a.generate(7,{'transfer_scope':'largest_template'},6,4)
    assert x['train']==y['train'][:2] and x['test']==y['test']


@pytest.mark.parametrize('args',[(True,{'transfer_scope':'all_templates'},2,4),(0,{},2,4),(0,{'transfer_scope':'bad'},2,4),(0,{'transfer_scope':'all_templates','private':1},2,4),(0,{'transfer_scope':'all_templates'},1,4),(0,{'transfer_scope':'all_templates'},7,4),(0,{'transfer_scope':'all_templates'},2,1),(0,{'transfer_scope':'all_templates'},True,4)])
def test_invalid_native_requests(args):
    with pytest.raises((ValueError,TypeError)):load('adapter').generate(*args)


def test_generator_is_standalone_when_relocated(tmp_path):
    import subprocess,sys
    path=HOME/'generator.py';assert path.exists()
    (tmp_path/'generator.py').write_bytes(path.read_bytes())
    code="import generator;g=generator.generate(17,103);assert len(g)==len(g[0])==30;print('relocated-ok')"
    p=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stderr
    assert 'relocated-ok' in p.stdout


def test_crop_frame_and_existing_markers_survive_clipped_stamp():
    g=offset_fixture();g[7][18]=9;g[3][15]=2
    out=load().solve(g)
    assert out[1][1]==2
    assert out[0]==[3]*9 and out[-1]==[3]*9
    assert all(row[0]==row[-1]==3 for row in out)


def test_two_demo_lessons_reject_declared_harmful_rivals():
    report=load('audit').audit(range(8),(2,3,6))
    assert report['status']=='passed',report['harmful_survivors']
    assert report['episodes']==48


def test_equal_largest_templates_all_transfer():
    g=offset_fixture()
    for r,c in ((6,2),(6,3),(7,2),(7,3)):g[r][c]=5
    g[8][3]=1;g[4][20]=1
    a=load();out=a.solve(g,'largest_template')
    assert out==a.solve(g,'all_templates')
    assert out[1][5:7]==[5,5]


def test_inconsistent_repeated_template_rejected():
    g=offset_fixture();g[6][7]=5
    with pytest.raises(ValueError,match='inconsistent'):load().solve(g)


def test_marker_without_source_template_rejected():
    g=offset_fixture();g[4][20]=1
    with pytest.raises(ValueError,match='every target'):load().solve(g)


@pytest.mark.parametrize('turns,mirror',[(r,m) for r in range(4) for m in (False,True)])
def test_whole_scene_symmetries_preserve_cropped_semantics(turns,mirror):
    a=load('adapter');core=load()
    grid=a.generate(31,{'transfer_scope':'all_templates'},2,4)['test'][2]['input']
    def transform(g):
        g=[row[::-1] for row in g] if mirror else [row[:] for row in g]
        for _ in range(turns):g=[list(row) for row in zip(*g[::-1])]
        return g
    for scope in ('all_templates','largest_template'):
        assert core.solve(transform(grid),scope)==transform(core.solve(grid,scope))


@pytest.mark.parametrize('overrides',[{'height':23},{'width':31},{'rotation':4},{'height':True},{'unknown':3}])
def test_generator_rejects_invalid_geometry(overrides):
    with pytest.raises(ValueError):load('sampler').generate(0,0,**overrides)
