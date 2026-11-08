"""Native contracts for public 1818057f plus-motif selection."""
from __future__ import annotations

from pathlib import Path
import copy
import importlib.util
import json
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = next(p for p in HOME.parents if (p / 'shared/data/raw/arc-agi_evaluation_challenges.json').is_file())


def load():
    path = HOME / 'workspace/parametric/adapter.py'
    assert path.is_file(), 'plus adapter has not been implemented'
    name = '_plus_test_' + str(abs(hash(path.resolve())))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def stamp_plus(grid, r, c):
    for rr, cc in ((r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        grid[rr][cc] = 4


def changed_to_eight(before, after):
    return {(r, c) for r in range(len(before)) for c in range(len(before[0]))
            if before[r][c] == 4 and after[r][c] == 8}


def test_every_original_train_and_test_gold():
    a = load()
    challenge = json.loads((ROOT / 'shared/data/raw/arc-agi_evaluation_challenges.json').read_text())['1818057f']
    gold = json.loads((ROOT / 'shared/data/raw/arc-agi_evaluation_solutions.json').read_text())['1818057f']
    pairs = challenge['train'] + [dict(input=p['input'], output=o) for p, o in zip(challenge['test'], gold)]
    for pair in pairs:
        assert a.impl.solve(pair['input'], 'all') == pair['output']


def test_canonical_marks_embedded_pluses_not_only_isolated_exact_shapes():
    a = load()
    g = [[2] * 12 for _ in range(9)]
    stamp_plus(g, 3, 3)
    g[2][2] = 4                 # occupied diagonal: still a valid plus
    g[3][5] = g[4][5] = 4      # connected tail: still mark only the plus cells
    stamp_plus(g, 5, 9)
    g[4][8] = 4                 # another occupied diagonal
    before = copy.deepcopy(g)
    out = a.impl.solve(g, 'all')
    expected = {(3, 3), (2, 3), (4, 3), (3, 2), (3, 4),
                (5, 9), (4, 9), (6, 9), (5, 8), (5, 10)}
    assert changed_to_eight(before, out) == expected
    assert out[2][2] == 4 and out[3][5] == 4 and out[4][8] == 4
    assert g == before


def test_no_cross_and_boundary_fragments_are_unchanged():
    a = load()
    g = [[2] * 8 for _ in range(7)]
    for p in ((0, 0), (0, 1), (1, 0), (3, 3), (2, 3), (4, 3), (3, 2)):
        g[p[0]][p[1]] = 4
    assert a.impl.solve(g, 'all') == g


def test_dominant_component_uses_plus_count_not_area_or_reading_order():
    a = load()
    g = [[2] * 24 for _ in range(14)]
    # Earliest component: one plus.
    stamp_plus(g, 2, 2)
    # Largest-area component: one plus plus a long one-cell-wide tail.
    stamp_plus(g, 3, 15)
    for r in range(4, 12):
        g[r][15] = 4
    for c in range(16, 23):
        g[11][c] = 4
    # Dominant component: two pluses joined by a thin bridge, but smaller area.
    stamp_plus(g, 9, 3)
    stamp_plus(g, 9, 7)
    g[9][5] = 4
    facts = a.impl.analyse(g)
    assert [row['plus_count'] for row in facts['components']] == [1, 1, 2]
    assert facts['dominant_component'] == 2
    out = a.impl.solve(g, 'dominant_component')
    expected = set()
    for center in ((9, 3), (9, 7)):
        r, c = center
        expected |= {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}
    assert changed_to_eight(g, out) == expected


def test_default_program_bytes_and_setting_neutral_inputs():
    a = load()
    assert a.program({'mark_scope': 'all'}) == (HOME / 'reference.rkt').read_text()
    all_ep = a.generate(17, {'mark_scope': 'all'}, 2, 4)
    dom_ep = a.generate(17, {'mark_scope': 'dominant_component'}, 2, 4)
    assert [p['input'] for s in ('train', 'test') for p in all_ep[s]] == [
        p['input'] for s in ('train', 'test') for p in dom_ep[s]
    ]
    assert all(p['output'] != q['output'] for p, q in zip(all_ep['train'], dom_ep['train']))


@pytest.mark.parametrize('demos', [2, 3, 6])
@pytest.mark.parametrize('queries', [1, 2, 4])
def test_counts_are_independent_deterministic_and_prefix_stable(demos, queries):
    a = load()
    ep = a.generate(43, {'mark_scope': 'dominant_component'}, demos, queries)
    assert ep == a.generate(43, {'mark_scope': 'dominant_component'}, demos, queries)
    assert len(ep['train']) == demos and len(ep['test']) == queries
    full = a.generate(43, {'mark_scope': 'dominant_component'}, 2, 4)
    assert ep['test'] == full['test'][:queries]
    assert len({json.dumps(p['input']) for s in ('train', 'test') for p in ep[s]}) == demos + queries


def test_substantive_30x30_query_is_distributed_and_contains_multiple_components():
    a = load()
    ep = a.generate(17, {'mark_scope': 'all'}, 2, 4)
    g = ep['test'][3]['input']
    assert (len(g), len(g[0])) == (30, 30)
    cells = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v == 4]
    assert len(cells) >= 100
    assert min(r for r, _ in cells) == 0 and max(r for r, _ in cells) == 29
    assert min(c for _, c in cells) == 0 and max(c for _, c in cells) == 29
    facts = a.impl.analyse(g)
    assert len(facts['centers']) >= 8 and len(facts['components']) >= 4
    assert max(row['plus_count'] for row in facts['components']) >= 3


def test_public_turns_hide_private_state_and_vary_first_query():
    a = load()
    ep = a.generate(17, {'mark_scope': 'all'}, 3, 4)
    views = a.impl.public_turns(ep, 99)
    assert len(views) == 4
    assert all(set(v) == {'train', 'test'} and len(v['test']) == 1
               and set(v['test'][0]) == {'input'} for v in views)
    poisoned = copy.deepcopy(ep)
    poisoned.update(seed='secret', settings={'hidden': True}, program_solution='PRIVATE')
    for p in poisoned['train']:
        p['hidden'] = True
    for p in poisoned['test']:
        p['output'] = [[9]]
        p['hidden'] = True
    assert views == a.impl.public_turns(poisoned, 99)
    assert views[:1] == a.impl.public_turns(ep, 99, stop_after=1)
    firsts = {json.dumps(a.impl.public_turns(ep, seed, stop_after=1)[0]['test']) for seed in range(32)}
    assert len(firsts) == 4


@pytest.mark.parametrize('seed,demos,queries,settings', [
    (True, 2, 4, {'mark_scope': 'all'}),
    (-1, 2, 4, {'mark_scope': 'all'}),
    (1, 1, 4, {'mark_scope': 'all'}),
    (1, 7, 4, {'mark_scope': 'all'}),
    (1, 2, 0, {'mark_scope': 'all'}),
    (1, 2, 5, {'mark_scope': 'all'}),
    (1, 2, 4, {}),
    (1, 2, 4, {'mark_scope': 'bad'}),
    (1, 2, 4, {'mark_scope': 'all', 'secret': 1}),
])
def test_invalid_native_requests(seed, demos, queries, settings):
    a = load()
    with pytest.raises(ValueError):
        a.generate(seed, settings, demos, queries)


def test_base_generator_is_self_contained_when_relocated(tmp_path):
    import shutil
    path = tmp_path / 'puzzle_generators/per_puzzle' / (HOME.name + '.py')
    path.parent.mkdir(parents=True)
    shutil.copyfile(HOME / 'generator.py', path)
    spec = importlib.util.spec_from_file_location('_relocated_' + HOME.name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    grid = module.generate(29, 3)
    assert module.check_invariants(grid) == []


def test_finite_named_rivals_have_no_harmful_survivor():
    a = load()
    rivals = ('exact_only', 'first_center', 'last_center', 'one_per_component',
              'first_component', 'last_component', 'largest_area', 'smallest_area',
              'topmost_centers', 'paint_components', 'all_fours')
    for seed in range(16):
        for scope in a.impl.MARK_SCOPES:
            ep = a.generate(seed, {'mark_scope': scope}, 2, 4)
            for rival in rivals:
                survives = all(a.impl.rival_solve(p['input'], scope, rival) == p['output']
                               for p in ep['train'])
                assert not survives or all(a.impl.rival_solve(p['input'], scope, rival) == p['output']
                                           for p in ep['test']), (seed, scope, rival)


def test_reusable_audit_runs_without_racket(tmp_path):
    path = HOME / 'workspace/parametric/audit.py'
    assert path.is_file(), 'reusable audit has not been implemented'
    name = '_plus_audit_test_' + str(abs(hash(path.resolve())))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    report = module.run_audit(tmp_path / 'audit', seeds=[0, 1], racket_seeds=[])
    assert report['status'] == 'passed'
    assert report['episodes'] == 12
    assert report['harmful_survivors'] == []
