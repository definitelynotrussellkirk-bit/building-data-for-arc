"""Author-private tests: recover period, test lattice hit, recolor and stop."""
from pathlib import Path
import copy
import importlib.util
import json
import pytest
HOME=Path(__file__).resolve().parents[1];BASE=HOME/'workspace/parametric'

def load(name='engine'):
    path=BASE/(name+'.py')
    assert path.is_file(), 'missing implementation '+name
    spec=importlib.util.spec_from_file_location('_periodic_test_'+name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_all_five_original_labels_without_mutation():
    m=load();source=json.loads((HOME/'tests/originals.json').read_text())
    for split in source.values():
        for pair in split:
            g=copy.deepcopy(pair['input'])
            assert m.solve(g,'stop_at_hit')==pair['output']
            assert g==pair['input']

def test_on_lattice_hit_recolors_seed_and_stops():
    m=load();g=[[0]*9,[2,0,2,0,5,0,0,0,0],[0]*9]
    assert m.solve(g,'stop_at_hit')==[[0]*9,[5,0,5,0,5,0,0,0,0],[0]*9]
    assert m.solve(g,'continue_after_hit')==[[0]*9,[5,0,5,0,5,0,5,0,5],[0]*9]
    p=m.analyze(g)
    assert p['side']==0 and p['rays'][0]['spacing']==2
    assert p['rays'][0]['hit']==[4,5]

def test_off_lattice_marker_is_preserved_not_triggered():
    m=load();g=[[0]*9,[2,0,2,0,0,5,0,0,0],[0]*9]
    expected=[[0]*9,[2,0,2,0,2,5,2,0,2],[0]*9]
    assert m.solve(g,'stop_at_hit')==expected
    assert m.solve(g,'continue_after_hit')==expected
    assert m.analyze(g)['rays'][0]['hit'] is None

def test_all_four_source_edges_obey_same_rule():
    m=load();g=[[0]*9,[2,0,2,0,5,0,0,0,0],[0]*9]
    out=[[0]*9,[5,0,5,0,5,0,0,0,0],[0]*9]
    for t in range(4):
        assert m.solve(g,'stop_at_hit')==out
        g=[list(row) for row in zip(*g[::-1])]
        out=[list(row) for row in zip(*out[::-1])]

def test_markerless_ray_extends_to_last_periodic_position():
    m=load();g=[[0]*10,[6,0,0,6,0,0,0,0,0,0],[0]*10]
    assert m.solve(g)==[[0]*10,[6,0,0,6,0,0,6,0,0,6],[0]*10]

@pytest.mark.parametrize('g',[[],[[True]],[[1.0]],[[10]],[[0]],[[1,0],[0]],[[1,2,0]],[[2,0,2]]])
def test_invalid_or_ambiguous_grammar_fails_closed(g):
    with pytest.raises(ValueError):load().solve(g)

def test_standalone_base_equals_native_engine():
    assert (HOME/'generator.py').read_bytes()==(BASE/'engine.py').read_bytes()

def test_all_counts_settings_and_structural_coverage():
    a=load('adapter');m=a.engine;seen=set()
    for seed in range(16):
        bank=a.generate(seed,{'extent':'stop_at_hit'},6,4)
        other=a.generate(seed,{'extent':'continue_after_hit'},6,4)
        assert len({json.dumps(p['input']) for s in ('train','test') for p in bank[s]})==10
        for split in ('train','test'):
            assert [p['input'] for p in bank[split]]==[p['input'] for p in other[split]]
        for count in range(2,7):
            ep=a.generate(seed,{'extent':'stop_at_hit'},count,4)
            assert ep['train']==bank['train'][:count] and ep['test']==bank['test']
            assert a.generate(seed,{'extent':'stop_at_hit'},count,1)['test']==bank['test'][:1]
        assert any(x['output']!=y['output'] for x,y in zip(bank['train'][:2],other['train'][:2]))
        for pair in bank['train'][:2]:
            info=m.analyze(pair['input']);seen.add(info['side'])
            assert any(r['hit'] is not None for r in info['rays'])
            assert any(r['marker'] is not None and r['hit'] is None for r in info['rays'])
            assert any(r['marker'] is None for r in info['rays'])
        stress=bank['test'][3]
        assert (len(stress['input']),len(stress['input'][0]))==(30,30)
        assert len(m.analyze(stress['input'])['rays'])>=12
        assert sum(v!=0 for row in stress['output'] for v in row)>=120
    assert seen=={0,1,2,3}

def test_exact_program_default():
    a=load('adapter')
    assert a.program({'extent':'stop_at_hit'})==(HOME/'reference.rkt').read_text()==(BASE/'canonical.rkt').read_text()
    assert a.program({'extent':'continue_after_hit'})!=a.program({'extent':'stop_at_hit'})

@pytest.mark.parametrize('kw',[
    {'seed':True},{'seed':-1},{'seed':2.5},{'demos':False},{'demos':1},{'demos':7},
    {'queries':True},{'queries':0},{'queries':5},{'settings':{}},
    {'settings':{'extent':'bad'}},{'settings':{'extent':'stop_at_hit','extra':0}}])
def test_invalid_requests(kw):
    args={'seed':0,'settings':{'extent':'stop_at_hit'},'demos':2,'queries':4};args.update(kw)
    with pytest.raises(ValueError):load('adapter').generate(**args)
