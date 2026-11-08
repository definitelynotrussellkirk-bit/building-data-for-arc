"""Behavioral regressions for the post-capping residual component family."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME=Path(__file__).resolve().parents[1]/'workspace/parametric'

def load(name):
    s=importlib.util.spec_from_file_location('native_142_'+name,HOME/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def test_adapter_implemented():
    assert (HOME/'adapter.py').is_file(), 'native residual-component adapter missing'


@pytest.fixture(scope='module')
def a(): return load('adapter')


def test_capping_changes_largest_component_and_relay_consumes_that_change(a):
    g=[[2,2,2,2,2,2,2,0,0], [0]*9, [2,2,2,2,0,0,0,0,0],
       [0,2,0,0,0,0,0,0,0], [0,2,0,0,0,0,0,0,0]]
    want=[[4,2,2,2,2,2,4,0,0], [0]*9, [8,8,8,8,0,0,0,0,0],
          [0,8,0,0,0,0,0,0,0], [0,8,0,0,0,0,0,0,0]]
    assert a.family.solve(g,'residual_largest')==want
    assert a.family.intermediate(g)['size']==6
    assert a.family.solve(g,'original_largest')!=want


def test_singletons_pairs_nonred_lines_and_empty_grid_are_total(a):
    for grid,want in [([[2]],[[4]]),([[2,2]],[[4,4]]),([[2],[2],[2]],[[4],[8],[4]]),([[3,3,3]],[[3,3,3]]),([[0]],[[0]])]:
        assert a.family.solve(grid,'residual_largest')==want


def test_equal_residual_sizes_choose_row_major_first(a):
    assert a.family.solve([[2,2,0,2,2],[2,0,0,0,2]],'residual_largest')==[[8,8,0,2,2],[8,0,0,0,2]]


def test_cycles_are_unchanged_by_caps_then_can_win_relay(a):
    g=[[2,2,0,2,2,2,2,2],[2,2,0,0,0,0,0,0]]
    assert a.family.solve(g,'residual_largest')==[[8,8,0,4,2,2,2,4],[8,8,0,0,0,0,0,0]]


def test_default_exact_catalog_authority(a):
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    ps={v['program_solution'] for v in Catalog(find_root(__file__)).get('142a3a64b02a')['variants']}
    assert ps=={a.program({'mode':'caps'})}


@pytest.mark.parametrize('seed',[0,17,2**63-1])
def test_matched_prefix_stable_queries_and_orientation_teaching(a,seed):
    original=None
    for mode in a.family.MODES:
        full=a.generate(seed,{'mode':mode},6,4);small=a.generate(seed,{'mode':mode},2,1)
        assert full['train'][:2]==small['train'] and full['test'][:1]==small['test']
        inputs=[p['input'] for p in full['train']+full['test']]
        assert len({json.dumps(g) for g in inputs})==10
        if original is None: original=inputs
        else: assert original==inputs
        assert not a.family.teaching_check(full)['query_disagreeing_survivors']
        assert not a.family.teaching_check(small)['query_disagreeing_survivors']
        for p in full['train'][:2]:
            cs=a.family.components(p['input'],2)
            assert any(len(set(r for r,c in g))==1 and len(g)>2 for g in cs)
            assert any(len(set(c for r,c in g))==1 and len(g)>2 for g in cs)
        boundary=full['test'][-1]['input']
        assert len(boundary)==30 and len(boundary[0])==30
        assert sum(v!=0 for row in boundary for v in row)>=180
        assert all(any(edge) for edge in [boundary[0],boundary[-1],[r[0] for r in boundary],[r[-1] for r in boundary]])


@pytest.mark.parametrize('name,value',[('seed',True),('seed',-1),('seed',2**63),('seed',1.0),('demos',1),('demos',7),('demos',True),('queries',0),('queries',5)])
def test_invalid_request_is_rejected(a,name,value):
    kw=dict(seed=0,settings={'mode':'caps'},demos=2,queries=4);kw[name]=value
    with pytest.raises(ValueError):a.generate(**kw)


@pytest.mark.parametrize('setting',[{},None,{'mode':'x'},{'mode':True},{'mode':'caps','ignored':1}])
def test_invalid_settings_are_rejected(a,setting):
    with pytest.raises(ValueError):a.program(setting)


@pytest.mark.parametrize('bad',[[],[[]],[[True]],[[10]],[[0],[0,2]],[[0]*31]])
def test_invalid_grids_are_rejected(a,bad):
    with pytest.raises(ValueError):a.family.solve(bad,'caps')


def test_public_bytes_ignore_private_metadata_at_all_pair_levels(a):
    e=a.generate(0,{'mode':'residual_largest'},2,4);before=a.family.public_view(e,0)
    dirty=copy.deepcopy(e);dirty['settings']='private';dirty['train'][0]['program']='private'
    dirty['test'][0]['output']=[[9]];dirty['seed']=17;dirty['future_inputs']=[[[9]]]
    assert a.family.public_view(dirty,0)==before
    assert set(before)=={'train','test'} and len(before['test'])==1
    assert all(set(p)=={'input','output'} for p in before['train'])
    assert set(before['test'][0])=={'input'}


def test_allcolor_shortcut_is_exposed_under_default_as_well_as_alternative(a):
    before=json.loads((HOME/'regression/allcolor-before.json').read_text())
    assert all(a.family.solve(g,'caps')==a.family.solve(g,'allcolor_remaining') for g in before['train_inputs'])
    assert a.family.solve(before['query_input'],'caps')!=a.family.solve(before['query_input'],'allcolor_remaining')
    for mode in a.family.MODES:
        e=a.generate(0,{'mode':mode},2,4)
        assert any(a.family.solve(p['input'],'allcolor_remaining')!=p['output'] for p in e['train'])


def test_programs_are_complete_single_forms():
    from arc_repl.parser import parse_all, Symbol
    for p in (HOME/'rules').glob('*.rkt'):
        forms=parse_all(p.read_text());assert len(forms)==1 and forms[0][0] in (Symbol('rule!'),Symbol('lambda'))


def test_first_demo_is_not_a_tiny_fixed_geometry_catalog(a):
    first=[a.generate(seed,{'mode':'caps'},2,4)['train'][0]['input'] for seed in range(32)]
    assert len({json.dumps(g) for g in first})>=28
    assert len({(len(g),len(g[0])) for g in first})>=8
