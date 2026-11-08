"""Native mirror curriculum: behavioral, independent expected-value regressions."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / 'workspace' / 'parametric'

def load(name):
    spec = importlib.util.spec_from_file_location('native_b9_' + name, HOME / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_entrypoint_exists():
    assert (HOME / 'adapter.py').is_file(), 'native adapter is not implemented'


@pytest.fixture(scope='module')
def family():
    return load('family')


def test_relay_measures_red_components_after_mirror_classification(family):
    grid = [
        [8,0,0,8,0,0,0,0],
        [0,8,8,0,0,8,0,0],
        [0,8,0,8,8,8,0,0],
        [0,0,0,0,0,0,0,8],
        [0,8,0,0,0,0,0,0],
        [0,8,8,0,0,0,0,0],
        [8,0,0,0,0,0,0,0],
    ]
    want = [
        [2,0,0,5,0,0,0,0],
        [0,2,2,0,0,4,0,0],
        [0,2,0,4,4,4,0,0],
        [0,0,0,0,0,0,0,2],
        [0,2,0,0,0,0,0,0],
        [0,2,2,0,0,0,0,0],
        [2,0,0,0,0,0,0,0],
    ]
    assert family.solve(grid, 'paired_rows') == want
    assert family.intermediate(grid) == {'size': 3, 'cells': [[1,1],[1,2],[2,1]], 'rows': [1,2]}


def test_empty_red_set_is_a_total_noop(family):
    assert family.solve([[8,0],[0,0]], 'paired_rows') == [[5,0],[0,0]]
    assert family.solve([[0]], 'paired_rows') == [[0]]
    assert family.solve([[8]], 'paired_rows') == [[2]]


def test_default_uses_exact_selected_canonical_bytes():
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    adapter = load('adapter')
    record = Catalog(find_root(__file__)).get('b9b63ae52d91')
    canonical = {v['program_solution'] for v in record['variants']}
    assert canonical == {adapter.program({'mode': 'vertical'})}


@pytest.mark.parametrize('seed', [0, 17, 2**63-1])
def test_counts_prefixes_matched_inputs_and_distinct_queries(family, seed):
    adapter = load('adapter')
    original = None
    for mode in family.MODES:
        full = adapter.generate(seed, {'mode': mode}, 6, 4)
        small = adapter.generate(seed, {'mode': mode}, 2, 1)
        assert small['train'] == full['train'][:2]
        assert small['test'] == full['test'][:1]
        inputs = [p['input'] for p in full['train'] + full['test']]
        assert len(set(json.dumps(g) for g in inputs)) == 10
        if original is None:
            original = inputs
        else:
            assert inputs == original
        assert not family.teaching_check(full)['query_disagreeing_survivors']
        grid = full['test'][-1]['input']
        assert (len(grid),len(grid[0])) == (30,30)
        assert sum(v == 8 for row in grid for v in row) >= 250
        assert all(any(v == 8 for v in edge) for edge in [grid[0],grid[-1],[r[0] for r in grid],[r[-1] for r in grid]])
        assert not family.teaching_check(small)['query_disagreeing_survivors']


@pytest.mark.parametrize('field,value', [('seed',True),('seed',-1),('seed',2**63),('seed',1.0),('demos',True),('demos',1),('demos',7),('queries',0),('queries',5)])
def test_invalid_request_fails_closed(field, value):
    adapter = load('adapter')
    args = dict(seed=0, settings={'mode':'vertical'}, demos=2, queries=4)
    args[field] = value
    with pytest.raises(ValueError):
        adapter.generate(**args)


@pytest.mark.parametrize('setting', [{}, {'mode':True},{'mode':'unknown'},{'mode':'vertical','extra':1},None])
def test_invalid_settings_fail_closed(setting):
    with pytest.raises(ValueError):
        load('adapter').program(setting)


def test_public_projection_drops_nested_and_top_level_private_values(family):
    e = load('adapter').generate(17, {'mode':'paired_rows'},2,4)
    before = family.public_view(e, 0)
    dirty = copy.deepcopy(e)
    dirty['settings'] = 'secret'
    dirty['test'][0]['output'] = [[9]]
    dirty['train'][0]['program'] = 'secret'
    dirty['train'][0]['seed'] = 42
    dirty['future_inputs'] = [[[9]]]
    assert family.public_view(dirty, 0) == before
    assert set(before) == {'train','test'}
    assert len(before['test']) == 1 and set(before['test'][0]) == {'input'}
    assert all(set(p) == {'input','output'} for p in before['train'])


def test_legacy_report_public_projection_removes_setting(monkeypatch):
    legacy = load('prototype')
    grids = [[[0,8,0,0,0],[0,8,0,8,0],[0,0,0,0,0],[0,0,0,0,0],[0,8,0,0,0]]] * 4
    monkeypatch.setattr(legacy, '_find_inputs', lambda **kwargs: (grids,[0,1,2,3],'source'))
    class Local:
        def __call__(self,g,a): return legacy.apply_python(g,a)
        def close(self): pass
    monkeypatch.setattr(legacy, '_RacketLabeler', Local)
    public = legacy.build_report(seed=0)['public_episode']
    assert set(public) == {'train','test'}, 'legacy public report discloses selected axis'


def test_retained_bbox_ambiguity_and_constructive_repair(family):
    old = json.loads((HOME/'regression/bbox-before.json').read_text())
    assert all(family.solve(g,'paired_rows') == family.solve(g,'largest_bbox_rows') for g in old['train_inputs'])
    assert family.solve(old['query_input'],'paired_rows') != family.solve(old['query_input'],'largest_bbox_rows')
    repaired = load('adapter').generate(17,{'mode':'paired_rows'},2,4)
    assert any(p['output'] != family.solve(p['input'],'largest_bbox_rows') for p in repaired['train'])


@pytest.mark.parametrize('bad', [[],[[]],[[True]],[[2]],[[0],[0,8]],[[0]*31]])
def test_invalid_grid_types_and_dimensions_are_rejected(family, bad):
    with pytest.raises(ValueError): family.solve(bad,'paired_rows')


def test_rule_programs_parse_as_one_complete_expression():
    from arc_repl.parser import parse_all, Symbol
    for path in (HOME/'rules').glob('*.rkt'):
        forms = parse_all(path.read_text())
        assert len(forms) == 1 and forms[0][0] in (Symbol('rule!'),Symbol('lambda'))
