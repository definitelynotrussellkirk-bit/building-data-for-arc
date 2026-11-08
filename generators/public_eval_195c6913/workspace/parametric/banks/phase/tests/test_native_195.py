import copy
import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).resolve().parents[1]/'workspace/parametric'

@pytest.fixture(scope='module')
def a():
    assert (P/'adapter.py').exists(),'Missing native phase-policy adapter'
    s=importlib.util.spec_from_file_location('terrain195_native_tests',P/'adapter.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def test_reference_program_exact_bytes(a):
    assert a.program({'phase':'carry'}).encode()==(P.parent.parent/'reference.rkt').read_bytes()
    assert a.program({'phase':'restart'})!=a.program({'phase':'carry'})

def test_minimum_lesson_bounded_rival_identification(a):
    for seed in range(32):
        for mode in a.core.MODES:
            e=a.generate(seed,{'phase':mode},2,4)
            for rival in a.RIVALS:
                if all(a.core.solve(p['input'],mode,rival=rival)==p['output'] for p in e['train']):
                    assert all(a.core.solve(p['input'],mode,rival=rival)==p['output'] for p in e['test']),(seed,mode,rival)

def test_inputs_settings_prefixes_and_copy_isolation(a):
    for seed in (0,17):
        full=a.generate(seed,{'phase':'carry'},6,4)
        for mode in a.core.MODES:
            for n in range(2,7):
                for q in range(1,5):
                    e=a.generate(seed,{'phase':mode},n,q)
                    assert [p['input'] for p in e['train']]==[p['input'] for p in full['train'][:n]]
                    assert [p['input'] for p in e['test']]==[p['input'] for p in full['test'][:q]]
        copied=a.inputs(seed);copied[0][0][0]=99
        assert a.generate(seed,{'phase':'carry'},6,4)==full

def test_stress_and_presentation_diversity(a):
    first=set()
    for seed in range(32):
        e=a.generate(seed,{'phase':'carry'},2,4);bank=a.inputs(seed)
        assert len({repr(p['input']) for p in e['train']+e['test']})==6
        large=[p for p in e['test'] if len(p['input'])==len(p['input'][0])==30]
        assert len(large)==1
        p=large[0];d=a.core.parse(p['input'])
        assert sum(v!=d['bg'] for row in p['input'] for v in row)>200
        assert sum(v!=x for row,other in zip(p['input'],p['output']) for v,x in zip(row,other))>50
        first.add(next(i for i in range(6,10) if bank[i]==e['test'][0]['input']))
    assert len(first)==4

@pytest.mark.parametrize('settings',[{},[],{'phase':'bad'},{'phase':True},{'phase':'carry','extra':0}])
def test_invalid_settings_fail_closed(a,settings):
    with pytest.raises(ValueError):a.generate(0,settings,2,4)

@pytest.mark.parametrize('seed,demos,queries',[(True,2,4),(-1,2,4),(1.0,2,4),(0,True,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,2,True)])
def test_invalid_request_fail_closed(a,seed,demos,queries):
    with pytest.raises(ValueError):a.generate(seed,{'phase':'carry'},demos,queries)

def test_public_view_private_field_invariance(a):
    e=a.generate(17,{'phase':'restart'},2,4);baseline=a.public_turn(e,0)
    e['program_solution']='secret';e['settings']={'phase':'carry'};e['future']=e['test'][1:]
    for p in e['train']+e['test']:p['private']='secret'
    for p in e['test']:p['output']=[[9]]
    assert a.public_turn(e,0)==baseline
    assert set(baseline)=={'train','test'} and set(baseline['test'][0])=={'input'}
    for index in (-1,True,4,1.0):
        with pytest.raises(ValueError):a.public_turn(e,index)


def test_racket_shortcuts_match_independent_claims(a):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid
    root=P.parents[3]
    with _local_imports(root/'shared/runtime',root/'shared/runtime'):
        apply,identity,bridge=_real_evaluator(root/'shared/runtime')
        try:
            assert identity['protected'] is True
            for mode in a.core.MODES:
                e=a.generate(17,{'phase':mode},2,4)
                for rival in a.RIVALS:
                    # Use both minimum demonstrations to catch repeated-chip and
                    # multi-source semantics, including rivals equivalent in restart.
                    program=a.rival_program(mode,rival)
                    for p in e['train']:
                        assert _grid(apply(program,p['input']))==a.core.solve(p['input'],mode,rival=rival),(mode,rival)
        finally:bridge.close()
