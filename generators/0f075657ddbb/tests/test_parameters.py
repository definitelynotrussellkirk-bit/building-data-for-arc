"""Native family regressions with independent, hand-derived expected cells."""
from pathlib import Path
import copy
import importlib.util
import json
import pytest

HOME=Path(__file__).resolve().parents[1]
P=HOME/'workspace/parametric'

@pytest.fixture(scope='module')
def mod():
    assert (P/'adapter.py').is_file(), 'native adapter is missing'
    spec=importlib.util.spec_from_file_location('frame_area_adapter_test',P/'adapter.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def fixture():
    g=[[0]*22 for _ in range(16)]
    for a,b,c,d in [(2,0,15,12),(5,3,12,9)]:
        for r in range(a,c+1):
            for col in range(b,d+1):
                if r in (a,c) or col in (b,d):g[r][col]=4
    g[0][1]=g[0][7]=2
    for c in (2,3):g[3][c]=6
    for c in (4,5,6,7):g[6][c]=6
    for r,c in [(2,16),(2,17),(6,16),(7,16),(7,17),(8,17),
                (11,16),(11,17),(11,18),(12,16),(12,17),(12,18)]:g[r][c]=1
    g[9][5]=2  # protected off-row red must not change the selector
    g[10][7]=8 # preexisting cyan is not an activation event
    return g

def test_hand_derived_key_and_remote_area_not_shape(mod):
    g=fixture(); before=copy.deepcopy(g)
    expected=copy.deepcopy(g)
    for r in range(6,12):
        for c in range(4,9):
            if expected[r][c]==0:expected[r][c]=8
    assert mod.predict(g,'fill_only')==expected
    for r,c in [(6,16),(7,16),(7,17),(8,17)]:expected[r][c]=3
    assert mod.predict(g,'key_relay')==expected
    assert g==before

def test_no_selector_and_overflow_are_identity(mod):
    for count in (0,4):
        g=fixture();g[0]=[2]*count+[0]*(22-count)
        assert mod.predict(g,'key_relay')==g

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(True,4),(3,0),(3,5),(3,True)])
def test_reject_invalid_counts(mod,d,q):
    with pytest.raises((TypeError,ValueError)):mod.generate(0,{'relay_policy':'key_relay'},d,q)

@pytest.mark.parametrize('settings',[{}, {'relay_policy':'typo'}, {'relay_policy':'fill_only','x':1}])
def test_reject_undeclared_settings(mod,settings):
    with pytest.raises((TypeError,ValueError)):mod.program(settings)

def test_canonical_bytes_and_racket_parity(mod):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    root=find_root(HOME)
    record=Catalog(root).get('0f075657ddbb')
    exact={v['program_solution'] for v in record['variants']}
    assert mod.program({'relay_policy':'fill_only'}) in exact
    runtime=root/'shared/runtime'
    apply,identity,bridge=_real_evaluator(runtime)
    try:
        assert identity['protected'] is True
        for mode in ('fill_only','key_relay'):
            program=mod.program({'relay_policy':mode})
            assert apply(program,fixture())==mod.predict(fixture(),mode)
            e=mod.generate(17,{'relay_policy':mode},2,4)
            for p in e['train']+e['test']:assert apply(program,p['input'])==p['output']
    finally:bridge.close()

def test_matched_inputs_counts_prefixes_and_private_turns(mod):
    first_shapes=set()
    for seed in range(10):
        a=mod.generate(seed,{'relay_policy':'fill_only'},6,4)
        b=mod.generate(seed,{'relay_policy':'key_relay'},6,4)
        assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
        inputs=[json.dumps(p['input']) for p in a['train']+a['test']]
        assert len(set(inputs))==10
        assert any(x['output']!=y['output'] for x,y in zip(a['train'][:2],b['train'][:2]))
        short=mod.generate(seed,{'relay_policy':'key_relay'},2,1)
        assert short['train']==b['train'][:2] and short['test']==b['test'][:1]
        first_shapes.add((len(b['test'][0]['input']),len(b['test'][0]['input'][0])))
        for i in range(4):
            view=mod.public_view(b,i)
            assert set(view)=={'train','test'} and view['test']==[{'input':b['test'][i]['input']}]
            noisy=copy.deepcopy(b);noisy['settings']='not public';noisy['test'][i]['output']=[[9]]
            assert mod.public_view(noisy,i)==view
        stress=[p for p in b['test'] if len(p['input'])==30 and len(p['input'][0])==30]
        assert len(stress)==1
        g=stress[0]['input']; points=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v]
        assert len(points)>170 and {min(r for r,c in points),max(r for r,c in points)}=={0,29}
        assert {min(c for r,c in points),max(c for r,c in points)}=={0,29}
        assert {(r//15,c//15) for r,c in points}=={(0,0),(0,1),(1,0),(1,1)}
    assert len(first_shapes)>1, 'four-query source order must be privately shuffled'

def test_public_view_validates_index_and_copies(mod):
    e=mod.generate(0,{'relay_policy':'key_relay'},2,4)
    for i in (-1,4,True):
        with pytest.raises((ValueError,IndexError)):mod.public_view(e,i)
    before=copy.deepcopy(e);view=mod.public_view(e,0);view['train'][0]['input'][0][0]=9
    assert e==before


def test_native_adapter_can_generate_a_lesson():
    assert (P/'adapter.py').is_file(), 'native family not implemented'
    spec=importlib.util.spec_from_file_location('native_lesson',P/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    episode=module.generate(0,{'relay_policy':'key_relay'},2,4)
    assert len(episode['train'])==2 and len(episode['test'])==4


def test_area_lesson_contains_nonrectangular_matching_receiver(mod):
    # Losing this distinction would let bounding-box area stand in for cell count.
    lesson=mod.generate(0,{'relay_policy':'key_relay'},2,4)
    observed=[]
    for pair in lesson['train']:
        cells=[(r,c) for r,row in enumerate(pair['output']) for c,v in enumerate(row) if v==3]
        if cells:
            area=(max(r for r,c in cells)-min(r for r,c in cells)+1)*(max(c for r,c in cells)-min(c for r,c in cells)+1)
            observed.append(area>len(cells))
    assert any(observed)


def test_audit_count_sweep_exercises_real_adapters(mod):
    path=P/'audit.py'
    assert path.is_file(), 'reusable count/export audit missing'
    spec=importlib.util.spec_from_file_location('frame_relay_audit_test',path)
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    report=audit.sweep(2)
    assert report['requests']==80 and report['pairs']==520
    assert report['matched_inputs']==40 and report['public_turns']==200
    assert report['unique_inputs']>=18
