"""Portable regressions for the palette-rank input contract."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '627260bf308f'
ROOT = find_root(__file__)
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
if not SOURCE.is_file():
    SOURCE = ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('palette_rank_review', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid, diagonals=False):
    remaining = {(r, c) for r in range(1, len(grid)) for c, v in enumerate(grid[r]) if v == 8}
    found = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, group = [start], {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)) + (((-1,-1),(-1,1),(1,-1),(1,1)) if diagonals else ()):
                q = r + dr, c + dc
                if q in remaining:
                    remaining.remove(q); group.add(q); stack.append(q)
        found.append(group)
    return found


def independent_expected(grid):
    palette = [v for v in grid[0] if v]
    out = [row[:] for row in grid]
    for color, group in zip(palette, sorted(components(grid), key=lambda x: (len(x), min(x)))):
        for r, c in group:
            out[r][c] = color
    return out


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('shape', [(8,10), (9,11), (24,24)])
def test_global_dimensions_and_exact_count(band, shape):
    g = gen.generate(37, 0, difficulty=band, grid_h=shape[0], grid_w=shape[1], n_components=5)
    assert (len(g), len(g[0])) == shape
    assert len(components(g)) == 5
    assert len({len(c) for c in components(g)}) == 5
    assert len([v for v in g[0] if v]) == 5
    assert gen.self_check(g) == []


@pytest.mark.parametrize('axis', ['typo_axis', 'palette_size', 'palette_kind', 'n_distinct_colors', 'density', 'texture', 'position_bias'])
def test_removed_or_unknown_axes_fail_loudly(axis):
    with pytest.raises(ValueError):
        gen.generate(37, 0, **{axis: 3})


@pytest.mark.parametrize('value', [True, 8.5, '8'])
def test_integer_axes_are_not_coerced(value):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(37, 0, grid_h=value)


def test_self_check_rejects_count_mismatch():
    pair = canonical_pairs(TASK, root=ROOT)[0]
    g = [list(row) for row in pair['input']]
    for r, c in min(components(g), key=len):
        g[r][c] = 0
    assert gen.self_check(g)


def test_self_check_rejects_tied_sizes():
    g = [[2,0,4,0,0], [0]*5, [8,0,0,0,8], [0]*5]
    assert gen.self_check(g)


@pytest.mark.parametrize('g', [None, [], [[]], [[1,2],[8]], [[2,0],[0,True]], [[8,0],[0,8]]])
def test_malformed_grid_is_diagnostic_not_exception(g):
    assert gen.self_check(g)


def test_every_canonical_pair_is_lawful():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair['input']) == []
        assert independent_expected(pair['input']) == pair['output']


def test_explicit_semantic_contract_exists():
    assert getattr(gen, 'RULE_HASH', None) == '088353dcd64f'
    assert callable(getattr(gen, 'observe_overrides', None))
    assert len(getattr(gen, 'CANONICAL_SHORTCUTS', {})) >= 7
    assert len(getattr(gen, 'SEMANTIC_WITNESSES', {})) >= 7


def test_all_default_even_draws_refute_each_canonical_shortcut():
    assert getattr(gen, 'CANONICAL_SHORTCUTS', {})
    for band in ('easy', 'medium', 'hard'):
        for seed in range(20):
            for index in (0, 2, 10):
                g = gen.generate(seed, index, difficulty=band)
                expected = independent_expected(g)
                for name, rival in gen.CANONICAL_SHORTCUTS.items():
                    assert rival(g) != expected, (band, seed, index, name)


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    pairs = canonical_pairs(TASK, root=ROOT)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair['input']) == pair['output'] for pair in pairs), name


def test_every_four_pair_window_is_safe_under_all_query_rotations():
    for band in ('easy', 'medium', 'hard'):
        for seed in range(8):
            grids = [gen.generate(seed, index, difficulty=band) for index in range(11)]
            labels = [independent_expected(g) for g in grids]
            for rival in gen.LESSON_COMPETITORS.values():
                predictions = [rival(g) for g in grids]
                for start in range(8):
                    for query in range(start, start+4):
                        demos = [i for i in range(start, start+4) if i != query]
                        assert not (all(predictions[i] == labels[i] for i in demos) and predictions[query] != labels[query])


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('index', [0,1])
@pytest.mark.parametrize('n', [2,3,4,5])
@pytest.mark.parametrize('order', ['sorted','unsorted'])
def test_controls_independently_observable_and_reproducible(band, index, n, order):
    args = dict(grid_h=8, grid_w=10, n_components=n, palette_order=order)
    first = gen.generate(765, index, difficulty=band, **args)
    assert first == gen.generate(765, index, difficulty=band, **args)
    assert gen.observe_overrides(first) == args
    assert len(components(first)) == n
    assert gen.self_check(first) == []


def test_constructive_fallback_keeps_all_five_components():
    class AlwaysLower:
        def randint(self, lo, hi):
            return lo
    from puzzle_generators.base import gen_ctx
    for seed in range(40):
        rng = gen_ctx(seed=seed, sample_index=0).draw_rng('fallback_test')
        for plan in (gen._witness_plan(rng, 5), gen._broad_plan(rng, 8, 10, 5)):
            grid = gen._layout(AlwaysLower(), 8, 10, plan)
            assert len(components(grid)) == 5
            assert len({len(group) for group in components(grid)}) == 5


def test_probe_independent_oracle_matches_canonical_and_dynamic_contract():
    task_source = SOURCE.parent
    probe_path = task_source / 'workspace' / 'coverage_probe.py'
    probe_spec = importlib.util.spec_from_file_location('palette_rank_coverage_probe', probe_path)
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    for pair in canonical_pairs(TASK, root=ROOT):
        assert probe.expected(pair['input']) == pair['output']
    report = probe.analyze(gen, gen, ROOT, seeds=1)
    assert report['status'] == 'no_findings'
    assert report['counts']['lessons'] == 24
    assert report['counts']['rotation_checks'] == 96
    assert len(report['canonical_fit']) == len(gen.CANONICAL_SHORTCUTS) + len(gen.LESSON_COMPETITORS)
