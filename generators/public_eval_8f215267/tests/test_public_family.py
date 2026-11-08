"""Fresh public-parent and graph-connectivity/tally regression tests."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HOME.parents if (p/'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())

def load(name,path):
    assert path.is_file(), f'missing implementation: {path.name}'
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def api(): return load('test_8f_generator',HOME/'generator.py')
def adapter(): return load('test_8f_adapter',HOME/'workspace/parametric/adapter.py')

@pytest.mark.parametrize('split,index',[('train',0),('train',1),('train',2),('test',0)])
def test_original_labels(split,index):
    data=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['8f215267']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['8f215267']
    pair=data[split][index]; grid=lambda v:[[int(x) for x in row] for row in v]
    expected=pair['output'] if split=='train' else gold[index]
    assert api().solve(grid(pair['input']))==grid(expected)

def test_hand_counted_diagonal_objects_and_tallies():
    g=[[8]*18 for _ in range(9)]
    for r in range(1,6):
        for c in range(1,12):
            if r in (1,5) or c in (1,11): g[r][c]=3
    g[1][14]=g[2][15]=3;g[7][17]=2
    want=deepcopy(g);want[1][14]=want[2][15]=want[7][17]=8
    want[3][7]=want[3][9]=3
    assert api().solve(g,4)==want
    want[3][7]=8
    assert api().solve(g,8)==want
    assert api().measure(g,4)['counts']==[2]
    assert api().measure(g,8)['counts']==[1]

def test_program_default_and_settings_rejection():
    a=adapter(); assert a.program({'connectivity':4})==(HOME/'reference.rkt').read_text()
    for bad in ({},{'connectivity':True},{'connectivity':'4'},{'connectivity':6},{'connectivity':4,'x':1},None):
        with pytest.raises((TypeError,ValueError)):a.program(bad)

@pytest.mark.parametrize('seed',[0,1,15,17,43,128])
def test_matched_prefixes_and_public_projection(seed):
    a=adapter(); full=a.generate(seed,{'connectivity':4},6,4);other=a.generate(seed,{'connectivity':8},6,4)
    assert [p['input'] for sp in ('train','test') for p in full[sp]]==[p['input'] for sp in ('train','test') for p in other[sp]]
    assert len({json.dumps(p['input']) for sp in ('train','test') for p in full[sp]})==10
    for d in range(2,7):
        for q in range(1,5):
            ep=a.generate(seed,{'connectivity':4},d,q)
            assert ep['train']==full['train'][:d] and ep['test']==full['test'][:q]
    assert any(x['output']!=y['output'] for x,y in zip(full['train'][:2],other['train'][:2]))
    bundle=a.present(seed,{'connectivity':4},2,4,presentation_seed=19)
    assert len(bundle['public'])==4
    assert a.present(seed,{'connectivity':4},2,1,presentation_seed=19)['public'][0]==bundle['public'][0]
    for v in bundle['public']:
        assert set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'}
    full['test'][0]['input'][0][0]=99
    assert a.generate(seed,{'connectivity':4},6,4)['test'][0]['input'][0][0]!=99

@pytest.mark.parametrize('seed',range(8))
def test_30x30_real_content_and_no_mutation(seed):
    a=adapter();m=api();g=a.generate(seed,{'connectivity':4},2,4)['test'][3]['input'];original=deepcopy(g)
    assert len(g)==len(g[0])==30
    facts=m.measure(g,4); assert len(facts['frames'])==4
    assert sum(v!=g[0][0] for row in g for v in row)>120
    assert any(v!=g[0][0] for v in g[-1]) and any(row[-1]!=g[0][0] for row in g)
    assert m.self_check(g)==[]
    m.solve(g);assert g==original

@pytest.mark.parametrize('seed,d,q',[(True,2,4),(-1,2,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,True,4),(0,2,True)])
def test_bad_controls(seed,d,q):
    with pytest.raises((TypeError,ValueError)):adapter().generate(seed,{'connectivity':4},d,q)

@pytest.mark.parametrize('g',[[],[[True]],[[10]],[[1],[2,3]],[[1.0]]])
def test_bad_grid(g):
    with pytest.raises((TypeError,ValueError)):api().solve(g)

def test_rival_learning_and_not_fixed_query_order():
    m=api();a=adapter();first=set()
    for seed in range(16):
        first.add(a.present(seed,{'connectivity':4},2,4)['private']['source_indices'][0])
        for con in (4,8):
            ep=a.generate(seed,{'connectivity':con},2,4)
            for rival in m.RIVALS:
                survive=all(m.solve(p['input'],con,rival=rival)==p['output'] for p in ep['train'])
                change=any(m.solve(p['input'],con,rival=rival)!=p['output'] for p in ep['test'])
                assert not(survive and change),(seed,con,rival)
    assert len(first)>1


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


def test_stress_exercises_full_tally_capacity():
    a=adapter();m=api();g=a.generate(17,{'connectivity':4},2,4)['test'][3]['input']
    four=m.measure(g,4);eight=m.measure(g,8)
    assert four['counts'][0]==6
    assert eight['counts'][0]==3
    f=four['frames'][0];r1,c1,r2,c2=f['bbox']
    out=m.solve(g,4)
    assert sum(out[(r1+r2)//2][c]==f['color'] for c in range(c1+1,c2))==6


def test_adapter_runs_from_native_bound_resource_closure(tmp_path):
    from shutil import copyfile, copytree
    home=tmp_path/'relocated';home.mkdir()
    copyfile(HOME/'generator.py',home/'generator.py')
    copytree(HOME/'workspace/parametric',home/'workspace/parametric')
    # Native promotion binds generator.py and prototype resources, not files
    # elsewhere in the task home. A qualified program must need only these.
    relocated=load('relocated_native_adapter',home/'workspace/parametric/adapter.py')
    settings={'connectivity': 4}
    expected=(HOME/'reference.rkt').read_text()
    assert relocated.program(settings)==expected
    episode=relocated.generate(17,settings,2,1)
    assert len(episode['train'])==2 and len(episode['test'])==1
    assert episode['program_solution']==expected
