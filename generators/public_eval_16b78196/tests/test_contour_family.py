"""Regression expectations come from original labels and observable contracts."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw').is_dir())

def load(name):
    path=HOME/'workspace/parametric'/f'{name}.py'
    assert path.is_file(), f'missing implementation: {name}'
    spec=importlib.util.spec_from_file_location('contour_test_'+name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def originals():
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['16b78196']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['16b78196']
    return data['train']+[{'input':p['input'],'output':o} for p,o in zip(data['test'],gold)]

@pytest.mark.parametrize('index',range(3))
def test_original_labels(index):
    p=originals()[index]
    assert load('model').solve(p['input'])==p['output']

def test_original_chain_depths_and_nonmutating_solution():
    m=load('model');p=originals()[2];before=copy.deepcopy(p['input']);info=m.analyze(p['input'])
    assert sorted(s['depth'] for s in info['steps'])==[1,1,2,2,3]
    assert m.solve(p['input'],'highlight_deepest')!=p['output']
    assert p['input']==before

@pytest.mark.parametrize('g',[[],[[True]],[[0],[0,0]],[[10]],[[0,0],[0,0]]])
def test_invalid_grids_fail_closed(g):
    with pytest.raises(ValueError):load('model').solve(g)

def test_source_reading_order_cannot_choose_a_dead_end_fit():
    m=load('model');p=originals()[1];g=copy.deepcopy(p['input']);pieces=m.parts(g)[2]
    blue=next(o for o in pieces if o['color']==1);yellow=next(o for o in pieces if o['color']==4)
    for o in (blue,yellow):
        for r,c in o['cells']:g[r][c]=0
    for o,dest in ((blue,yellow['origin']),(yellow,blue['origin'])):
        for r,c in o['local']:g[dest[0]+r][dest[1]+c]=o['color']
    assert m.solve(g)==p['output']

@pytest.mark.parametrize('seed',[0,17,43])
@pytest.mark.parametrize('demos',[2,3,6])
def test_episode_counts_prefixes_matched_settings_and_stress(seed,demos):
    a=load('adapter');base=a.generate(seed,{'finish':'assemble_only'},2,4)
    ep=a.generate(seed,{'finish':'assemble_only'},demos,4);alt=a.generate(seed,{'finish':'highlight_deepest'},demos,4)
    assert ep['train'][:2]==base['train'] and ep['test']==base['test']
    inputs=[p['input'] for s in ('train','test') for p in ep[s]]
    assert inputs==[p['input'] for s in ('train','test') for p in alt[s]]
    assert len({json.dumps(g) for g in inputs})==demos+4
    assert any(p['output']!=q['output'] for p,q in zip(ep['train'],alt['train']))
    assert any(len(g)==len(g[0])==30 for g in inputs)
    assert a.program({'finish':'assemble_only'})==(HOME/'reference.rkt').read_text()

@pytest.mark.parametrize('args',[(True,{'finish':'assemble_only'},3,4),(-1,{'finish':'assemble_only'},3,4),(0,{'finish':'assemble_only'},1,4),(0,{'finish':'assemble_only'},7,4),(0,{'finish':'assemble_only'},3,3),(0,{'finish':True},3,4),(0,{'finish':'assemble_only','extra':0},3,4)])
def test_invalid_native_contract(args):
    with pytest.raises(ValueError):load('adapter').generate(*args)

@pytest.mark.parametrize('orientation',range(8))
def test_exact_rectangular_controls_and_constructed_ground_truth(orientation):
    s=load('sampler');m=load('model')
    g,want=s.construct(17,0,split='production',grid_h=24,grid_w=30,orientation_id=orientation)
    assert (len(g),len(g[0]))==(24,30)
    assert m.solve(g)==want

def test_short_demonstrations_refute_declared_rivals():
    a=load('adapter');m=load('model')
    for seed in range(12):
        for finish in ('assemble_only','highlight_deepest'):
            ep=a.generate(seed,{'finish':finish},2,4)
            for name in m.rivals(finish):
                assert any(m.rival(p['input'],finish,name)!=p['output'] for p in ep['train']), (seed,finish,name)

@pytest.mark.parametrize('seed',[14,44,52])
def test_final_orientation_must_not_leak_deepest_by_source_reading_order(seed):
    a=load('adapter');ep=a.generate(seed,{'finish':'highlight_deepest'},2,4)
    for name in ('first_reading','last_reading'):
        assert any(a.model.rival(p['input'],'highlight_deepest',name)!=p['output'] for p in ep['train'])

def test_public_projection_is_independent_of_hidden_fields():
    f=load('family');ep=f.generate(17,{'finish':'assemble_only'},2,4);before=f.public_view(ep,0)
    changed=copy.deepcopy(ep);changed['program_solution']='secret';changed['test'][0]['output']=True;changed['test'][1:]=[{}]
    assert f.public_view(changed,0)==before
    one=copy.deepcopy(ep);one['test']=one['test'][:1];assert f.public_view(one,0)==before
    with pytest.raises(ValueError):f.public_view(ep,True)
    changed['test'][0]['input'][0][0]=True
    with pytest.raises(ValueError):f.public_view(changed,0)

def test_export_checks_visible_bytes_and_query_shuffle(tmp_path):
    f=load('family');tool=load('authoring');ep=f.generate(17,{'finish':'assemble_only'},2,4)
    seen=set()
    for seed in range(20):
        _,mapping=tool.projection([ep],seed);seen.add(mapping[0]['source_indices'][0])
    assert seen==set(range(4))
    views,mapping=tool.projection([ep],41)
    for key,b in views.items():(tmp_path/(key+'.json')).write_bytes(b)
    tool.check_public_files(tmp_path,views)
    path=next(tmp_path.iterdir());old=path.read_bytes();path.write_bytes(old+b' ')
    with pytest.raises(ValueError):tool.check_public_files(tmp_path,views)
    path.write_bytes(old);(tmp_path/'extra.json').write_text('{}')
    with pytest.raises(ValueError):tool.check_public_files(tmp_path,views)

def test_two_piece_explicit_production_case_is_supported():
    s=load('sampler');m=load('model')
    g,want=s.construct(19,0,split='production',chain_count=1,chain_depth=2)
    assert m.solve(g)==want

@pytest.mark.parametrize('bad',[{'seed':True},{'sample_index':-1},{'grid_h':23},{'orientation_id':8},{'piece_width':4},{'unknown':1}])
def test_public_generator_rejects_bad_controls(bad):
    path=HOME/'generator.py';spec=importlib.util.spec_from_file_location('contour_root',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    args={'seed':0,'sample_index':0,**bad}
    with pytest.raises(ValueError):m.generate(**args)
