"""Native cross family: real behavior and literal independent expectations."""
import importlib.util
import json
from pathlib import Path
import pytest
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK = '95524d104174'
BASE = find_root(__file__) / 'generators' / TASK / 'workspace' / 'parametric'


def load(name):
    path = BASE / (name + '.py')
    assert path.is_file(), f'{name} must be implemented'
    spec = importlib.util.spec_from_file_location('test_cross_' + name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_relay_selects_one_post_ring_fragment_not_original_whole_line():
    m = load('native')
    g = [[0,0,1,0,0,0,0,0,0] for _ in range(7)]
    g[3] = [3]*9
    want = [
        [0,0,1,0,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0],
        [0,4,4,4,0,0,0,0,0],
        [3,4,3,4,8,8,8,8,8],
        [0,4,4,4,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0],
        [0,0,1,0,0,0,0,0,0],
    ]
    assert m.predict(g, 'largest_fragment') == want
    assert m.predict(g, 'pre_ring') != want
    assert m.fragment_facts(g)['size'] == 5
    assert m.fragment_facts(g)['cells'] == [[3,4],[3,5],[3,6],[3,7],[3,8]]


def test_default_and_retained_frame_programs_exact():
    m, old = load('native'), load('prototype')
    for c in (4,2,8):
        assert m.program({'rule': f'frame_{c}'}) == old.instantiate_rule(c)
    assert m.program({'rule': 'frame_4'}) == (BASE/'canonical.rkt').read_text()


@pytest.mark.parametrize('kw', [
    {'seed': True}, {'seed': -1}, {'seed': 2**63}, {'demos': 1}, {'demos': 7},
    {'demos': 3.0}, {'queries': 0}, {'queries': 5}, {'queries': True},
    {'settings': {'rule': 'no'}}, {'settings': {'rule': 'frame_4','other': 1}},
    {'settings': {'rule': 4}},
])
def test_invalid_requests_fail_closed(kw):
    m = load('adapter')
    args = dict(seed=0, settings={'rule':'frame_4'}, demos=2, queries=4)
    args.update(kw)
    with pytest.raises(ValueError):
        m.generate(**args)


def test_all_counts_distinct_prefix_queries_setting_neutral():
    m = load('adapter')
    for seed in (0,17,91):
        reference = m.generate(seed, {'rule':'frame_4'}, 6, 4)
        for mode in ('frame_4','frame_2','frame_8','largest_fragment'):
            for n in range(2,7):
                e = m.generate(seed, {'rule':mode}, n, 4)
                assert len(e['train']) == n and len(e['test']) == 4
                inputs = [p['input'] for p in e['train']+e['test']]
                assert len(set(map(json.dumps, inputs))) == len(inputs)
                assert inputs == [p['input'] for p in reference['train'][:n]+reference['test']]
                assert m.generate(seed, {'rule':mode}, n, 1)['test'] == e['test'][:1]
                assert len(e['test'][3]['input']) == len(e['test'][3]['input'][0]) == 30
                assert sum(v!=0 for row in e['test'][3]['input'] for v in row) == 59


def test_declared_finite_rivals_refuted_at_minimum_demos():
    m = load('native')
    for seed in range(12):
        for mode in m.MODES:
            e = m.generate(seed, {'rule':mode}, 2, 4)
            assert m.teaching_check(e)['ambiguous'] == []


def test_legacy_writer_ids_depend_only_on_public_bytes(tmp_path):
    m = load('prototype')
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge() as b:
        report = m.materialize(tmp_path/'legacy', seed=0, bridge=b)
    for row in report['episodes']:
        path = tmp_path/'legacy'/row['public_path']
        value = json.loads(path.read_bytes())
        assert path.name == public_challenge_id(value) + '.json'
        assert path.read_bytes() == public_challenge_bytes(value)


def test_protected_racket_relay_and_wrong_order_match_independent_claims():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    m = load('native')
    with RacketBridge() as b:
        assert b.runtime_identity['protected'] is True
        for mode in m.MODES:
            e = m.generate(17, {'rule':mode}, 2, 4)
            for p in e['train']+e['test']:
                datum = "'("+' '.join('('+' '.join(map(str,row))+')' for row in p['input'])+')'
                assert b.eval_text(f'({wrap_rule(e["program_solution"])} {datum})') == p['output']
        g = m.generate(17, {'rule':'largest_fragment'},2,4)['train'][0]['input']
        datum = "'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
        assert b.eval_text(f'({wrap_rule(m.counterfactual_program())} {datum})') == m.predict(g,'pre_ring')
        assert m.predict(g,'pre_ring') != m.predict(g,'largest_fragment')


def test_legacy_public_projection_drops_private_demo_metadata():
    m = load('prototype')
    e = {'pairs':[{'input':[[1]],'output':[[2]],'settings':{'secret':1},'program':'secret'} for _ in range(4)]}
    pub = m.public_challenge(e)
    assert all(set(p)=={'input','output'} for p in pub['train'])
    assert pub['test'] == [{'input':[[1]]}]


def test_tie_precedence_is_taught_not_just_unique_area():
    m = load('native')
    for seed in range(16):
        e = m.generate(seed, {'rule':'largest_fragment'},2,4)
        for rival in ('column_major_tie','min_color_tie','max_color_tie'):
            fits = all(m.predict(p['input'],rival) == p['output'] for p in e['train'])
            differs = any(m.predict(p['input'],rival) != p['output'] for p in e['test'])
            assert not (fits and differs), (seed,rival)


def test_bounded_audit_counts_unique_inputs_and_keeps_regression():
    audit = load('audit')
    report = audit.run(seeds=2, racket_seeds=())
    assert report['episodes'] == 40
    assert report['labeled_pair_checks'] == 320
    assert report['distinct_inputs'] == 20
    assert report['failures'] == []
    assert report['regression']['old_rival_fits_demos'] is True
    assert report['regression']['old_rival_differs_query'] is True
    assert report['regression']['new_refuting_demos'] == [0,1]
    assert report['protected_racket_evaluations'] == 0
