from pathlib import Path
import importlib.util
import json
import copy
import pytest
HOME=Path(__file__).resolve().parents[1]
def load():
    path=HOME/'workspace/parametric/family.py'
    assert path.exists(), 'General socket family is not implemented'
    s=importlib.util.spec_from_file_location('_test_socket_family',path);f=importlib.util.module_from_spec(s);s.loader.exec_module(f);return f

def originals():
    root=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').exists())/'shared/data/raw'
    data=json.loads((root/'arc-agi_evaluation_challenges.json').read_text())['8b9c3697']
    gold=json.loads((root/'arc-agi_evaluation_solutions.json').read_text())['8b9c3697']
    return [(s,i,[[int(v) for v in row] for row in p['input']],[[int(v) for v in row] for row in (p['output'] if s=='train' else gold[i])]) for s in ('train','test') for i,p in enumerate(data[s])]

def test_every_original_label_and_test_gold():
    f=load()
    for split,i,g,out in originals():assert f.solve(g)==out,(split,i)

def test_exact_default_source_bytes():
    f=load();assert f.program({'candidate_order':'nearest'}).encode()==(HOME/'reference.rkt').read_bytes()

@pytest.mark.parametrize('seed',[0,1,17,43,97])
def test_distinct_matched_inferable_episodes(seed):
    f=load();a=f.generate(seed,{'candidate_order':'nearest'},2,4);b=f.generate(seed,{'candidate_order':'farthest'},2,4)
    assert a==f.generate(seed,{'candidate_order':'nearest'},2,4)
    assert [p['input'] for s in ('train','test') for p in a[s]]==[p['input'] for s in ('train','test') for p in b[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in a[s]})==6
    for ep in (a,b):
        assert f.surviving_rivals(ep)==[]
        assert any(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
        for p in ep['train']+ep['test']:
            info=f.analyze(p['input']);assert 2<=len(info['sockets'])<=4
            assert all(len(s['candidates'])==2 for s in info['sockets'])

@pytest.mark.parametrize('demos',[2,3,4,5,6])
def test_demo_prefix_and_query_independence(demos):
    f=load();s={'candidate_order':'farthest'};a=f.generate(7,s,demos,4);b=f.generate(7,s,6,4)
    assert a['train']==b['train'][:demos] and a['test']==b['test']

@pytest.mark.parametrize('rotation,reflection',[(r,b) for r in range(4) for b in (False,True)])
def test_all_orientations_and_reflections(rotation,reflection):
    f=load();g=f.scene(11,'symmetry',4,0)
    for setting in ('nearest','farthest'):
        assert f.solve(f._turn(g,rotation,reflection),setting)==f._turn(f.solve(g,setting),rotation,reflection)

def test_nearest_compatible_rectangle_not_global_nearest_red():
    f=load();g=f.scene(17,'exact-width',3,0);info=f.analyze(g)
    for socket in info['sockets']:
        assert len(socket['candidates'])==2
        overlaps=[o for o in info['reds'] if f.overlaps_lane(o,socket)]
        assert len(overlaps)>len(socket['candidates'])
    assert f.rival(g,'nearest','ignore_width')!=f.solve(g,'nearest')
    assert f.rival(g,'farthest','ignore_width')!=f.solve(g,'farthest')

def test_original_unmatched_socket_stays_and_distractors_disappear():
    f=load();_,_,g,y=originals()[0];info=f.analyze(g)
    assert sorted(len(s['candidates']) for s in info['sockets'])==[0,1]
    assert sum(v==2 for row in f.solve(g) for v in row)==1
    assert f.solve(g)==y

@pytest.mark.parametrize('args',[(True,{'candidate_order':'nearest'},2,4),(-1,{'candidate_order':'nearest'},2,4),(0,{},2,4),(0,{'candidate_order':'x'},2,4),(0,{'candidate_order':'nearest','extra':1},2,4),(0,{'candidate_order':'nearest'},1,4),(0,{'candidate_order':'nearest'},7,4),(0,{'candidate_order':'nearest'},2,1),(0,{'candidate_order':'nearest'},False,4)])
def test_strict_invalid_requests(args):
    with pytest.raises((ValueError,TypeError)):load().generate(*args)

@pytest.mark.parametrize('g',[[],[[True]],[[1],[1,2]],[[10]],[[2.0]]])
def test_strict_grid(g):
    with pytest.raises(ValueError):load().analyze(g)

def test_public_first_turn_privacy():
    f=load();ep=f.generate(0,{'candidate_order':'farthest'},3,4);before=f.public_view(ep,0)
    v=copy.deepcopy(ep);v['program_solution']='private';v['test'][0]['output']={'not':'grid'};v['test'][1:]=[{'not':'query'}]
    assert f.public_view(v,0)==before
    parsed=json.loads(before);assert set(parsed)=={'train','test'} and len(parsed['test'])==1 and set(parsed['test'][0])=={'input'}

def test_general_rule_not_official_data_lookup():
    f=load();code=(HOME/'reference.rkt').read_text()+(HOME/'workspace/parametric/family.py').read_text()
    assert 'arc-agi_evaluation' not in code and 'solutions.json' not in code

def test_quadrant_rays_cannot_capture_another_socket_payload():
    f=load()
    for seed in range(32):
        for count in (2,3,4):
            info=f.analyze(f.scene(seed,'noninterference',count,seed%2))
            assert len(info['sockets'])==count
            assert [len(s['candidates']) for s in info['sockets']]==[2]*count

def test_reusable_authoring_projection_rejects_tampering(tmp_path):
    path=HOME/'workspace/parametric/authoring.py'
    assert path.is_file(), 'Missing reusable unapproved-preflight export verifier'
    spec=importlib.util.spec_from_file_location('_socket_authoring_tests',path)
    tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
    f=load();ep=f.generate(3,{'candidate_order':'nearest'},2,4);ep['seed']=3
    views,mapping=tool.projection([ep],11)
    assert len(views)==4 and sorted(mapping[0]['source_indices'])==[0,1,2,3]
    public=tmp_path/'public';public.mkdir()
    for key,raw in views.items():(public/(key+'.json')).write_bytes(raw)
    tool.check_public_files(public,views)
    first=next(public.iterdir());first.write_text(first.read_text()+' ')
    with pytest.raises(ValueError):tool.check_public_files(public,views)
    for key,raw in views.items():(public/(key+'.json')).write_bytes(raw)
    (public/'extra.json').write_text('{}')
    with pytest.raises(ValueError):tool.check_public_files(public,views)

def test_size_proxy_reverses_between_minimum_demonstrations():
    f=load();ep=f.generate(17,{'candidate_order':'nearest'},2,4)
    one=f.analyze(ep['train'][0]['input']);two=f.analyze(ep['train'][1]['input'])
    assert all(len(s['candidates'][0]['cells'])>len(s['candidates'][1]['cells']) for s in one['sockets'])
    assert all(len(s['candidates'][0]['cells'])<len(s['candidates'][1]['cells']) for s in two['sockets'])
