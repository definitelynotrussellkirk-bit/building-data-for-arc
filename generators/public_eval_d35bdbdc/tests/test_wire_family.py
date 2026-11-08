from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import pytest

HOME = Path(__file__).resolve().parents[1]
BASE = HOME / 'workspace/parametric'

def load():
    path = BASE / 'adapter.py'
    assert path.is_file(), 'native adapter is not implemented'
    spec = importlib.util.spec_from_file_location('_test_wire_adapter', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize('index', range(6))
def test_original_labels(index):
    a=load(); p=json.loads((HOME/'tests/originals.json').read_text())[index]
    assert a.predict(p['input'], 'one_hop') == p['output']

def test_canonical_bytes_and_distinct_alternative():
    a=load()
    assert a.program({'transfer':'one_hop'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()
    assert a.program({'transfer':'follow_chain'})!=a.program({'transfer':'one_hop'})

@pytest.mark.parametrize('d',range(2,7))
@pytest.mark.parametrize('q',range(1,5))
def test_count_prefixes_and_matched_inputs(d,q):
    a=load(); full=a.generate(17,{'transfer':'one_hop'},6,4)
    e=a.generate(17,{'transfer':'one_hop'},d,q);alt=a.generate(17,{'transfer':'follow_chain'},d,q)
    assert e['train']==full['train'][:d] and e['test']==full['test'][:q]
    assert [p['input'] for s in ('train','test') for p in e[s]]==[p['input'] for s in ('train','test') for p in alt[s]]
    assert len({json.dumps(p['input']) for s in ('train','test') for p in e[s]})==d+q
    assert any(p['output']!=t['output'] for p,t in zip(e['train'],alt['train']))

def test_private_field_invariance_and_mutation_isolation():
    a=load();state=random.getstate();e=a.generate(43,{'transfer':'follow_chain'},2,4)
    assert random.getstate()==state
    old=deepcopy(e);view=a.public_turn(e,0)
    e['private']={'leak':'CANARY'};e['settings']={'leak':'CANARY'};e['program_solution']='CANARY';e['test'][0]['output']=[[9]]
    e['test'][1:] = [{'input':[[9]],'output':[[9]]}]*3
    assert a.public_turn(e,0)==view
    assert a.generate(43,{'transfer':'follow_chain'},2,4)==old
    view['train'][0]['input'][0][0]=99
    assert a.public_turn(old,0)['train'][0]['input'][0][0]!=99

def test_substantive_large_query():
    a=load();e=a.generate(0,{'transfer':'follow_chain'},2,4)
    large=[p for p in e['test'] if len(p['input'])==len(p['input'][0])==30]
    assert large
    occupied=[(r,c) for r,row in enumerate(large[0]['input']) for c,v in enumerate(row) if v]
    assert len(occupied)>100
    assert max(r for r,c in occupied)-min(r for r,c in occupied)>=25
    assert max(c for r,c in occupied)-min(c for r,c in occupied)>=25
    assert a.predict(large[0]['input'],'follow_chain')!=a.predict(large[0]['input'],'one_hop')

@pytest.mark.parametrize('seed',[-1,True,1.0,'1'])
def test_bad_seed_rejected(seed):
    with pytest.raises(ValueError):load().generate(seed,{'transfer':'one_hop'},2,4)

@pytest.mark.parametrize('grid',[[],[[]],[[True]],[[1.0]],[[10]],[[1],[1,2]],[[0]*31]])
def test_bad_grid_rejected(grid):
    with pytest.raises(ValueError):load().predict(grid,'one_hop')

@pytest.mark.parametrize('seed',range(8))
def test_named_rivals_cannot_fit_demos_then_change_queries(seed):
    a=load()
    for mode in a.PARAMETERS['transfer']:
        ep=a.generate(seed,{'transfer':mode},2,4)
        for rival in a.rivals():
            if all(a.predict(p['input'],rival)==p['output'] for p in ep['train']):
                assert all(a.predict(p['input'],rival)==p['output'] for p in ep['test']),(seed,mode,rival)

@pytest.mark.parametrize('settings',[{}, {'transfer':True},{'transfer':'bad'},{'transfer':'one_hop','extra':1}])
def test_bad_settings_rejected(settings):
    with pytest.raises(ValueError):load().generate(0,settings,2,4)

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True),(2.0,4)])
def test_bad_counts_rejected(d,q):
    with pytest.raises(ValueError):load().generate(0,{'transfer':'one_hop'},d,q)

