"""Regression tests: prevent fixed row parity, swallowed overrides and weak lessons."""
from copy import deepcopy
import hashlib
import itertools
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / 'workspace'))
from review_probe import (canonical, canonical_pairs, load_generator, reference_python,
                          rows_info, shifted_canonical)

gen = load_generator(os.environ.get('GENERATOR_UNDER_TEST'))


@pytest.mark.parametrize('pair', canonical_pairs(), ids=['train0', 'train1', 'test0'])
def test_canonical_acceptance_and_independent_test_oracle(pair):
    assert gen.self_check(pair['input']) == []
    assert reference_python(pair['input']) == pair['output']


def test_pins_unchanged_racket_rule():
    assert getattr(gen, 'RULE_HASH', None) == hashlib.sha256(canonical()['program_solution'].encode()).hexdigest()[:12]


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_generated_rows_cover_positive_even_indices(band):
    seen = set()
    for i in range(60):
        g = gen.generate('row-position-regression', i, difficulty=band)
        assert gen.self_check(g) == []
        seen.update(x['row'] for x in rows_info(g))
    assert {0, 1, 2, 3, 4} <= seen


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_every_exact_axis_at_every_corner(band):
    for h, w, n, length in itertools.product([5, 7], [7, 12], [1, 3], [3, 6]):
        opts = dict(grid_h=h, grid_w=w, n_active_rows=n, run_len=length)
        g = gen.generate(17, 4, difficulty=band, **opts)
        assert gen.self_check(g) == []
        assert len(g) == h and len(g[0]) == w
        info = rows_info(g)
        assert len(info) == n and {v['length'] for v in info} == {length}
        assert all(b['row'] - a['row'] >= 2 for a, b in zip(info, info[1:]))
        assert hasattr(gen, 'observe_overrides'), 'exact axes need a pixel-derived observer'
        assert gen.observe_overrides(g) == opts


@pytest.mark.parametrize('key,value', [
    ('typo', 1), ('grid_h', 4), ('grid_h', 8), ('grid_w', 6), ('grid_w', 13),
    ('n_active_rows', 0), ('n_active_rows', 4), ('run_len', 2), ('run_len', 7),
    ('grid_h', True), ('grid_w', '8'), ('run_len', 3.5),
    ('palette_kind', 'warm'), ('anchor_corner', True), ('asymmetry_force', True),
    ('palette_size', 4), ('n_distinct_colors', 4), ('position_bias', 'random'),
    ('texture', 'no_marks'),
])
def test_invalid_or_retired_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(17, 0, **{key: value})


@pytest.mark.parametrize('bad', [
    [], [[]], [[0]*8, [0]], None, [[True]*8]*5, [[-1]*8]*5,
    [[10]*8]*5, [[1.5]*8]*5, [['2']*8]*5, [[0]*8]*5,
])
def test_validator_reports_malformed_inputs_without_crashing(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize('mutation', ['gap', 'tie', 'three_colors', 'all_major', 'adjacent'])
def test_validator_rejects_semantic_domain_violations(mutation):
    g = deepcopy(canonical_pairs()[0]['input'])
    if mutation == 'gap':
        g[1] = [2, 0, 4, 2, 2, 0, 0, 0]
    elif mutation == 'tie':
        g[1] = [2, 4, 2, 4, 0, 0, 0, 0]
    elif mutation == 'three_colors':
        g[1][0] = 9
    elif mutation == 'all_major':
        g[1][2] = 2
    elif mutation == 'adjacent':
        g[2], g[3] = g[3], g[2]
    assert gen.self_check(g)


def test_shifted_canonical_is_in_documented_domain():
    assert gen.self_check(shifted_canonical()) == []


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    shortcuts = getattr(gen, 'CANONICAL_SHORTCUTS', {})
    assert shortcuts, 'declare executable, canonical-perfect shortcuts'
    for name, rival in shortcuts.items():
        for pair in canonical_pairs():
            inp = deepcopy(pair['input'])
            assert rival(inp) == pair['output'], name
            assert inp == pair['input'], name
    assert set(shortcuts) <= set(gen.LESSON_COMPETITORS)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_every_cyclic_three_demo_lesson_refutes_declared_rivals(band):
    rivals = getattr(gen, 'LESSON_COMPETITORS', {})
    assert rivals, 'test the actual declared rivals, not a copied name list'
    for seed in range(10):
        for start in range(3):
            grids = [gen.generate(seed, start+i, difficulty=band) for i in range(4)]
            demos = [{'input': g, 'output': reference_python(g)} for g in grids[:3]]
            for name, rival in rivals.items():
                assert any(rival(deepcopy(p['input'])) != p['output'] for p in demos), (seed, start, name)
            assert gen.lesson_identifiable(demos, grids[-1]) == []


def test_witnesses_have_true_per_grid_rival_disagreements():
    witnesses = getattr(gen, 'SEMANTIC_WITNESSES', {})
    assert witnesses
    hits = {name: 0 for name in witnesses}
    for i in range(90):
        g = gen.generate(20261002, i)
        expected = reference_python(g)
        for name, witness in witnesses.items():
            if witness(g):
                hits[name] += 1
                assert any(gen.SEMANTIC_RIVALS[r](deepcopy(g)) != expected
                           for r in gen.WITNESS_RIVALS[name]), name
    assert all(hits.values()), hits


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_determinism_full_color_support_and_nonidentity(band):
    colors, sides, counts, lengths = set(), set(), set(), set()
    for i in range(90):
        g = gen.generate(7331, i, difficulty=band)
        assert g == gen.generate(7331, i, difficulty=band)
        assert gen.self_check(g) == []
        assert reference_python(g) != g
        for item in rows_info(g):
            colors.update((item['major'], item['odd']))
            lengths.add(item['length'])
            sides.add('first' if item['odd_col'] == item['start'] else
                      'last' if item['odd_col'] == item['end'] else 'interior')
        counts.add(len(rows_info(g)))
    assert colors == set(range(1, 10))
    assert sides == {'first', 'last', 'interior'}
    assert counts == {1, 2, 3} and lengths == {3, 4, 5, 6}
