"""Behavioral tests for the public parent and its deterministic parameter family."""
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load(name, path):
    assert path.is_file(), f'missing implementation: {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def api():
    return load('test_195_generator', HOME / 'generator.py')

def adapter():
    return load('test_195_adapter', HOME / 'workspace/parametric/adapter.py')

@pytest.mark.parametrize('split,index', [('train',0),('train',1),('train',2),('test',0),('test',1)])
def test_original_labels(split,index):
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['195c6913']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['195c6913']
    pair=data[split][index]
    grid=lambda v:[[int(x) for x in row] for row in v]
    expected=pair['output'] if split=='train' else gold[index]
    assert api().solve(grid(pair['input'])) == grid(expected)

def test_canonical_program_exact_and_parameters_strict():
    a=adapter()
    assert a.program({'turn':'north'})==(HOME/'reference.rkt').read_text()
    for bad in ({},{'turn':'west'},{'turn':True},{'turn':'north','x':1},None):
        with pytest.raises((TypeError,ValueError)):
            a.program(bad)

@pytest.mark.parametrize('seed', [0,1,15,17,43,128])
def test_matched_inputs_prefixes_and_projection(seed):
    a=adapter(); full=a.generate(seed,{'turn':'north'},6,4)
    other=a.generate(seed,{'turn':'south'},6,4)
    assert [p['input'] for sp in ('train','test') for p in full[sp]] == [p['input'] for sp in ('train','test') for p in other[sp]]
    assert len({json.dumps(p['input']) for sp in ('train','test') for p in full[sp]})==10
    for d in range(2,7):
        for q in range(1,5):
            ep=a.generate(seed,{'turn':'north'},d,q)
            assert ep['train']==full['train'][:d] and ep['test']==full['test'][:q]
    assert any(p['output']!=r['output'] for p,r in zip(full['train'][:2],other['train'][:2]))
    views=a.present(seed,{'turn':'north'},2,4,presentation_seed=19)
    assert len(views['public'])==4
    assert a.present(seed,{'turn':'north'},2,1,presentation_seed=19)['public'][0]==views['public'][0]
    for view in views['public']:
        assert set(view)=={'train','test'} and len(view['test'])==1
        assert set(view['test'][0])=={'input'}
    full['train'][0]['input'][0][0]=99
    assert a.generate(seed,{'turn':'north'},6,4)['train'][0]['input'][0][0]!=99

def test_presentation_not_fixed_query_ordinal():
    a=adapter()
    first={a.present(s,{'turn':'north'},2,4,presentation_seed=0)['private']['source_indices'][0] for s in range(16)}
    assert len(first)>1

@pytest.mark.parametrize('seed,demos,queries', [(True,2,4),(-1,2,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,True,4),(0,2,True)])
def test_reject_invalid_controls(seed,demos,queries):
    with pytest.raises((TypeError,ValueError)):
        adapter().generate(seed,{'turn':'north'},demos,queries)

@pytest.mark.parametrize('seed',range(8))
def test_stress_and_boundaries(seed):
    a=adapter(); ep=a.generate(seed,{'turn':'north'},2,4)
    g=ep['test'][3]['input']; m=api()
    assert len(g)==30 and len(g[0])==30
    facts=m.parse(g)
    assert len(facts['starts'])==2
    assert sum(v==facts['road'] for row in g for v in row)>200
    assert max(r for r,row in enumerate(g) if facts['road'] in row)>=26
    assert any(row[-1]==facts['road'] for row in g)
    assert m.self_check(g)==[]
    before=copy.deepcopy(g); m.solve(g); assert g==before

def test_literal_turn_and_pattern_continuation():
    m=api()
    # Detached trace test: turn at the last free cell, keep sequence phase,
    # mark the blocked cell, and stop if the new heading is also blocked.
    terrain=[[9,9,0,0],[0,0,0,9],[0,9,9,9],[9,9,9,9]]
    path,bumps=m.trace(terrain,(2,0),road=0,wall=9,turn='north')
    assert path==[(2,0),(1,0),(1,1),(1,2),(0,2)]
    assert bumps==[(2,1),(0,0),(1,3)]

@pytest.mark.parametrize('bad', [[],[[True]],[[10]],[[1],[2,3]], [[1.0]]])
def test_strict_grid_types(bad):
    with pytest.raises((TypeError,ValueError)):
        api().solve(bad)


def test_bounded_rivals_on_minimum_lesson():
    m=api(); a=adapter()
    for seed in (0,15,17,43,127):
        for turn in ('north','south'):
            ep=a.generate(seed,{'turn':turn},2,4)
            for rival in m.RIVALS:
                survives=all(m.solve(p['input'],turn,rival=rival)==p['output'] for p in ep['train'])
                changes=any(m.solve(p['input'],turn,rival=rival)!=p['output'] for p in ep['test'])
                assert not(survives and changes),(seed,turn,rival)


def test_adapter_reload_binds_exact_generator_bytes(tmp_path):
    import os
    from shutil import copyfile
    home=tmp_path/'family';base=home/'workspace/parametric';base.mkdir(parents=True)
    copyfile(HOME/'workspace/parametric/adapter.py',base/'adapter.py')
    source=home/'generator.py';source.write_text('SOURCE_SENTINEL = 1\n')
    stamp=source.stat()
    first=load('reload_before',base/'adapter.py')
    assert first.G.SOURCE_SENTINEL==1
    source.write_text('SOURCE_SENTINEL = 2\n')
    os.utime(source,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    second=load('reload_after',base/'adapter.py')
    assert second.G.SOURCE_SENTINEL==2


def test_adapter_runs_from_native_bound_resource_closure(tmp_path):
    from shutil import copyfile, copytree
    home=tmp_path/'relocated';home.mkdir()
    copyfile(HOME/'generator.py',home/'generator.py')
    copytree(HOME/'workspace/parametric',home/'workspace/parametric')
    # Native promotion binds generator.py and prototype resources, not files
    # elsewhere in the task home. A qualified program must need only these.
    relocated=load('relocated_native_adapter',home/'workspace/parametric/adapter.py')
    settings={'turn': 'north'}
    expected=(HOME/'reference.rkt').read_text()
    assert relocated.program(settings)==expected
    episode=relocated.generate(17,settings,2,1)
    assert len(episode['train'])==2 and len(episode['test'])==1
    assert episode['program_solution']==expected
