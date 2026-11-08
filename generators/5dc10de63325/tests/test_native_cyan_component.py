from pathlib import Path
import importlib.util
import json
from copy import deepcopy
import pytest
from reviewer_support import find_root
ROOT=find_root(__file__)
HOME=ROOT/'generators/5dc10de63325/workspace/parametric'

@pytest.fixture(scope='module')
def native():
    assert (HOME/'adapter.py').is_file(), 'Native adapter has not been implemented'
    spec=importlib.util.spec_from_file_location('cyan_native_test', HOME/'adapter.py')
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def test_canonical_exact_and_existing_settings_reused(native):
    from arcpuzzles import Catalog
    sources={v['program_solution'] for v in Catalog(ROOT).get(native.TASK)['variants'] if isinstance(v.get('program_solution'),str)}
    assert native.program({'fill_order':'bottom_row_first'}) == sources.pop()
    for setting in native.LEGACY.ALLOWED_FILL_ORDERS:
        assert native.program({'fill_order':setting}) == native.LEGACY.materialize_rule(setting)

def test_component_selection_changes_count_before_glyph(native):
    g=[[8,8,8,0,0,0],[8,8,0,0,8,0],[0,0,0,0,8,0],[8,8,8,0,0,0]]
    # Global count=10; largest monochromatic cardinal component has 5 cells.
    q1=[[0,0,0,0,0],[0,8,0,0,8],[0,0,0,0,0],[0,0,0,0,0],[0,8,0,0,8]]
    q2=[[0,0,0,0,0],[8,8,0,8,8],[0,0,0,0,0],[0,0,0,0,0],[8,8,0,8,8]]
    assert native.predict(g,'largest_component_count') == q1
    assert native.predict(g,'bottom_row_first') == q2

def test_diagonal_is_not_cardinal_and_noncyan_is_not_counted(native):
    g=[[8,0,9],[0,8,9],[9,9,9]]
    assert native.cyan_sizes(g)==[1,1]
    assert native.predict(g,'largest_component_count')==[[0]*5 for _ in range(5)]

@pytest.mark.parametrize('settings',[None,{}, {'fill_order':'bad'}, {'fill_order':'bottom_row_first','extra':1}, {'fill_order':True}])
def test_invalid_settings_fail_closed(native,settings):
    with pytest.raises((ValueError,TypeError)): native.program(settings)

@pytest.mark.parametrize('kwargs',[{'seed':True},{'seed':-1},{'demos':3},{'demos':7},{'demos':True},{'queries':0},{'queries':5},{'queries':True}])
def test_request_limits_fail_closed(native,kwargs):
    args=dict(seed=0,settings={'fill_order':'bottom_row_first'},demos=4,queries=4); args.update(kwargs)
    with pytest.raises((ValueError,TypeError)): native.generate(**args)

def test_no_count_clamp_above_canonical_glyph_range(native):
    # The actual source returns an empty tile at q=5, not a saturated full tile.
    assert native.predict([[8]*5 for _ in range(4)],'bottom_row_first')==[[0]*5 for _ in range(5)]

def test_matched_inputs_prefix_stable_and_unique(native):
    for seed in (0,17,319):
        ep=native.generate(seed,{'fill_order':'bottom_row_first'},4,4)
        grids=[p['input'] for s in ('train','test') for p in ep[s]]
        assert len({json.dumps(g) for g in grids})==8
        for setting in native.SETTINGS:
            other=native.generate(seed,{'fill_order':setting},6,1)
            assert [p['input'] for p in other['train'][:4]]==[p['input'] for p in ep['train']]
            assert other['test'][0]['input']==ep['test'][0]['input']

def test_large_case_contains_distributed_signal_and_dense_distractors(native):
    ep=native.generate(17,{'fill_order':'largest_component_count'},4,4)
    g=ep['test'][3]['input']; assert len(g)==len(g[0])==30
    assert sum(v!=0 for row in g for v in row)>=200
    assert sum(v==8 for row in g for v in row)==19
    assert 8 in g[0] and 8 in g[-1]
    assert any(row[0]==8 for row in g) and any(row[-1]==8 for row in g)

def test_teaching_uses_only_demos_and_rejects_short_lesson(native):
    ep=native.generate(0,{'fill_order':'largest_component_count'},4,4)
    report=native.teaching(ep); assert report['passed']
    changed=deepcopy(ep); changed['test'][0]['output']=[[9]]
    altered=native.teaching(changed)
    assert altered['survivors']==report['survivors']
    assert not altered['passed']
    short=deepcopy(ep); short['train']=ep['train'][:3]
    assert not native.teaching(short)['passed']

def test_public_turns_ignore_all_private_fields(native):
    ep=native.generate(17,{'fill_order':'largest_component_count'},4,4)
    original=native.public_turn(ep,0)
    private=deepcopy(ep); private['settings']={'secret':9}; private['program_solution']='secret'
    for split in ('train','test'):
        for pair in private[split]: pair['hidden']={'query_answers':123}
    private['test'][0]['output']=[[9]]; private['test'][1:]=[]
    assert native.public_turn(private,0)==original
    assert set(original)=={'train','test'} and len(original['test'])==1
    assert set(original['test'][0])=={'input'}
