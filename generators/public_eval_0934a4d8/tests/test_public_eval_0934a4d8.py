"""Behavioral contract for the public 0934a4d8 symmetry-repair family."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME=Path(__file__).resolve().parents[1]
ROOT=HOME.parents[1]


def load_adapter():
    path=HOME/'workspace/parametric/adapter.py'
    assert path.is_file(),'native adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('_test_public_eval_0934a4d8_adapter',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


def originals():
    challenge=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['0934a4d8']
    gold=json.loads((ROOT/'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['0934a4d8']
    return challenge['train']+[{'input':p['input'],'output':gold[i]} for i,p in enumerate(challenge['test'])]


def test_adapter_is_implemented():
    assert (HOME/'workspace/parametric/adapter.py').is_file()


@pytest.mark.parametrize('index',range(5))
def test_general_python_rule_matches_every_original(index):
    pair=originals()[index]
    assert load_adapter().model.solve(pair['input'],'patch')==pair['output']


@pytest.mark.parametrize('index',range(5))
def test_all_visible_orbits_are_consistent_in_originals(index):
    adapter=load_adapter();grid=originals()[index]['input'];state=adapter.model.analyze(grid)
    assert state['visible_orbit_conflicts']==0
    assert state['unrecoverable_hidden_cells']==0


def test_hidden_public_test_requires_transpose_augmented_orbit():
    adapter=load_adapter();grid=originals()[-1]['input'];state=adapter.model.analyze(grid)
    assert state['bbox']==(14,22,0,2)
    assert any(adapter.model.visible_values(grid,r,c,include_transpose=False)==set() for r in range(14,23) for c in range(3))
    assert adapter.model.recover_patch(grid)==originals()[-1]['output']


def test_reference_resource_is_exact_canonical_source():
    adapter=load_adapter()
    assert adapter.program({'output_mode':'patch'})==(HOME/'reference.rkt').read_text()


def test_alternative_crops_bbox_of_recovered_unique_rarest_color():
    adapter=load_adapter();grid=adapter.model.sample_input(7,0)
    patch=adapter.model.recover_patch(grid);color,bbox=adapter.model.rarest_marker(patch)
    assert sum(v==color for row in patch for v in row)==2
    r0,r1,c0,c1=bbox
    assert adapter.model.solve(grid,'marker_bbox')==[row[c0:c1+1] for row in patch[r0:r1+1]]
    assert adapter.model.solve(grid,'marker_bbox')!=patch


@pytest.mark.parametrize('mode',['patch','marker_bbox'])
def test_two_demos_teach_setting_and_reject_named_rivals(mode):
    adapter=load_adapter();episode=adapter.generate(17,{'output_mode':mode},2,4)
    pairs=episode['train']+episode['test']
    assert len(episode['train'])==2 and len(episode['test'])==4
    assert len({json.dumps(p['input']) for p in pairs})==6
    other='marker_bbox' if mode=='patch' else 'patch'
    assert all(adapter.model.solve(p['input'],other)!=p['output'] for p in episode['train'])
    for rival in adapter.model.RIVALS:
        assert any(adapter.model.solve(p['input'],mode,rival)!=p['output'] for p in episode['train']),rival


def test_setting_blind_prefix_stability_and_shuffled_query_order():
    adapter=load_adapter();orders=set()
    for seed in range(20):
        full=adapter.generate(seed,{'output_mode':'patch'},6,4)
        alt=adapter.generate(seed,{'output_mode':'marker_bbox'},6,4)
        assert [p['input'] for p in full['train']+full['test']]==[p['input'] for p in alt['train']+alt['test']]
        for demos,queries in ((2,1),(3,4),(6,2)):
            prefix=adapter.generate(seed,{'output_mode':'patch'},demos,queries)
            assert prefix['train']==full['train'][:demos]
            assert prefix['test']==full['test'][:queries]
        orders.add(tuple(adapter.model.query_order(seed)))
    assert len(orders)>1 and any(order[0]!=0 for order in orders)


def test_query_bank_contains_substantive_30_by_30_input():
    adapter=load_adapter();episode=adapter.generate(3,{'output_mode':'patch'},2,4)
    assert any(len(p['input'])==len(p['input'][0])==30 for p in episode['test'])
    for pair in episode['train']+episode['test']:
        assert max(len(pair['input']),len(pair['input'][0]),len(pair['output']),len(pair['output'][0]))<=30
        assert sum(v!=8 for row in pair['input'] for v in row)>100


def test_public_view_exposes_one_unlabelled_query_and_is_private_field_invariant():
    adapter=load_adapter();episode=adapter.generate(9,{'output_mode':'patch'},2,4)
    view=adapter.public_view(episode,1)
    assert view=={'train':episode['train'],'test':[{'input':episode['test'][1]['input']}]}
    episode['seed']='private';episode['program_solution']='secret';episode['test'][1]['output']=[[9]];episode['test'][0]['input']=[[8]]
    assert adapter.public_view(episode,1)==view


@pytest.mark.parametrize('settings',[None,{}, {'output_mode':True},{'output_mode':'bad'},{'output_mode':'patch','extra':0}])
def test_unknown_settings_fail_closed(settings):
    with pytest.raises(ValueError):load_adapter().program(settings)


@pytest.mark.parametrize('demos,queries',[(True,4),(1,4),(7,4),(2,False),(2,0),(2,5),(2.0,4)])
def test_invalid_counts_fail_closed(demos,queries):
    with pytest.raises(ValueError):load_adapter().generate(1,{'output_mode':'patch'},demos,queries)


def test_base_generator_worker_contract():
    path=HOME/'generator.py';assert path.is_file()
    spec=importlib.util.spec_from_file_location('_test_public_eval_0934a4d8_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for seed,index in ((2,0),(11,1)):
        assert module.generate(seed,index,difficulty=None)==module.generate(seed,index,difficulty='medium')
        assert module.self_check(module.generate(seed,index))==[]
    with pytest.raises(ValueError):module.generate(1,0,difficulty='unknown')


@pytest.fixture(scope='module')
def racket():
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    assert identity['backend']=='racket' and identity['protected'] is True
    yield apply
    bridge.close()


@pytest.mark.parametrize('index',range(5))
def test_protected_racket_matches_every_original(index,racket):
    adapter=load_adapter();pair=originals()[index]
    assert racket(adapter.program({'output_mode':'patch'}),pair['input'])==pair['output']


@pytest.mark.parametrize('seed',[0,17,43])
@pytest.mark.parametrize('mode',['patch','marker_bbox'])
def test_generated_labels_match_protected_racket(seed,mode,racket):
    adapter=load_adapter();episode=adapter.generate(seed,{'output_mode':mode},2,4)
    for pair in episode['train']+episode['test']:
        assert racket(episode['program_solution'],pair['input'])==pair['output']


def test_bounded_audit_tool_rejects_all_named_rivals():
    path=HOME/'workspace/parametric/audit_native.py'
    assert path.is_file(),'bounded audit tool has not been implemented'
    spec=importlib.util.spec_from_file_location('_test_public_eval_0934a4d8_audit',path)
    tool=importlib.util.module_from_spec(spec);sys.modules[spec.name]=tool;spec.loader.exec_module(tool)
    for seed in range(4):
        for mode in tool.adapter.model.MODES:
            episode=tool.adapter.generate(seed,{'output_mode':mode},2,4)
            assert tool.teaching_check(episode,mode)==[]
