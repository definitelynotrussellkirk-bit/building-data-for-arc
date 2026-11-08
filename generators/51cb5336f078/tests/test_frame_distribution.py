"""Task-local regressions; labels remain the responsibility of canonical Racket."""
import hashlib
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = '51cb5336f078'
ROOT = find_root(__file__)
SOURCE = (ROOT / 'generators' / TASK / 'generator.py' if (ROOT / 'generators').is_dir()
          else ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py')
SPEC = importlib.util.spec_from_file_location('frame_generator_under_test', SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def geometry(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    edge = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
            if r in (top, bottom) or c in (left, right)}
    return cells, edge


def oracle(grid):
    cells, edge = geometry(grid)
    color = grid[next(iter(cells))[0]][next(iter(cells))[1]]
    return [[color if (r, c) in edge else 0 for c in range(len(grid[0]))]
            for r in range(len(grid))]


def erased(grid):
    cells, edge = geometry(grid)
    return bool(cells - edge)


def test_canonical_acceptance_and_python_spec():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair['input']) == []
        assert oracle(pair['input']) == pair['output']


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('size', [3, 4, 5, 7, 8, 12, 18])
def test_exact_size_and_minimum_canvas(band, size):
    grid = gen.generate(17, 0, difficulty=band, grid_h=5, grid_w=5, motif_size=size)
    assert (len(grid), len(grid[0])) == (5, 5)
    assert len(geometry(grid)[0]) == size
    assert gen.self_check(grid) == []
    assert grid != oracle(grid)


@pytest.mark.parametrize('color', range(1, 10))
def test_exact_color(color):
    grid = gen.generate(7, 1, color=color)
    assert {v for row in grid for v in row} == {0, color}
    assert gen.observe_overrides(grid)['color'] == color


@pytest.mark.parametrize('overrides', [
    {'typo_axis': 1}, {'grid_h': 4}, {'grid_w': 13}, {'motif_size': 2},
    {'motif_size': 19}, {'color': 0}, {'grid_h': True}, {'color': '3'},
    {'motif_size': 5.5}, {'texture': 'no_motif'},
])
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize('grid', [
    [], [[]], [[0]], [[0] * 5 for _ in range(5)], [[0, 1], [0]],
    [[0, 1], None], [[0, True], [True, True]], [[0, -1], [-1, -1]],
    [[0, 'x'], ['x', 'x']], [[0, 2], [2, 3]],
])
def test_validator_returns_reasons_without_crashing(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_lesson_windows_and_all_query_rotations(band):
    # 20 seeds x 8 cyclic starts x 4 rotations, not independent lessons.
    for seed in range(20):
        samples = [gen.generate(seed, i, difficulty=band) for i in range(12)]
        for grid in samples:
            assert gen.self_check(grid) == []
            assert grid != oracle(grid)
        for start in range(8):
            block = samples[start:start + 4]
            assert sum(map(erased, block)) >= 2
            for query_index in range(4):
                demos = [g for i, g in enumerate(block) if i != query_index]
                assert any(map(erased, demos))
                for name, rival in gen.LESSON_COMPETITORS.items():
                    # A candidate agreeing everywhere is not a query ambiguity.
                    if all(rival(g) == oracle(g) for g in demos):
                        assert rival(block[query_index]) == oracle(block[query_index]), name


def test_every_exact_axis_is_observable():
    overrides = dict(grid_h=12, grid_w=11, motif_size=18, color=9)
    g = gen.generate(31, 7, difficulty='easy', **overrides)
    assert gen.observe_overrides(g) == overrides
    assert gen.generate(31, 7, difficulty='easy', **overrides) == g


def test_canonical_shortcuts_really_fit_every_canonical_pair():
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in canonical_pairs(TASK, root=ROOT)), name
