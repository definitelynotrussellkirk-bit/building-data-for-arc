"""Portable regression tests for task-local reflection and its teaching schedule."""
import copy
import importlib.util
import itertools
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = 'ba29d14676d1'
ROOT = find_root(__file__)
PATHS = (ROOT/'generators'/TASK/'generator.py',
         ROOT/'puzzle_generators'/'per_puzzle'/TASK/'generator.py')
SOURCE = next(p for p in PATHS if p.is_file())
spec = importlib.util.spec_from_file_location('selected_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def oracle(grid):
    """Independent row-run oracle; labels for production still come from Racket."""
    out = []
    for row in grid:
        result, start = list(row), 0
        for stop in range(len(row) + 1):
            if stop == len(row) or row[stop] == 9:
                result[start:stop] = row[start:stop][::-1]
                start = stop + 1
        out.append(result)
    return out


def test_unknown_axes_are_rejected():
    with pytest.raises(ValueError, match='unknown'):
        gen.generate(7, 0, tile_wdith=4)


@pytest.mark.parametrize('name', ['palette_kind', 'palette_size', 'position_bias',
                                  'n_distinct_colors', 'tile_density', 'texture'])
def test_removed_inert_controls_fail_loudly(name):
    with pytest.raises(ValueError, match='unknown'):
        gen.generate(7, 0, **{name: 'default'})


@pytest.mark.parametrize('value', [True, False, 2.5, '2', [], {}])
def test_exact_dimensions_do_not_coerce(value):
    with pytest.raises((ValueError, TypeError)):
        gen.generate(7, 0, tile_rows=value)


def test_documented_joint_boundaries_are_realized():
    grid = gen.generate(7, 0, tile_rows=3, tile_cols=2, tile_h=2, tile_w=5, foreground=8)
    assert len(grid) == 8 and len(grid[0]) == 11
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == dict(tile_rows=3, tile_cols=2, tile_h=2, tile_w=5, foreground=8)


def test_validator_rejects_stray_divider_color():
    grid = gen.generate(7, 0)
    grid[0][0] = 9
    assert gen.self_check(grid), 'stray 9 inside a tile must not be accepted'


@pytest.mark.parametrize('grid', [None, [], [[]], [[0], [0, 1]], [[True]], [[1.5]], [[10]], ['123']])
def test_malformed_grid_returns_reasons_instead_of_crashing(grid):
    assert gen.self_check(grid)


def test_every_labeled_canonical_pair_is_accepted_and_explained():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair['input']) == []
        assert gen.strict_canonical_like(pair['input']) == []
        assert oracle(pair['input']) == pair['output']
    assert gen.CANONICAL_SHORTCUTS
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(copy.deepcopy(p['input'])) == p['output'] for p in pairs)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_all_1536_joint_axis_tuples_in_each_band(band):
    for values in itertools.product(range(1, 4), range(2, 6), range(2, 6), range(2, 6), range(1, 9)):
        axes = dict(zip(('tile_rows', 'tile_cols', 'tile_h', 'tile_w', 'foreground'), values))
        grid = gen.generate(103, 2, difficulty=band, **axes)
        assert gen.self_check(grid) == [], axes
        assert gen.observe_overrides(grid) == axes
        assert oracle(oracle(grid)) == grid
        assert oracle(grid) != grid


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_all_cyclic_six_pair_windows_and_query_rotations(band):
    assert gen.EXAMPLES_NEEDED == 5
    for seed in range(12):
        grids = [gen.generate(seed, i, difficulty=band) for i in range(17)]
        for start in range(12):
            pairs = [{'input': g, 'output': oracle(g)} for g in grids[start:start+6]]
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                refutations = [rival(copy.deepcopy(p['input'])) != p['output'] for p in pairs]
                assert sum(refutations) >= 2, (seed, start, name)
            for query_index in range(6):
                demos = [p for i, p in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == [], (seed, start, query_index)
                for name, rival in gen.LESSON_COMPETITORS.items():
                    if all(rival(copy.deepcopy(p['input'])) == p['output'] for p in demos):
                        assert rival(copy.deepcopy(query['input'])) == query['output'], (seed, start, name)


def test_independent_free_profile_breaks_forced_feature_correlations():
    seen = set()
    for seed in range(600):
        obs = gen.observe_overrides(gen.generate(seed, 2))
        seen.add((obs['tile_rows'] == 1, obs['tile_w'] == 3, obs['foreground'] == 4))
    assert len(seen) == 8, seen


def test_default_draws_deterministic_and_keyed_axis_values_observable():
    from puzzle_generators.base import set_ctx_observer
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        for band in ('easy', 'medium', 'hard'):
            for index in range(18):
                first = gen.generate(1103, index, difficulty=band)
                second = gen.generate(1103, index, difficulty=band)
                assert first == second
                assert gen.self_check(first) == []
                observed = gen.observe_overrides(first)
                assert all(contexts[-1].axis_value(k) == v for k, v in observed.items())
    finally:
        set_ctx_observer(None)


def test_canonical_profile_still_emits_symmetric_individual_tiles():
    symmetric_columns = set()
    for seed in range(100):
        grid = gen.generate(seed, 0)
        for tc in range(3):
            tile = [row[tc*4:tc*4+3] for row in grid]
            if tile == [row[::-1] for row in tile]:
                symmetric_columns.add(tc)
    assert symmetric_columns == {0, 1, 2}, symmetric_columns


def test_witness_profile_refutes_swap_outer_columns_only():
    for seed in range(24):
        for band in ('easy', 'medium', 'hard'):
            grid = gen.generate(seed, 1, difficulty=band)
            out = [row[:] for row in grid]
            for r, row in enumerate(grid):
                if all(v == 9 for v in row):
                    continue
                start = 0
                for stop in range(len(row) + 1):
                    if stop == len(row) or row[stop] == 9:
                        out[r][start], out[r][stop-1] = grid[r][stop-1], grid[r][start]
                        start = stop + 1
            assert out != oracle(grid), (seed, band)


def test_teaching_witnesses_use_compact_two_by_four_tile_scenes():
    # A single extra row and extra column suffice to refute the partial rules;
    # keep the full size range in independent draws and exact overrides.
    areas = []
    for seed in range(100):
        for band in ('easy', 'medium', 'hard'):
            grid = gen.generate(seed, 1, difficulty=band)
            axes = gen.observe_overrides(grid)
            assert axes['tile_rows'] == 2 and axes['tile_cols'] == 4
            assert axes['tile_h'] in (2, 3)
            areas.append(len(grid) * len(grid[0]))
    assert max(areas) <= 161


def test_workspace_probe_is_portable_and_retains_every_declared_rival():
    path = SOURCE.parent / 'workspace' / 'probe.py'
    assert path.is_file(), 'retain a reusable public-reference probe with the task'
    probe_spec = importlib.util.spec_from_file_location('workspace_probe', path)
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    report = probe.make_corpus(gen, pairs)
    assert len(report['cases']) == 64
    assert all(c['expected'] == oracle(c['input']) for c in report['cases'])
    assert set(report['canonical_shortcut_fit']) == set(gen.CANONICAL_SHORTCUTS)
    assert all(report['canonical_shortcut_fit'].values())
    assert set(report['rival_refutations']) == set(gen.LESSON_COMPETITORS)
    assert all(report['rival_refutations'].values())
