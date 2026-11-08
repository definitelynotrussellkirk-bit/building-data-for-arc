from pathlib import Path
import importlib.util
import json
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
BASE=HOME/'workspace/parametric'

def load(name):
    path=BASE/(name+'.py')
    assert path.is_file(), f'Missing implementation: {name}'
    spec=importlib.util.spec_from_file_location('_network_test_'+name, path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def originals():
    from reviewer_support import find_root
    root=find_root(__file__);raw=root/'shared/data/raw'
    task=json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['800d221b']
    gold=json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['800d221b']
    return task['train']+[dict(p,output=o) for p,o in zip(task['test'],gold)]

@pytest.mark.parametrize('index',range(4))
def test_general_reference_matches_every_official_label(index):
    model=load('model');p=originals()[index]
    assert model.solve(p['input'],'contacts')==p['output']

def test_votes_are_per_contact_not_per_chamber_or_raw_pixel():
    m=load('model');p=originals()[3]
    a=m.analyze(p['input'])
    assert a['hub']==(12,13)
    assert sorted((x['winner'],x['contacts']) for x in a['terminals'])==[(2,1),(2,2),(3,1),(3,3)]
    assert m.solve(p['input'])[12][13]==3  # Four green versus three red contacts.
    assert m.solve(p['input'],'chambers')[12][13]==2  # Deterministic lower-color tie extension.

def test_chamber_variant_keeps_all_local_propagation():
    m=load('model');p=originals()[2]
    got=m.solve(p['input'],'chambers');want=[r[:] for r in p['output']];want[9][9]=5
    assert got==want  # Three gray chambers versus two magenta, despite four magenta wires.

def test_invalid_grids_and_modes_fail_closed():
    m=load('model')
    for grid in ([],[[True]],[[0],[0,1]],[[10]],[[0.0]],[[0]*5 for _ in range(5)]):
        with pytest.raises((ValueError,TypeError)):m.solve(grid)
    with pytest.raises(ValueError):m.solve(originals()[0]['input'],'unknown')
