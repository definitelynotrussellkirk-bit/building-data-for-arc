"""Task-local regression tests; execute in a staged ARCpuzzles runtime.

These tests deliberately fail on v4.0: its mixed template never puts a
corner-pair stop below the square, and all blocker depths are constant.
"""
from __future__ import annotations

import importlib
from collections import defaultdict

import pytest
from reviewer_support import canonical_pairs as _canonical_pairs, find_root

LIB_ROOT = find_root(__file__)

def canonical_pairs(task_id: str):
    return _canonical_pairs(task_id, root=LIB_ROOT, labeled_only=True)

gen = importlib.import_module('puzzle_generators.per_puzzle.fbf36c193fa6.generator')


def upward_pair_only(grid):
    """Independent red scan; keep the ordinary yellow rule unchanged."""
    output = gen.rule_mirror(grid)
    cyan = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    top, left = min(r for r, _ in cyan), min(c for _, c in cyan)
    bottom, right = max(r for r, _ in cyan), max(c for _, c in cyan)
    for cr, cc, dr, dc in ((top,left,-1,-1), (top,right,-1,1),
                            (bottom,left,1,-1), (bottom,right,1,1)):
        r, c = cr+dr, cc+dc
        while 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            if grid[r][c] == 5:
                break
            if dr < 0 and grid[r][c-dc] == grid[r-dr][c] == 5:
                break
            if output[r][c] != 4:
                output[r][c] = 2
            r, c = r+dr, c+dc
    return output


def test_directional_rival_really_fits_all_public_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    assert all(upward_pair_only(p['input']) == p['output'] for p in pairs)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('seed', [1700, 1701])
def test_every_three_demo_window_refutes_directional_shortcut(band, seed):
    grids = [gen.generate(seed, i, difficulty=band) for i in range(18)]
    refutes = [upward_pair_only(g) != gen.rule_mirror(g) for g in grids]
    for start in range(16):
        assert any(refutes[start:start+3]), (band, seed, start, refutes)


def test_all_corners_and_nonconstant_distances_are_reached():
    corners, lengths = defaultdict(set), defaultdict(set)
    for seed in (900, 901):
        for i in range(90):
            grid = gen.generate(seed, i, difficulty='hard')
            features = gen._features_for_witness(grid)
            for family in ('red', 'yellow'):
                for corner, (cells, why) in enumerate(features[family]):
                    if why != 'edge':
                        corners[family, why].add(corner)
                        lengths[family, why].add(len(cells))
    for branch in [('red','direct_gray'), ('red','corner_pair'),
                   ('yellow','start_gray'), ('yellow','intermediate_gray'),
                   ('yellow','diagonal_gray')]:
        assert corners[branch] == set(range(4)), (branch, corners[branch])
        if branch[1] != 'start_gray':
            assert len(lengths[branch]) >= 3, (branch, lengths[branch])


def test_canonical_shortcuts_are_actual_canonical_fits():
    pairs = canonical_pairs(gen.TASK_ID)
    assert gen.CANONICAL_SHORTCUTS, 'declare at least the verified directional rival'
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p['input']) == p['output'] for p in pairs), name


def test_lesson_hook_rejects_open_only_directionally_ambiguous_lesson():
    grids = [gen.generate(193, i, barrier_profile='open') for i in range(4)]
    demos = [{'input': g, 'output': gen.rule_mirror(g)} for g in grids[:3]]
    query = {'input': grids[3], 'output': gen.rule_mirror(grids[3])}
    assert gen.lesson_identifiable(demos, query)


def test_declared_competitors_are_all_checked_on_sliding_lessons():
    for seed in (6700, 6701):
        grids = [gen.generate(seed, i, difficulty='medium') for i in range(18)]
        for start in range(15):
            demos = [{'input': g, 'output': gen.rule_mirror(g)} for g in grids[start:start+3]]
            query_grid = grids[start+3]
            query = {'input': query_grid, 'output': gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(p['input']) != p['output'] for p in demos), (name, start)


def test_each_semantic_witness_has_a_real_rival_disagreement():
    for name in gen.SEMANTIC_WITNESSES:
        assert gen.WITNESS_RIVALS.get(name), name
    for seed in (4320, 4321):
        for i in range(6):
            grid = gen.generate(seed, i)
            answer = gen.rule_mirror(grid)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    assert any(gen.SEMANTIC_RIVALS[rival](grid) != answer
                               for rival in gen.WITNESS_RIVALS[name]), name
