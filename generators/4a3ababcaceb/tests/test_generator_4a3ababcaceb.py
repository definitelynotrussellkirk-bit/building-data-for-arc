"""Run explicitly: python3 -m pytest -q generators/4a3ababcaceb/tests."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('reviewed_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def tiles(grid):
    return [[grid[r+i][c+j] for i in range(3) for j in range(3)]
            for r in range(0, len(grid), 4) for c in range(0, len(grid[0]), 4)]


def canonical_pairs():
    for line in (REPO / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['task_id'] == gen.TASK_ID:
            test = row['test'] if isinstance(row['test'], list) else [row['test']]
            return row, row['train'] + test
    raise AssertionError('missing canonical row')


def test_src_size_override_is_effective():
    for size in (3, 8, 9):
        grid = gen.generate(7, 0, src_size=size)
        assert max(t.count(2) for t in tiles(grid)) == size


def test_original_one_row_layout_is_supported():
    grid = gen.generate(19, 3, tile_rows=1, tile_cols=3)
    assert (len(grid), len(grid[0])) == (3, 11)


def test_unknown_controls_are_not_silently_ignored():
    with pytest.raises(TypeError, match='unknown override'):
        gen.generate(1, 0, imaginary_axis=7)


@pytest.mark.parametrize('grid', [
    [[2, 9, 3], [0]],
    [[2, 0, 0, 9, 0, 3, 0, 9, 0, 0, 0]],
    [[2, 0, 0, 9, 0, 0, 0, 9, 2, 0, 0],
     [0, 0, 0, 9, 0, 3, 0, 9, 0, 0, 0],
     [0, 0, 0, 9, 0, 0, 0, 9, 0, 0, 0]],
])
def test_bad_structure_and_tied_sources_are_rejected(grid):
    assert gen.self_check(grid)


def test_all_canonical_pairs_and_rule_pin():
    row, pairs = canonical_pairs()
    expected = hashlib.sha256(' '.join(row['program_solution'].split()).encode()).hexdigest()[:12]
    assert getattr(gen, 'RULE_HASH', None) == expected
    assert callable(getattr(gen, 'rule_mirror', None))
    for pair in pairs:
        assert gen.self_check(pair['input']) == []
        assert gen.rule_mirror(pair['input']) == pair['output']


def test_every_three_demo_window_refutes_named_rivals():
    assert callable(getattr(gen, 'rule_mirror', None))
    assert getattr(gen, 'EXAMPLES_NEEDED', None) == 3
    for band, seed, start in itertools.product((None, 'easy', 'medium', 'hard'), range(6), range(6)):
        grids = [gen.generate(seed, start + i, difficulty=band) for i in range(4)]
        pairs = [{'input': g, 'output': gen.rule_mirror(g)} for g in grids]
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(p['input']) != p['output'] for p in pairs[:3]), name


def test_full_boundary_matrix_and_observed_axes():
    assert callable(getattr(gen, 'observe_overrides', None))
    for band, rows, cols, size, marker in itertools.product(
            (None, 'easy', 'medium', 'hard'), (1, 5), (3, 6), (2, 9), (0, 8)):
        overrides = dict(tile_rows=rows, tile_cols=cols, src_size=size, marker_offset=marker)
        grid = gen.generate(41, 2, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_replay_is_fresh_and_global_rng_pure():
    before = random.getstate()
    first = gen.generate(91, 17)
    second = gen.generate(91, 17)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == before
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


@pytest.mark.parametrize('axis,value', [
    ('src_size', 0), ('src_size', 10), ('src_size', True), ('src_size', 3.2),
    ('tile_rows', 0), ('tile_cols', 7), ('marker_offset', 9),
])
def test_invalid_values_are_not_coerced(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(2, 1, **{axis: value})


def test_mutation_fixtures_reject_without_crashing_or_mutating():
    assert callable(getattr(gen, 'mutation_fixtures', None))
    for name, grid in gen.mutation_fixtures():
        snapshot = copy.deepcopy(grid)
        assert gen.self_check(grid), name
        assert grid == snapshot


def test_validator_checks_interior_palette_and_complete_dividers():
    grid = gen.generate(91, 5, tile_rows=2, tile_cols=3)
    broken = copy.deepcopy(grid)
    broken[0][3] = 0
    assert gen.self_check(broken)
    for value in (9, 11, True, 1.5):
        broken = copy.deepcopy(grid)
        broken[0][0] = value
        assert gen.self_check(broken)


def test_dense_counterexamples_do_not_fill_every_unrelated_tile():
    for seed in range(60):
        grid = gen.generate(seed, 1-seed % 3 if seed % 3 <= 1 else 2,
                            tile_rows=3, tile_cols=4)
        # One dense decoy and a cluttered target are sufficient. A full source
        # at the size-9 boundary may be a third; unrelated tiles stay sparse.
        assert sum(all(v != 0 for v in tile) for tile in tiles(grid)) <= 3


def test_source_density_purity_and_last_position_shortcuts_are_explicitly_tested():
    assert {'least_occupied_red_tile', 'purest_red_tile', 'last_red_tile'} <= set(gen.LESSON_COMPETITORS)
