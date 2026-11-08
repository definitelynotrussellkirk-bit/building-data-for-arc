from pathlib import Path
import importlib.util
import json
import copy
import pytest

HOME = Path(__file__).resolve().parents[1]

def load():
    path = HOME / 'workspace/parametric/family.py'
    assert path.exists(), 'The requested general family has not yet been implemented'
    spec = importlib.util.spec_from_file_location('_test_cavity_family', path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def root():
    return next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def originals():
    r=root()/'shared/data/raw'
    data=json.loads((r/'arc-agi_evaluation_challenges.json').read_text())['898e7135']
    gold=json.loads((r/'arc-agi_evaluation_solutions.json').read_text())['898e7135']
    return [(s,i,[[int(v) for v in row] for row in p['input']],
             [[int(v) for v in row] for row in (p['output'] if s=='train' else gold[i])])
            for s in ('train','test') for i,p in enumerate(data[s])]

def test_all_official_labels():
    f=load()
    for split,i,g,y in originals():
        assert f.solve(g)==y, (split,i)

def test_default_program_exact_bytes():
    f=load()
    assert f.program({'finish':'assemble_only'}).encode()==(HOME/'reference.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,17,43,97])
def test_deterministic_matched_settings_and_teaching(seed):
    f=load(); a=f.generate(seed,{'finish':'assemble_only'},2,4)
    b=f.generate(seed,{'finish':'highlight_largest_fitted_cluster'},2,4)
    assert a==f.generate(seed,{'finish':'assemble_only'},2,4)
    assert [p['input'] for s in ('train','test') for p in a[s]]==[p['input'] for s in ('train','test') for p in b[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in a[s]})==6
    for ep in (a,b):
        assert len(ep['test'])==4
        assert f.surviving_rivals(ep)==[]
        assert any(len(p['output'])==len(p['output'][0])==30 for p in ep['test'])

@pytest.mark.parametrize('demos',[2,3,4,5,6])
def test_prefix_and_new_objects(demos):
    f=load(); s={'finish':'highlight_largest_fitted_cluster'}
    ep=f.generate(17,s,demos,4); big=f.generate(17,s,6,4)
    assert ep['train']==big['train'][:demos]
    assert ep['test']==big['test']
    for split in ('train','test'):
        for pair in ep[split]:
            info=f.analyze(pair['input'])
            assert len(info['holes'])>=5
            assert len(info['cluster_sizes'])>=3
            assert info['cluster_sizes'][0]>info['cluster_sizes'][1]
            assert f.solve(pair['input'],s['finish'])==pair['output']

@pytest.mark.parametrize('args',[(True,{},2,4),(-1,{},2,4),(0,{},2,4),(0,{'finish':'x'},2,4),(0,{'finish':'assemble_only','x':0},2,4),(0,{'finish':'assemble_only'},1,4),(0,{'finish':'assemble_only'},7,4),(0,{'finish':'assemble_only'},2,3),(0,{'finish':'assemble_only'},True,4)])
def test_bad_requests_fail_closed(args):
    with pytest.raises((TypeError,ValueError)):
        load().generate(*args)

@pytest.mark.parametrize('bad',[[],[[True]],[[10]],[[1],[1,2]],[[1.0]]])
def test_invalid_grids_rejected(bad):
    with pytest.raises(ValueError):load().analyze(bad)

def test_public_view_ignores_private_state():
    f=load();ep=f.generate(17,{'finish':'assemble_only'},3,4)
    raw=f.public_view(ep,0);v=json.loads(raw)
    assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
    changed=copy.deepcopy(ep);changed['program_solution']='private';changed['settings']={'bad':'private'}
    changed['test'][0]['output']=[[9]];changed['test'][1:] = [{'input':[[1]],'output':[[1]]}]
    assert f.public_view(changed,0)==raw
    changed=copy.deepcopy(ep);changed['test'][0]['input'][0][0]=(changed['test'][0]['input'][0][0]+1)%10
    assert f.public_view(changed,0)!=raw

def test_source_not_data_lookup():
    f=load()
    text=(HOME/'reference.rkt').read_text()+(HOME/'workspace/parametric/family.py').read_text()
    assert 'arc-agi_evaluation' not in text
    assert 'solutions.json' not in text

@pytest.mark.parametrize('rotation,reflection',[(r,f) for r in range(4) for f in (False,True)])
def test_d4_equivariance(rotation,reflection):
    f=load();g=f.scene(23,'metamorphic',3,True)
    for setting in f.SETTINGS:
        expected=f._turn(f.solve(g,setting),rotation,reflection)
        assert f.solve(f._turn(g,rotation,reflection),setting)==expected

def test_reusable_authoring_tools_exist_and_project_privately(tmp_path):
    path=HOME/'workspace/parametric/authoring.py'
    assert path.is_file(), 'Reusable preflight audit and export verifier are missing'
    spec=importlib.util.spec_from_file_location('_test_authoring',path)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    f=load();ep=f.generate(3,{'finish':'assemble_only'},2,4);ep['seed']=3
    views,mapping=tool.projection([ep],11)
    assert len(views)==4 and sorted(mapping[0]['source_indices'])==[0,1,2,3]
    assert set(json.loads(next(iter(views.values()))))=={'train','test'}
    public=tmp_path/'public';public.mkdir()
    for key,raw in views.items():(public/(key+'.json')).write_bytes(raw)
    tool.check_public_files(public,views)
    first=next(public.iterdir());first.write_text(first.read_text()+' ')
    with pytest.raises(ValueError):tool.check_public_files(public,views)
    for key,raw in views.items():(public/(key+'.json')).write_bytes(raw)
    (public/'extra.json').write_text('{}')
    with pytest.raises(ValueError):tool.check_public_files(public,views)

def test_source_inventory_is_not_a_fixed_role_layout():
    f=load();orders=set()
    for seed in range(64):
        info=f.analyze(f.scene(seed,'permutation',3,True));k=info['scale']
        orders.add(tuple(len(o['cells'])//(k*k) for o in info['outside'] if len(o['cells'])>=k*k))
    assert len(orders)>=20, 'Fixed source slots leak piece roles instead of teaching shape matching'

def test_reflection_not_just_rotation_is_taught():
    f=load();ep=f.generate(17,{'finish':'assemble_only'},2,4)
    assert 'rotations_only' in f.rival_names('assemble_only')
    assert any(f.rival(p['input'],'assemble_only','rotations_only')!=p['output'] for p in ep['train'])
