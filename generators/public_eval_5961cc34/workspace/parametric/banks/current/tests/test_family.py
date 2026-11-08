"""Breaks caught: missing relay, inactive painting, wrong depth, unsafe controls."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p/'shared/data/raw').is_dir())

def load(name):
    path = HOME/'workspace/parametric'/f'{name}.py'
    assert path.exists(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location('beam_test_'+name, path)
    mod = importlib.util.module_from_spec(spec);sys.modules[spec.name] = mod;spec.loader.exec_module(mod)
    return mod

def originals():
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['5961cc34']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['5961cc34']
    return data['train']+[{'input':p['input'],'output':o} for p,o in zip(data['test'],gold)]

@pytest.mark.parametrize('i',range(5))
def test_official_labels(i):
    p=originals()[i]; assert load('model').solve(p['input']) == p['output']

def test_inactive_shape_erased_and_no_beam_teleport():
    p=originals()[0]; info=load('model').analyze(p['input'])
    assert info['depths']=={}
    assert all(row[8]==2 and set(row)<={2,8} for row in info['output'])

@pytest.mark.parametrize('seed',[0,17,43])
@pytest.mark.parametrize('demos',[2,3,6])
def test_matched_unique_prefixes_and_stress(seed,demos):
    a=load('adapter');small=a.generate(seed,{'finish':'trace_only'},2,4)
    ep=a.generate(seed,{'finish':'trace_only'},demos,4)
    alt=a.generate(seed,{'finish':'highlight_deepest'},demos,4)
    assert ep['train'][:2]==small['train']
    assert ep['test']==small['test']
    grids=[p['input'] for s in ('train','test') for p in ep[s]]
    assert len({json.dumps(g) for g in grids})==demos+4
    assert grids==[p['input'] for s in ('train','test') for p in alt[s]]
    assert any(p['output']!=q['output'] for p,q in zip(ep['train'],alt['train']))
    assert any(len(g)==30 and len(g[0])==30 for g in grids)
    assert a.program({'finish':'trace_only'}) == (HOME/'reference.rkt').read_text()
    for g in grids:
        assert 1<=len(g)<=30 and 1<=len(g[0])<=30
        assert all(type(v) is int and 0<=v<=9 for r in g for v in r)

@pytest.mark.parametrize('args',[(True,{'finish':'trace_only'},3,4),(-1,{'finish':'trace_only'},3,4),(0,{'finish':'trace_only'},1,4),(0,{'finish':'trace_only'},7,4),(0,{'finish':'trace_only'},3,3),(0,{'finish':True},3,4),(0,{'finish':'trace_only','extra':1},3,4)])
def test_invalid_contract(args):
    with pytest.raises((ValueError,TypeError)):load('adapter').generate(*args)

@pytest.mark.parametrize('g',[[],[[True]],[[8],[8,8]],[[11]]])
def test_bad_grids_rejected(g):
    with pytest.raises((ValueError,TypeError)):load('model').solve(g)

def test_demo_rivals_and_depth_dependency():
    m=load('model');a=load('adapter')
    for seed in range(12):
        for finish in ('trace_only','highlight_deepest'):
            ep=a.generate(seed,{'finish':finish},2,4)
            for name in m.RIVALS:
                assert any(m.rival(p['input'],finish,name)!=p['output'] for p in ep['train']), (seed,finish,name)
            info=m.analyze(ep['train'][0]['input'])
            assert max(info['depths'].values())>=3
            assert len(info['depths']) < len(info['objects'])

@pytest.mark.parametrize('seed',[0,17])
def test_model_does_not_mutate_inputs(seed):
    a=load('adapter');m=load('model');g=a.generate(seed,{'finish':'trace_only'},2,4)['test'][0]['input'];old=copy.deepcopy(g)
    m.solve(g,'highlight_deepest');assert g==old

def test_public_view_hides_future_answers_and_metadata():
    f=load('family');ep=f.generate(17,{'finish':'trace_only'},3,4);before=f.public_view(ep,0)
    modified=copy.deepcopy(ep);modified['program_solution']='secret replacement';modified['settings']={'bad':True}
    modified['test'][0]['output']={'not':'grid'};modified['test'][1:]=[{'invalid':'future'}]
    assert f.public_view(modified,0)==before
    one=copy.deepcopy(ep);one['test']=one['test'][:1]
    assert f.public_view(one,0)==before
    changed=copy.deepcopy(ep);changed['test'][0]['input'][0][0]=7
    assert f.public_view(changed,0)!=before
    public=json.loads(before)
    assert set(public)=={'train','test'} and set(public['test'][0])=={'input'}


def test_public_strict_visible_grid_and_bool_index():
    f=load('family');ep=f.generate(17,{'finish':'trace_only'},2,4)
    with pytest.raises(ValueError): f.public_view(ep,True)
    ep['test'][0]['input'][0][0]=True
    with pytest.raises(ValueError): f.public_view(ep,0)


def test_public_writer_checks_exact_bytes_and_extra_files(tmp_path):
    tool=load('authoring');f=load('family');ep=f.generate(17,{'finish':'trace_only'},2,4);ep['seed']=17
    views,mapping=tool.projection([ep],41)
    for key,content in views.items():(tmp_path/(key+'.json')).write_bytes(content)
    tool.check_public_files(tmp_path,views)
    target=next(tmp_path.iterdir());original=target.read_bytes();target.write_bytes(original+b' ')
    with pytest.raises(ValueError):tool.check_public_files(tmp_path,views)
    target.write_bytes(original);(tmp_path/'unexpected.json').write_text('{}')
    with pytest.raises(ValueError):tool.check_public_files(tmp_path,views)


def test_query_order_is_shuffled_independently_of_private_fields():
    tool=load('authoring');f=load('family');ep=f.generate(17,{'finish':'trace_only'},2,4);ep['seed']=17
    seen=set()
    for ps in range(20):
        views,mapping=tool.projection([ep],ps);seen.add(mapping[0]['source_indices'][0])
    assert seen==set(range(4))
    altered=copy.deepcopy(ep);altered['seed']=999;altered['program_solution']='private'
    assert tool.projection([ep],41)==tool.projection([altered],41)

@pytest.mark.parametrize('orientation',range(8))
def test_exact_canvas_controls_survive_rotation(orientation):
    s=load('sampler')
    g=s.draw(17,0,split='production',grid_h=24,grid_w=30,transform_id=orientation)
    assert (len(g),len(g[0]))==(24,30)


def test_cycle_terminates_with_minimum_hop_depths():
    s=load('sampler');m=load('model')
    g=s.draw(17,0,split='production',grid_h=30,grid_w=30,transform_id=0,path_id=3,band=2)
    info=m.analyze(g)
    assert sorted(info['depths'].values())==[1,2,3,4]
    assert len(info['rays'])==9  # launch plus two rays from each reached port
