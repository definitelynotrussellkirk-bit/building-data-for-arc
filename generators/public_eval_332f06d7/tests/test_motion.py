from pathlib import Path
import importlib.util
import json
import sys
import pytest
BASE=Path(__file__).resolve().parents[1]/'workspace/parametric'

def load(name):
    path=BASE/(name+'.py');assert path.is_file(),f'Missing implementation: {name}'
    spec=importlib.util.spec_from_file_location('_rigid_test_'+name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def originals():
    from reviewer_support import find_root
    raw=find_root(__file__)/'shared/data/raw'
    t=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['332f06d7']
    s=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['332f06d7']
    return t['train']+[dict(p,output=o)for p,o in zip(t['test'],s)]

@pytest.mark.parametrize('index',range(5))
def test_general_rule_matches_all_official_labels(index):
    p=originals()[index];assert load('model').solve(p['input'])==p['output']

def test_footprint_clearance_and_goal_geodesic_both_matter():
    m=load('model');p=originals()[2];d=m.analyze(p['input'])
    assert d['shape']==(3,3) and d['start']==(12,1) and d['terminal']==(6,7)
    assert len(d['route'])-1==14 and len(d['reachable'])==15
    assert (7,7) not in d['legal']  # The next 3x3 placement intersects the green neck.
    assert d['terminal']!=min(d['reachable'],key=lambda pos:(abs(pos[0]-1)+abs(pos[1]),pos))

def test_halfway_has_hand_computed_literal_route():
    m=load('model')
    g=[[3]*7,[3,0,1,1,1,2,3],[3]*7]
    assert m.solve(g,'terminal')==[[3]*7,[3,1,1,1,1,0,3],[3]*7]
    assert m.solve(g,'halfway')==[[3]*7,[3,1,1,0,1,2,3],[3]*7]
    odd=[[3]*6,[3,0,1,1,2,3],[3]*6]
    assert m.solve(odd,'halfway')==[[3]*6,[3,1,1,0,2,3],[3]*6]

def test_malformed_and_disconnected_inputs_fail_closed():
    m=load('model')
    for g in ([],[[True]],[[0],[0,1]],[[0,3,2]],[[0,0],[0,2]],[[0,10,2]]):
        with pytest.raises((ValueError,TypeError)):m.solve(g)
    with pytest.raises(ValueError):m.solve(originals()[0]['input'],'unknown')
