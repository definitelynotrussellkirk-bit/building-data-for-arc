"""Focused regression for the reviewed first/last-blocker collision merge."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'workspace'))
from reference_probe import load_generator, rule_output, teaching_errors

gen = load_generator()


def test_first_and_last_blockers_are_observably_different():
    grid = [[0] * 9 for _ in range(5)]
    grid[2] = [0, 2, 0, 8, 0, 8, 0, 0, 0]
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid)[2] == [0, 2, 2, 8, 0, 8, 0, 0, 0]
    assert gen._last_blocker(grid)[2] == [0, 2, 2, 8, 2, 8, 0, 0, 0]
    assert gen._has_first_vs_last_blocker(grid)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_default_four_pair_windows_keep_witness_after_each_query_holdout(band):
    for seed in [0, 11, 861]:
        grids = [gen.generate(seed, i, difficulty=band) for i in range(24)]
        for grid in grids:
            assert gen.self_check(grid) == []
            assert teaching_errors(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
        for start in range(21):
            pairs = grids[start:start + 4]
            for query in range(4):
                assert any(gen._last_blocker(g) != rule_output(g)
                           for i, g in enumerate(pairs) if i != query)


@pytest.mark.parametrize('post', [0, 1, 2, 3])
def test_exact_zero_and_positive_post_blocker_counts_are_retained(post):
    for band in [None, 'easy', 'medium', 'hard']:
        for i in [0, 1, 2, 3]:
            grid = gen.generate(0, i, difficulty=band, grid_h=5, grid_w=7,
                                rays=5, post_blocker_cells=post)
            assert gen.observe_overrides(grid) == {
                'grid_h': 5, 'grid_w': 7, 'rays': 5, 'post_blocker_cells': post}
            assert gen.self_check(grid) == []
            assert gen._has_first_vs_last_blocker(grid) is (post > 0)
