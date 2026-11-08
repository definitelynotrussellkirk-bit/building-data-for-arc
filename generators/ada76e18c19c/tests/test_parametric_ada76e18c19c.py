"""Behavioral tests for the separate native row-fill family."""
import copy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


def load():
    path = find_root(Path(__file__)) / 'generators/ada76e18c19c/workspace/parametric/prototype.py'
    assert path.is_file(), 'native row-fill prototype is missing'
    spec = importlib.util.spec_from_file_location('row_fill_native_tests', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_pair_gate_and_immutability():
    p = load()
    g = [[2,0,0,0,2], [3,0,3,0,3], [4,0,0,0,5], [6,0,7,0,6]]
    before = copy.deepcopy(g)
    assert p.solve(g, 'all_colors') == [[2]*5, *before[1:]]
    assert g == before


def test_postfill_count_not_input_count():
    p = load()
    g = [[2,0,0,0,0,0,2], [3,0,3,0,3,0,0], [0,3,0,3,0,3,0]]
    assert p.solve(g, 'filled_majority') == [[2]*7, [0]*7, [0]*7]
    assert p.predict(g, 'exact/pre') == [[0]*7, g[1], g[2]]


def test_global_color_union_ties_and_empty_grid():
    p = load()
    g = [[7,0,7,0,0], [0]*5, [2,0,2,0,0], [0]*5, [7,0,0,0,0]]
    assert p.solve(g, 'filled_majority') == [[7,7,7,0,0], [0]*5, [0]*5, [0]*5, g[4]]
    tie = [[7,0,7], [2,0,2]]
    assert p.solve(tie, 'filled_majority') == [[7]*3, [0]*3]
    assert p.solve([[0,0]], 'filled_majority') == [[0,0]]


@pytest.mark.parametrize('settings', [{}, {'mode':'bad'}, {'mode':True}, {'mode':'all_colors','extra':1}, None])
def test_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        load().generate(0, settings, 3, 4)


@pytest.mark.parametrize('key,value', [('seed',True),('seed',-1),('seed',2**63),('demos',2),('demos',7),('demos',3.0),('queries',0),('queries',5),('queries',True)])
def test_counts_fail_closed(key, value):
    kw = dict(seed=0, settings={'mode':'all_colors'}, demos=3, queries=4)
    kw[key] = value
    with pytest.raises(ValueError):
        load().generate(**kw)


def test_prefix_stability_matched_inputs_and_distinctness():
    p = load()
    a = p.generate(17, {'mode':'all_colors'}, 3, 4)
    b = p.generate(17, {'mode':'filled_majority'}, 6, 4)
    c = p.generate(17, {'mode':'all_colors'}, 6, 1)
    assert a == p.generate(17, {'mode':'all_colors'}, 3, 4)
    assert [x['input'] for x in a['train']] == [x['input'] for x in b['train'][:3]]
    assert [x['input'] for x in a['test']] == [x['input'] for x in b['test']]
    assert a['test'][:1] == c['test']
    all_inputs = [repr(x['input']) for x in b['train']+b['test']]
    assert len(set(all_inputs)) == 10
    assert a['program_solution'] == (Path(p.__file__).with_name('canonical.rkt')).read_text()
    assert a['test'] != b['test']


def test_teaching_and_substantive_boundary():
    p = load()
    for seed in range(8):
        for mode in p.MODES:
            e = p.generate(seed, {'mode':mode}, 3, 4)
            check = p.teaching_check(e)
            assert check['failures'] == [], check
            g = e['test'][3]['input']
            assert len(g) == len(g[0]) == 30
            assert sum(v != 0 for row in g for v in row) >= 90
            assert all(any(row) for row in g)
            assert any(row[0] for row in g) and any(row[-1] for row in g)


def test_public_projection_discards_nested_private_data():
    p = load()
    e = p.generate(0, {'mode':'filled_majority'}, 3, 4)
    v = p.public_turn(e, 0)
    before = public_challenge_bytes(v)
    e['train'][0]['settings'] = {'mode':'secret'}
    e['test'][0]['output'] = [[9]]
    e['program_solution'] = 'private'
    e['seed'] = -4
    assert public_challenge_bytes(p.public_turn(e, 0)) == before
    assert set(v) == {'train','test'}
    assert all(set(pair) == {'input','output'} for pair in v['train'])
    assert v['test'] == [{'input': e['test'][0]['input']}]
    assert public_challenge_id(v) == __import__('hashlib').sha256(before).hexdigest()


@pytest.mark.parametrize('seed', [12,14,16,17,52,60])
def test_color_and_scan_order_regressions(seed):
    p = load()
    e = p.generate(seed, {'mode':'filled_majority'}, 3, 4)
    assert p.teaching_check(e)['failures'] == []


def test_racket_sources_parse_and_execute_literal_order_and_tie_cases():
    # Legacy staged tests may preload the execution-layout namespace. Isolate
    # exact same-checkout imports, then restore it for the remaining tests.
    from arcpuzzles.parametric_worker import _real_evaluator, _local_imports
    root = find_root(Path(__file__))
    with _local_imports(root / 'shared/runtime', root / 'generators/ada76e18c19c/workspace/parametric'):
        from arc_repl.parser import parse_all
        p = load()
        root = find_root(Path(__file__))
        apply, identity, bridge = _real_evaluator(root / 'shared/runtime')
        try:
            assert identity['protected'] is True
            for mode in p.MODES:
                assert len(parse_all(p.program({'mode':mode}))) == 1
            g = [[7,0,7],[2,0,2]]
            assert apply(p.program({'mode':'filled_majority'}), g) == [[7]*3,[0]*3]
            assert apply(p.racket_policy(selector='first'), g) == [[7]*3,[0]*3]
            assert apply(p.racket_policy(selector='last'), g) == [[0]*3,[2]*3]
            assert apply(p.racket_policy(selector='min_color'), g) == [[0]*3,[2]*3]
            assert apply(p.racket_policy(selector='max_color'), g) == [[7]*3,[0]*3]
        finally:
            bridge.close()

def test_sparse_stress_seed_eight_is_repaired_constructively():
    p = load()
    g = p.generate(8, {'mode':'all_colors'}, 3, 4)['test'][3]['input']
    assert sum(v != 0 for row in g for v in row) >= 90


def test_count_rows_is_not_a_substitute_for_counting_filled_cells():
    from collections import Counter
    p=load();e=p.generate(0,{'mode':'filled_majority'},3,4)
    def row_rival(g):
        rows=Counter()
        for row in g:
            vals=[v for v in row if v]
            if len(vals)==2 and vals[0]==vals[1]:rows[vals[0]]+=1
        filled=p.fill(g);colors=list(dict.fromkeys(v for row in filled for v in row if v))
        chosen=max(colors,key=lambda c:rows[c])
        return [[v if v==chosen else 0 for v in row] for row in filled]
    assert any(row_rival(pair['input'])!=pair['output'] for pair in e['train'])
