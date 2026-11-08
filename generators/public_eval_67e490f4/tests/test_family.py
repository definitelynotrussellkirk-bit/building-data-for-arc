import importlib.util,json,copy
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1]
def load(name='generator.py'):
    path=HOME/name
    assert path.is_file(), 'missing implementation: '+str(path)
    s=importlib.util.spec_from_file_location('_67_subject',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
@pytest.mark.parametrize('index',range(3))
def test_originals(index):
    m=load();p=json.loads((HOME/'tests/originals.json').read_text())[index]
    assert m.solve(p['input'])==p['output']
def test_no_input_mutation():
    m=load();g=json.loads((HOME/'tests/originals.json').read_text())[0]['input'];b=copy.deepcopy(g);m.solve(g);assert g==b

def adapter():return load('workspace/parametric/adapter.py')

@pytest.mark.parametrize('demos',[2,3,6])
def test_episode_contract(demos):
    a=adapter();e=a.generate(17,{'vote_rule':'most_frequent'},demos,4);f=a.generate(17,{'vote_rule':'least_frequent'},demos,4)
    assert len(e['train'])==demos and len(e['test'])==4
    assert [p['input'] for split in ('train','test') for p in e[split]]==[p['input'] for split in ('train','test') for p in f[split]]
    assert any(p['output']!=q['output'] for p,q in zip(e['train'],f['train']))
    assert len({json.dumps(p['input']) for split in ('train','test') for p in e[split]})==demos+4
    assert e['test']==a.generate(17,{'vote_rule':'most_frequent'},2,4)['test']
    assert (len(e['test'][3]['input']),len(e['test'][3]['input'][0]))==(30,30)
    assert e==a.generate(17,{'vote_rule':'most_frequent'},demos,4)

def test_reference_and_source_copy():
    a=adapter();assert a.program({'vote_rule':'most_frequent'})==(HOME/'reference.rkt').read_text()
    assert (HOME/'generator.py').read_bytes()==(HOME/'workspace/parametric/model.py').read_bytes()

@pytest.mark.parametrize('demos,queries',[(1,4),(7,4),(True,4),(3,1),(3,True)])
def test_bad_counts(demos,queries):
    with pytest.raises(ValueError):adapter().generate(0,{'vote_rule':'most_frequent'},demos,queries)

@pytest.mark.parametrize('settings',[{}, {'vote_rule':'bad'}, {'vote_rule':'most_frequent','extra':True}])
def test_bad_settings(settings):
    with pytest.raises(ValueError):adapter().program(settings)

def test_sampler_shape_candidates_and_ties():
    m=load()
    for seed in range(12):
        for i in (0,1,9):
            g=m.generate(seed=seed,sample_index=i);assert m.self_check(g)==[]
            _,holes,counts,objs,global_counts=m.records(g)
            assert len(holes)==6 and len(objs)==(18 if i%2==0 else 15)
            assert len(counts)==3 and all(len(v)==3 for v in counts.values())
            assert all(m.key(h) in counts for h in holes)
            assert m.solve(g,'most_frequent')!=m.solve(g,'least_frequent')

def test_shape_matching_distinguishes_equal_area():
    m=load()
    assert m.key([(0,0),(0,1),(1,0)])!=m.key([(0,0),(0,1),(0,2)])
    assert m.key([(0,0),(1,0),(2,0),(2,1)])==m.key([(0,1),(1,1),(2,1),(2,0)])

def test_relocated_generator(tmp_path):
    import subprocess,sys
    p=tmp_path/'generator.py';p.write_bytes((HOME/'generator.py').read_bytes())
    subprocess.run([sys.executable,'-I','-c',"import runpy; m=runpy.run_path("+repr(str(p))+");g=m['generate'](seed=17,sample_index=9);assert m['self_check'](g)==[];assert len(g)==30"],cwd=tmp_path,check=True,capture_output=True,text=True)

def test_minimal_teaching():
    a=load('workspace/parametric/audit.py');r=a.audit(range(16),[2]);assert r['failures']==[]

def test_first_demo_teaches_reflections_and_exact_shape():
    m=load()
    for seed in range(32):
        g=m.scene(seed,0)
        for policy in ('most_frequent','least_frequent'):
            for rival in ('rotations_only','bbox_only','area_only'):
                assert m.solve(g,policy)!=m.solve(g,policy,rival),(seed,policy,rival)
