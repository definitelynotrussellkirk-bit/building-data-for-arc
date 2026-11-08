import importlib.util
from pathlib import Path
HOME=Path(__file__).resolve().parents[1]

def rivals():
    path=HOME/'workspace/parametric/rivals.py'
    assert path.is_file(), 'Executable quadrant rivals missing'
    s=importlib.util.spec_from_file_location('quadrant_rivals_test',path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_two_demo_teaching_census():
    m=rivals();failures=[]
    for seed in range(32):
        for setting in m.adapter.SETTINGS:
            e=m.adapter.generate(seed,setting,2,4)
            for name in m.NAMES:
                if all(m.solve(p['input'],setting,name)==p['output'] for p in e['train']):
                    if any(m.solve(p['input'],setting,name)!=p['output'] for p in e['test']):
                        failures.append((seed,setting,name))
    assert not failures,failures[:12]

def test_counter_and_layer_rival_meanings():
    m=rivals();setting={'background_sampling':'block'}
    grid=[[1,1,2,2],[1,1,0,0],[3,4,7,0],[5,6,0,8]]
    assert m.solve(grid,setting,'swap_dimensions')==[[7,3,7,4],[3,8,4,8]]
    assert m.solve(grid,setting,'ignore_stencil')==[[3,3],[3,3],[5,5],[5,5]]
    assert m.solve(grid,setting,'stencil_only')==[[7,0],[0,8],[7,0],[0,8]]


def test_retained_empty_counterexample_and_repaired_demo():
    import json
    m=rivals();case=json.loads((HOME/'tests/empty_stencil_counterexample.json').read_text())
    assert case['matches']==[True,True,False]
    for p in case['pairs']:
        assert m.adapter.solve(p['input'],case['settings'])==p['canonical_output']
        assert m.solve(p['input'],case['settings'],'empty_large_hole')==p['rival_output']
    e=m.adapter.generate(case['seed'],case['settings'],2,4)
    assert m.solve(e['train'][0]['input'],case['settings'],'empty_large_hole')!=e['train'][0]['output']
