"""Private gold parity and native-family regression tests for ray transfer."""
from pathlib import Path
import importlib.util
import json
import sys
import pytest
from reviewer_support import find_root, canonical_pairs, load_selected_generator
ROOT = find_root(__file__)
HOME = ROOT/'generators/public_eval_64efde09'
if not HOME.is_dir(): HOME = load_selected_generator('public_eval_64efde09',root=ROOT)[1].parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec); sys.modules[name]=obj
    spec.loader.exec_module(obj); return obj


def artifact():
    path=HOME/'workspace/parametric/prototype.py'
    assert path.is_file(), 'the native ray-transfer family must be implemented'
    return load('_rays_test_proto',path)


def original_pairs():
    path=ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json'
    if not path.is_file():
        for p in canonical_pairs('public_eval_64efde09',root=ROOT,labeled_only=True):
            yield p['split'],p['pair_index'],p['input'],p['output']
        return
    parent=json.loads(path.read_text())['64efde09']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['64efde09']
    for split in ('train','test'):
        for i,pair in enumerate(parent[split]):
            grid=lambda g:[[int(c) for c in row] for row in g]
            yield split,i,grid(pair['input']),grid(pair.get('output',gold[i] if split=='test' else []))


def test_original_python_labels():
    m=artifact()
    for split,index,inp,out in original_pairs():
        assert m.solve(inp,'boundary') == out,(split,index)


def test_default_is_exact_reference():
    m=artifact()
    assert m.program({'ray_extent':'boundary'}) == (HOME/'reference.rkt').read_text()
    assert m.program({'ray_extent':'source_length'}) != (HOME/'reference.rkt').read_text()


@pytest.mark.parametrize('demos',[2,3,4,5,6])
def test_counts_prefixes_teaching_and_matching(demos):
    m=artifact()
    eps=[m.generate(17,{'ray_extent':s},demos,4) for s in m.SETTINGS]
    assert [p['input'] for p in eps[0]['train']+eps[0]['test']] == [p['input'] for p in eps[1]['train']+eps[1]['test']]
    for s,ep in zip(m.SETTINGS,eps):
        assert len(ep['train']) == demos and len(ep['test']) == 4
        assert len({json.dumps(p['input']) for p in ep['train']+ep['test']}) == demos+4
        small=m.generate(17,{'ray_extent':s},2,1)
        assert small['train']==ep['train'][:2] and small['test']==ep['test'][:1]
        assert not m.ambiguities(ep,s)
        assert len(ep['test'][3]['input'])==len(ep['test'][3]['input'][0])==30


def test_sampler_contract_and_stress():
    m=artifact()
    for seed in range(16):
        for index in (0,1,2,100,103):
            inp=m.base.generate(seed,index)
            assert not m.base.self_check(inp)
        inp=m.generate(seed,{'ray_extent':'boundary'},2,4)['test'][3]['input']
        bg,bars,seeds=m.base.analyze(inp)
        assert len(bars)==4 and len(seeds)==3
        assert sum(len(b['pattern'])*len(b['pattern'][0]) for b in bars)==112
        assert len({m.base.source_connection(p,bars)['gap'] for p in seeds})==3
        assert m.solve(inp,'boundary')!=m.solve(inp,'source_length')


def test_d4_cell_maps_agree_with_grid_transform():
    m=artifact()
    g=[[1,2,3],[4,5,6]]
    for k in range(8):
        out=m.base.turn_grid(g,k)
        for r in range(2):
            for c in range(3):
                rr,cc=m.base.turn_cell((r,c),k,2,3)
                assert out[rr][cc]==g[r][c]
    assert len({json.dumps(m.base.turn_grid(g,k)) for k in range(8)})==8


@pytest.mark.parametrize('args',[(True,{'ray_extent':'boundary'},2,4),(0,{},2,4),(0,{'ray_extent':'bad'},2,4),(0,{'ray_extent':'boundary','extra':1},2,4),(0,{'ray_extent':'boundary'},1,4),(0,{'ray_extent':'boundary'},7,4),(0,{'ray_extent':'boundary'},True,4),(0,{'ray_extent':'boundary'},3,0),(0,{'ray_extent':'boundary'},3,5)])
def test_invalid_requests_fail_closed(args):
    with pytest.raises((ValueError,TypeError)): artifact().generate(*args)


def test_invalid_grids_and_controls():
    m=artifact()
    for grid in ([],[[True]],[[0.0]],[[10]],[[0],[]],[[0]*31]):
        with pytest.raises((ValueError,TypeError)): m.solve(grid,'boundary')
    for kwargs in ({'unknown':1},{'scene_profile':'bad'}):
        with pytest.raises((ValueError,TypeError)): m.base.generate(1,0,**kwargs)


def test_public_first_turn_privacy():
    m=artifact(); ep=m.generate(43,{'ray_extent':'source_length'},3,4)
    full=m.present(ep,91,4)
    assert m.present(ep,91,1)['views']==full['views'][:1]
    changed=json.loads(json.dumps(ep)); changed['settings']='private'; changed['program_solution']='secret'
    for p in changed['test']:p['output']=[[7]]
    assert m.present(changed,91,4)['views']==full['views']
    assert len({tuple(m.present(ep,s,4)['private']['source_indices']) for s in range(20)})>1
    for view in full['views']:
        assert set(view)=={'train','test'} and len(view['test'])==1
        assert set(view['test'][0])=={'input'}


def test_racket_originals_and_fresh_labels():
    m=artifact()
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert identity['protected'] is True
        for split,i,inp,out in original_pairs():
            assert apply(m.program({'ray_extent':'boundary'}),inp)==out,(split,i)
        for s in m.SETTINGS:
            ep=m.generate(43,{'ray_extent':s},2,4)
            for p in ep['train']+ep['test']:
                assert apply(ep['program_solution'],p['input'])==p['output']
    finally: bridge.close()


def test_boundary_normal_beats_a_closer_sideways_bar():
    m=artifact()
    inp=next(inp for split,i,inp,out in original_pairs() if split=='test')
    _,bars,seeds=m.base.analyze(inp)
    seed=next(s for s in seeds if s['cell'][0]==len(inp)-1)
    connection=m.base.source_connection(seed,bars)
    chosen=bars[connection['source_index']]
    assert len(chosen['pattern'])==2, 'bottom marker must look upward, not sideways at the nearer vertical bar'
    assert connection['normal']==(1,0)
    assert connection['gap']==25


def test_each_scene_teaches_reflection_and_port_reversal():
    m=artifact()
    for seed in range(16):
        for index in (0,1,100,103):
            inp=m.base.generate(seed,index)
            for extent in m.SETTINGS:
                out=m.solve(inp,extent);pred=m.rivals(inp,extent)
                for rival in ('rotations_without_reflections','same_index_without_template_reversal'):
                    assert pred[rival]!=out,(seed,index,extent,rival)


def test_audit_tool_and_source_drift(tmp_path):
    path=HOME/'workspace/parametric/audit.py'
    assert path.is_file(), 'reusable source-bound audit is missing'
    tool=load('_rays_audit_test',path)
    report=tool.finite_audit(2)
    assert report['status']=='passed' and report['episodes']==20
    import hashlib
    source=tmp_path/'file.py';source.write_text('before')
    binding={'files':[{'path':'file.py','sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]}
    tool.check_binding(binding,tmp_path)
    source.write_text('after')
    with pytest.raises(ValueError,match='source drift'):tool.check_binding(binding,tmp_path)
