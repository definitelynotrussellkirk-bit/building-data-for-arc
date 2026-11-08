"""Focused support regressions for repeated and unsorted bar heights.

These check the explicit pattern overrides on general (even-index) draws.
The production teaching schedule has separate lesson tests; it need not retain
the old uniform mixture of height families.
"""
from __future__ import annotations

from collections import Counter
from itertools import combinations, permutations

import pytest

from reviewer_support import find_root, load_selected_generator


generator, _source, _sha = load_selected_generator(
    "44e865b6a43e", root=find_root(__file__)
)


def heights_of(grid):
    return [sum(row[col] != 7 for row in grid)
            for col in range(1, len(grid[0]), 2)]


@pytest.mark.parametrize("n_bars", [3, 4, 5])
def test_repeat_override_varies_duplicate_positions_ranks_and_multiplicities(n_bars):
    seen_pairs, seen_ranks, seen_multiplicities = set(), set(), set()
    for index in range(768):
        grid = generator.generate(
            81000 + index, 2 * index, difficulty="medium",
            grid_h=10, n_bars=n_bars, height_pattern="repeat",
        )
        heights = heights_of(grid)
        assert len(grid) == 10 and len(grid[0]) == 2 * n_bars + 1
        assert all(1 <= height < 10 for height in heights)
        assert 1 < len(set(heights)) < n_bars
        levels = sorted(set(heights))
        counts = Counter(heights)
        seen_multiplicities.add(tuple(sorted(counts.values(), reverse=True)))
        for height, count in counts.items():
            if count < 2:
                continue
            positions = [i for i, value in enumerate(heights) if value == height]
            seen_pairs.update(combinations(positions, 2))
            seen_ranks.add(levels.index(height))

    assert seen_pairs == set(combinations(range(n_bars), 2))
    assert seen_ranks == set(range(n_bars - 1))
    if n_bars >= 4:
        assert any(pattern[0] >= 3 for pattern in seen_multiplicities)
        assert any(sum(count >= 2 for count in pattern) >= 2
                   for pattern in seen_multiplicities)


@pytest.mark.parametrize("n_bars", [3, 4])
def test_mixed_override_covers_every_nonmonotone_rank_permutation(n_bars):
    ascending = tuple(range(n_bars))
    descending = ascending[::-1]
    expected = set(permutations(range(n_bars))) - {ascending, descending}
    observed = set()
    for index in range(512):
        grid = generator.generate(
            92000 + index, 2 * index, difficulty="medium",
            grid_h=10, n_bars=n_bars, height_pattern="mixed",
        )
        heights = heights_of(grid)
        assert len(set(heights)) == n_bars
        ranks = {height: rank for rank, height in enumerate(sorted(heights))}
        observed.add(tuple(ranks[height] for height in heights))
    assert observed == expected


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_samples_retain_nonminimum_and_nonendpoint_repeats(difficulty):
    saw_nonminimum = saw_nonendpoint = False
    for index in range(96):
        grid = generator.generate(103000 + index, index, difficulty=difficulty)
        heights = heights_of(grid)
        assert 7 <= len(grid) <= 12
        assert 3 <= len(heights) <= 5
        for i, j in combinations(range(len(heights)), 2):
            if heights[i] == heights[j]:
                saw_nonminimum |= heights[i] != min(heights)
                saw_nonendpoint |= (i, j) != (0, len(heights) - 1)
    assert saw_nonminimum
    assert saw_nonendpoint
