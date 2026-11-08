from pathlib import Path
import copy, importlib.util, json, sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]

def load(path, name):
    assert path.is_file(), f'missing implementation {path.name}'
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

@pytest.fixture(scope='module')
def family():
    return load(HOME/'generator.py', 'donor_family_test')

@pytest.fixture(scope='module')
def adapter():
    return load(HOME/'workspace/parametric/adapter.py', 'donor_adapter_test')

def original_pairs():
    raw = ROOT/'shared/data/raw'
    challenges = json.loads((raw/'arc-agi_evaluation_challenges.json').read_text())['9aaea919']
    gold = json.loads((raw/'arc-agi_evaluation_solutions.json').read_text())['9aaea919']
    return challenges['train'] + [dict(input=p['input'],output=o) for p,o in zip(challenges['test'],gold)]

def test_canonical_python_all_originals(family):
    for pair in original_pairs():
        assert family.solve(pair['input']) == pair['output']
        assert family.self_check(pair['input']) == []

def test_resource_copy_and_default_bytes(adapter):
    assert (HOME/'generator.py').read_bytes() == (HOME/'workspace/parametric/family.py').read_bytes()
    assert (HOME/'reference.rkt').read_bytes() == (HOME/'workspace/parametric/canonical.rkt').read_bytes()
    assert adapter.program({'aggregation':'sum'}) == (HOME/'reference.rkt').read_text()
    assert adapter.program({'aggregation':'maximum'}) != adapter.program({'aggregation':'sum'})

@pytest.mark.parametrize('seed',[0,17,43,999])
@pytest.mark.parametrize('demos',[2,3,6])
def test_episode_contract(family,adapter,seed,demos):
    a = adapter.generate(seed,{'aggregation':'sum'},demos,4)
    b = adapter.generate(seed,{'aggregation':'maximum'},demos,4)
    assert a == adapter.generate(seed,{'aggregation':'sum'},demos,4)
    assert [p['input'] for s in ('train','test') for p in a[s]] == [p['input'] for s in ('train','test') for p in b[s]]
    assert len(a['train']) == demos and len(a['test']) == 4
    assert len({json.dumps(p['input']) for s in ('train','test') for p in a[s]}) == demos+4
    assert any(x['output']!=y['output'] for x,y in zip(a['train'],b['train']))
    for policy,e in [('sum',a),('maximum',b)]:
        for s in ('train','test'):
            for p in e[s]:
                assert not family.self_check(p['input'])
                assert family.solve(p['input'],policy) == p['output']
                assert 1<=len(p['output'])<=30 and 1<=len(p['output'][0])<=30
        assert adapter.generate(seed,{'aggregation':policy},demos,1)['test']==e['test'][:1]
    assert len(a['test'][3]['input']) == len(a['test'][3]['input'][0]) == 30

@pytest.mark.parametrize('bad',[True,-1,1.2,'3',None])
def test_reject_invalid_seed(adapter,bad):
    with pytest.raises(ValueError): adapter.generate(bad,{'aggregation':'sum'},2,4)

@pytest.mark.parametrize('field,value',[('demos',1),('demos',7),('demos',True),('queries',0),('queries',5),('queries',2.0)])
def test_reject_bad_counts(adapter,field,value):
    req=dict(seed=17,settings={'aggregation':'sum'},demos=2,queries=4);req[field]=value
    with pytest.raises(ValueError): adapter.generate(**req)

@pytest.mark.parametrize('settings',[{}, {'aggregation':'SUM'}, {'aggregation':True}, {'aggregation':'sum','extra':1},None])
def test_reject_settings(adapter,settings):
    with pytest.raises(ValueError): adapter.program(settings)

def test_finite_lesson_rivals(family,adapter):
    for seed in (0,17,43):
        for policy in ('sum','maximum'):
            e=adapter.generate(seed,{'aggregation':policy},2,4)
            for name in family.RIVALS:
                survived=all(family.rival(p['input'],policy,name)==p['output'] for p in e['train'])
                assert not (survived and any(family.rival(p['input'],policy,name)!=p['output'] for p in e['test'])),name

def test_public_privacy_shuffle_and_mutation(adapter):
    e=adapter.generate(17,{'aggregation':'sum'},3,4)
    before=copy.deepcopy(e)
    views=adapter.public_views(e,23)
    assert len(views)==4
    assert all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)
    changed=copy.deepcopy(e);changed['settings']='SECRET';changed['program_solution']='SECRET'
    for p in changed['test']: p['output']=[[9]]
    assert views==adapter.public_views(changed,23)
    assert e==before
    assert len({json.dumps(adapter.public_views(e,s)[0]) for s in range(12)})>1
    views[0]['train'][0]['input'][0][0]=42
    assert e==before

def test_standalone_generator_relocation(family,tmp_path):
    path=tmp_path/'generator.py';path.write_bytes((HOME/'generator.py').read_bytes())
    isolated=load(path,'standalone_donors')
    for i in range(10):
        assert isolated.generate(seed=19,sample_index=i)==family.generate(seed=19,sample_index=i)

@pytest.mark.parametrize('kwargs',[{'seed':True},{'sample_index':-1},{'sample_index':'2'},{'unexpected':3},{'difficulty':'bad'}])
def test_generator_controls(family,kwargs):
    with pytest.raises(ValueError): family.generate(**kwargs)

def test_protected_racket_authority_all_originals_and_profiles(family,adapter):
    from arcpuzzles.parametric_worker import _real_evaluator, _local_imports
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        assert identity['protected'] and identity['backend']=='racket'
        try:
            p=adapter.program({'aggregation':'sum'})
            for pair in original_pairs(): assert apply(p,pair['input'])==pair['output']
            for policy in family.POLICIES:
                e=adapter.generate(0,{'aggregation':policy},6,4)
                for split in ('train','test'):
                    for pair in e[split]: assert apply(e['program_solution'],pair['input'])==pair['output']
        finally: bridge.close()

@pytest.mark.parametrize('bad',[[],[[]],[[True]],[[11]],[[1],[2,3]],[[0]*31]])
def test_reject_bad_grids(family,bad):
    assert family.self_check(bad)
    with pytest.raises(ValueError): family.solve(bad)

def test_standard_positional_generator_api(family):
    assert family.generate(17,3)==family.generate(seed=17,sample_index=3)