def test_bounded_pointer_cycles():
    e=load()._engine
    assert e.trace(1,{1:2,2:3,3:1})==(1,[1,2,3])
    assert e.trace(1,{1:2,2:3,3:1},1)==(2,[1])

def test_standalone_generator_drift_and_native_relocation(tmp_path):
    import shutil
    a=load()
    for name in ('adapter.py','engine.py','canonical.rkt'):
        shutil.copyfile(BASE/name,tmp_path/name)
    spec=importlib.util.spec_from_file_location('_relocated_wire',tmp_path/'adapter.py')
    moved=importlib.util.module_from_spec(spec);spec.loader.exec_module(moved)
    assert moved.generate(17,{'transfer':'follow_chain'},2,4)==a.generate(17,{'transfer':'follow_chain'},2,4)
    spec=importlib.util.spec_from_file_location('_wire_builder',BASE/'build_generator.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    assert (HOME/'generator.py').read_text()==builder.source()
    shutil.copyfile(HOME/'generator.py',tmp_path/'ordinary.py')
    spec=importlib.util.spec_from_file_location('_standalone_wire',tmp_path/'ordinary.py')
    ordinary=importlib.util.module_from_spec(spec);spec.loader.exec_module(ordinary)
    for i in range(10):assert not ordinary.self_check(ordinary.generate(17,i)['input'])

def test_public_validator_and_negative_cases():
    a=load();path=BASE/'public_io.py';assert path.is_file(),'strict public-file validator missing'
    spec=importlib.util.spec_from_file_location('_wire_public_io',path)
    io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)
    view=a.public_turn(a.generate(17,{'transfer':'follow_chain'},2,4),0)
    raw=io.encode(view)
    import hashlib
    io.validate(raw,hashlib.sha256(raw).hexdigest())
    bad=[]
    x=deepcopy(view);x['settings']={'transfer':'follow_chain'};bad.append(x)
    x=deepcopy(view);x['test'][0]['output']=[[1]];bad.append(x)
    x=deepcopy(view);x['test'].append({'input':[[2]]});bad.append(x)
    x=deepcopy(view);x['test'][0]['input']=[[True]];bad.append(x)
    x=deepcopy(view);x['test'][0]['input']=deepcopy(x['train'][0]['input']);bad.append(x)
    for x in bad:
        with pytest.raises(ValueError):io.encode(x)
    with pytest.raises(ValueError):io.validate(raw,'0'*64)
    with pytest.raises(ValueError):io.validate(raw+b'\n',hashlib.sha256(raw+b'\n').hexdigest())

def test_auditor_rejects_stale_binding_and_counts_shape_differences(tmp_path):
    path=BASE/'verify.py';assert path.is_file(),'source-bound verifier missing'
    spec=importlib.util.spec_from_file_location('_wire_verifier',path)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    import hashlib
    p=tmp_path/'source.py';p.write_text('original')
    receipt={'status':'passed','source_binding':{'files':[{'path':'source.py','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
    v.verify_binding(tmp_path,receipt)
    p.write_text('changed')
    with pytest.raises(ValueError):v.verify_binding(tmp_path,receipt)
    assert v.differences([[1]],[[1,2],[3,4]])=={'overlap_changed':0,'shape_extra_cells':3,'changed_cells':3}

def test_seed57_largest_two_shortcut_is_defeated_in_minimum_lesson():
    a=load();ep=a.generate(57,{'transfer':'one_hop'},2,4)
    assert any(a.predict(p['input'],'largest_two')!=p['output'] for p in ep['train'])

def test_first_lesson_wire_touches_a_nonreceiver_without_selecting_it():
    a=load();g=a.generate(17,{'transfer':'one_hop'},2,4)['train'][0]['input'];cert=a.parse(g)
    touched=[i for i,b in enumerate(cert['beads']) if any(abs(r-u)+abs(c-v)==1 for r,c in b['cells'] for u,v in cert['wire'])]
    assert set(touched)-set(cert['selected']), 'only receivers touch the wire; endpoint reasoning is not taught'

def test_receiver_role_pair_varies_beyond_rigid_edge_layout():
    a=load();pairs=set()
    for seed in range(16):
        for grid,_ in a._engine.bank(seed):pairs.add(tuple(a.parse(grid)['selected']))
    assert len(pairs)>=10, f'only {len(pairs)} of 15 geometric role pairs exercised'
