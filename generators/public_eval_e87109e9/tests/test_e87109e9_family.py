from __future__ import annotations
import copy,importlib.util,json
from pathlib import Path
import pytest
HOME=Path(__file__).resolve().parents[1];ROOT=HOME.parents[1];BASE=HOME/'workspace/parametric'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
@pytest.fixture(scope='module')
def adapter():
    assert (BASE/'adapter.py').is_file(),'native adapter missing'
    return load('adapter_e87109e9',BASE/'adapter.py')
@pytest.fixture(scope='module')
def racket():
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');assert identity['backend']=='racket' and identity['protected']
        yield apply;bridge.close()
def official(): return json.loads((HOME/'tests/fixtures/official.json').read_text())

def test_general_rule_matches_every_official_label(racket):
    program=(HOME/'reference.rkt').read_text()
    for split in ('train','test'):
        for pair in official()[split]: assert racket(program,pair['input'])==pair['output']

def test_python_mirror_matches_every_official_label(adapter):
    for split in ('train','test'):
        for pair in official()[split]: assert adapter.model.solve(pair['input'],'legend')==pair['output']

def test_canonical_copy_is_byte_exact(adapter):
    assert adapter.program({'turn_policy':'legend'}).encode()==(HOME/'reference.rkt').read_bytes()==(BASE/'canonical.rkt').read_bytes()

@pytest.mark.parametrize('mode',['legend','opposite'])
def test_generated_claims_match_protected_racket(adapter,racket,mode):
    ep=adapter.generate(17,{'turn_policy':mode},2,4)
    for pair in ep['train']+ep['test']: assert racket(ep['program_solution'],pair['input'])==pair['output']

def test_prefixes_matched_inputs_distinct_and_two_demos_identify_setting(adapter):
    for seed in (0,17,43):
        full={m:adapter.generate(seed,{'turn_policy':m},6,4) for m in ('legend','opposite')}
        assert [p['input'] for p in full['legend']['train']+full['legend']['test']]==[p['input'] for p in full['opposite']['train']+full['opposite']['test']]
        assert len({json.dumps(p['input']) for p in full['legend']['train']+full['legend']['test']})==10
        for mode in ('legend','opposite'):
            for d in range(2,7):
                for q in range(1,5):
                    part=adapter.generate(seed,{'turn_policy':mode},d,q)
                    assert part['train']==full[mode]['train'][:d] and part['test']==full[mode]['test'][:q]
            other='opposite' if mode=='legend' else 'legend'
            assert not all(adapter.model.solve(p['input'],other)==p['output'] for p in full[mode]['train'][:2])

def test_query_shuffle_and_substantive_30_by_30_input(adapter,racket):
    positions=set()
    for seed in range(12):
        ep=adapter.generate(seed,{'turn_policy':'legend'},2,4)
        positions.add(next(i for i,p in enumerate(ep['test']) if len(p['input'])==30 and len(p['input'][0])==30))
    assert len(positions)>1
    p=next(p for p in adapter.generate(17,{'turn_policy':'opposite'},2,4)['test'] if len(p['input'])==30)
    assert len(p['output'])==24 and len(p['output'][0])==30
    bg=max(set(v for row in p['output'] for v in row),key=lambda x:sum(row.count(x) for row in p['output']))
    assert sum(v!=bg for row in p['input'][6:] for v in row)>120
    assert racket(adapter.program({'turn_policy':'opposite'}),p['input'])==p['output']

def test_public_view_ignores_private_fields_and_future_queries(adapter):
    ep=adapter.generate(17,{'turn_policy':'legend'},2,4);before=copy.deepcopy(ep);view=adapter.public_view(ep,0)
    assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
    ep['settings']={'x':'y'};ep['seed']=-1;ep['program_solution']='secret';ep['test'][0]['output']=[[9]];ep['test'][1:]=[{'input':[[9]],'output':[[9]]}]
    assert adapter.public_view(ep,0)==view
    view['train'][0]['input'][0][0]=99;assert ep['train']==before['train']

def test_finite_rivals_leave_no_harmful_minimum_lesson_survivor(adapter):
    for seed in range(24):
        for mode in ('legend','opposite'):
            ep=adapter.generate(seed,{'turn_policy':mode},2,4)
            for rival in adapter.model.RIVALS:
                fits=all(adapter.model.solve(p['input'],mode,rival)==p['output'] for p in ep['train'])
                assert not fits or all(adapter.model.solve(p['input'],mode,rival)==p['output'] for p in ep['test']), (seed,mode,rival)

@pytest.mark.parametrize('mode',['legend','opposite'])
def test_seed_29_minimum_lesson_rejects_legend_position_parity(adapter,mode):
    """Catch a curriculum mutation where legend order encodes alternating turns."""
    ep=adapter.generate(29,{'turn_policy':mode},2,4)
    assert not all(
        adapter.model.solve(p['input'],mode,'legend_order_parity')==p['output']
        for p in ep['train']
    )

def test_wrong_turn_intermediate_changes_output(adapter,racket):
    ep=adapter.generate(17,{'turn_policy':'legend'},2,4);p=ep['test'][0]
    assert racket(adapter.program({'turn_policy':'opposite'}),p['input'])!=p['output']

@pytest.mark.parametrize('d,q',[(1,4),(7,4),(2,0),(2,5),(True,4),(2,True),(2.0,4)])
def test_count_validation(adapter,d,q):
    with pytest.raises((TypeError,ValueError)): adapter.generate(1,{'turn_policy':'legend'},d,q)
@pytest.mark.parametrize('settings',[{},None,{'turn_policy':'bad'},{'turn_policy':True},{'turn_policy':'legend','extra':1}])
def test_setting_validation(adapter,settings):
    with pytest.raises((TypeError,ValueError)): adapter.program(settings)

def test_ordinary_generator_is_self_checking(adapter,racket):
    gen=load('generator_e87109e9',HOME/'generator.py')
    for difficulty in ('easy','medium','hard'):
        g=gen.generate(seed=17,sample_index=3,difficulty=difficulty);assert gen.self_check(g)==[]
        assert racket(adapter.program({'turn_policy':'legend'}),g)==adapter.model.solve(g,'legend')
