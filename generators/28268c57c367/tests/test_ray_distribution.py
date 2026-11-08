"""Portable regression tests for the wall-ray sampler and teaching schedule."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '28268c57c367'
ROOT = find_root(__file__)
PATH = next(p for p in (ROOT/'generators'/TASK/'generator.py',
                       ROOT/'puzzle_generators'/'per_puzzle'/TASK/'generator.py') if p.is_file())
SPEC = importlib.util.spec_from_file_location('ray_generator_under_test', PATH)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def oracle(grid):
    """Independent prefix characterization, not source-by-source ray casting."""
    walls = [c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid)]
    assert len(walls) == 1
    wall = walls[0]
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        first = next((c for c in range(wall) if row[c] not in (0, 5)), None)
        if first is not None:
            for c in range(first + 1, wall):
                if row[c] == 0:
                    out[r][c] = row[first]
    return out


def test_rule_hash_is_pinned():
    assert getattr(GEN, 'RULE_HASH', None) == 'b4fa0726be56'


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_population_has_gray_counterexamples(band):
    grids = [GEN.generate(13, i, difficulty=band) for i in range(24)]
    assert any(any(v == 5 and c != next(c for c in range(len(g[0]))
               if all(row[c] == 5 for row in g))
               for row in g for c, v in enumerate(row)) for g in grids)


@pytest.mark.parametrize('overrides', [
    {'n_cells': 1}, {'n_cells': 6}, {'n_distinct_colors': 1},
    {'n_distinct_colors': 6}, {'n_gray': 3}, {'n_gray': 0},
    {'n_right': 3}, {'n_right': 0}, {'wall_col': 5}, {'wall_col': 16},
    {'grid_h': 5}, {'grid_h': 14}, {'grid_w': 7}, {'grid_w': 18},
    {'grid_h': 5, 'grid_w': 7, 'n_cells': 6, 'n_distinct_colors': 6,
     'n_gray': 3, 'n_right': 3, 'wall_col': 5},
])
def test_exact_axes_are_observable(overrides):
    assert callable(getattr(GEN, 'observe_overrides', None))
    for band in ('easy', 'medium', 'hard'):
        for index in (0, 1, 2, 3):
            grid = GEN.generate(31, index, difficulty=band, **overrides)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            assert all(observed[k] == v for k, v in overrides.items())


@pytest.mark.parametrize('overrides', [
    {'n_cells': 2, 'n_distinct_colors': 3}, {'grid_w': 7, 'wall_col': 6},
    {'n_cells': True}, {'grid_h': 7.5}, {'n_gray': '2'},
    {'unknown_axis': 1}, {'n_cells': 0}, {'n_gray': 4},
    {'texture': 'no_wall'}, {'palette_kind': 'warm'},
])
def test_invalid_or_retired_axes_fail_loudly(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(3, 1, **overrides)


def test_canonical_support_and_prefix_oracle():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair['input']) == []
        assert GEN.strict_canonical_like(pair['input']) == []
        assert oracle(pair['input']) == pair['output']


@pytest.mark.parametrize('grid', [[], [[]], [[0], [0, 5]], [[True, 5]],
    [[-1, 5]], [[10, 5]], [[1, 0]], [[5, 5], [5, 5]], None,
])
def test_malformed_grids_are_rejected_without_crashing(grid):
    assert GEN.self_check(grid)


def test_declared_canonical_shortcuts_really_fit_all_pairs():
    shortcuts = getattr(GEN, 'CANONICAL_SHORTCUTS', {})
    assert shortcuts
    for name, rival in shortcuts.items():
        for pair in canonical_pairs(TASK, root=ROOT):
            assert rival(pair['input']) == pair['output'], name


def test_every_cyclic_window_and_rotation_refutes_declared_rivals():
    rivals = getattr(GEN, 'LESSON_COMPETITORS', {})
    assert rivals
    # Exhaustive starts modulo the two-profile schedule, with two subsequent
    # cycles as a guard; each of the four positions is also held out in turn.
    for band in ('easy', 'medium', 'hard'):
        for seed in range(20):
            grids = [GEN.generate(seed, i, difficulty=band) for i in range(7)]
            labels = [oracle(g) for g in grids]
            for start in range(4):
                for query in range(4):
                    demo_indices = [start+j for j in range(4) if j != query]
                    for name, rival in rivals.items():
                        assert any(rival(grids[i]) != labels[i] for i in demo_indices), (
                            band, seed, start, query, name)


def test_generation_is_deterministic_nonmutating_and_lawful():
    for band in ('easy', 'medium', 'hard'):
        for seed in range(12):
            a = GEN.generate(seed, seed+1, difficulty=band)
            b = GEN.generate(seed, seed+1, difficulty=band)
            assert a == b and a is not b
            assert GEN.self_check(a) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                rival(a)
                assert a == b


def test_independent_reference_matches_racket_on_rich_and_edge_inputs():
    from arcpuzzles import Catalog
    grids = [GEN.generate(seed, i, difficulty=band)
             for band in ('easy', 'medium', 'hard') for seed in range(3) for i in (0,1)]
    # Also verify a maximally constrained small legal case using all colors.
    grids.append(GEN.generate(9, 1, grid_h=5, grid_w=7, wall_col=5,
                 n_cells=6, n_distinct_colors=6, n_gray=3, n_right=3))
    result = Catalog(ROOT).apply(TASK, inputs=grids)
    outputs = [item['output'] for item in result['results']]
    assert outputs == [oracle(grid) for grid in grids]


def test_diagonal_probe_cohort_has_real_difficulty_variation():
    assert any(len({str(GEN.generate(seed, seed, difficulty=band))
                    for band in ('easy', 'medium', 'hard')}) > 1
               for seed in range(16))


def test_natural_core_includes_two_source_canonical_family():
    assert any(GEN.strict_canonical_like(g) == [] and GEN.observe_overrides(g)['n_cells'] == 2
               for seed in range(20) for i in range(4)
               for g in [GEN.generate(seed, i, difficulty='medium')])


def test_rich_witness_is_not_one_fixed_local_template():
    distances = set()
    for seed in range(60):
        for i in (0, 1):
            g = GEN.generate(seed, i, difficulty='hard')
            wall = GEN.observe_overrides(g)['wall_col']
            for row in g:
                src = [c for c in range(wall) if row[c] not in (0, 5)]
                if len(src) >= 2 and 5 in row[src[0] + 1:src[1]]:
                    distances.add(src[1] - src[0])
    assert len(distances) >= 3, distances
