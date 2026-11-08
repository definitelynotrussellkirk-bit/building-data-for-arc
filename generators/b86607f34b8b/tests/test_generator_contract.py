"""Behavioral regressions; portable in the library and copied task runtime."""
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
TASK = 'b86607f34b8b'
SOURCE = next(path for path in (
    ROOT / 'generators' / TASK / 'generator.py',
    ROOT / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py',
) if path.is_file())
spec = importlib.util.spec_from_file_location('selected_closure_generator', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


@pytest.mark.parametrize('band', [None, 'easy', 'medium', 'hard'])
def test_exact_dimensions_and_color_count(band):
    for h, w, count in [(9, 9, 3), (9, 14, 5), (14, 9, 5), (14, 14, 4)]:
        grid = gen.generate(17, 7, difficulty=band,
                            grid_h=h, grid_w=w, n_colors=count)
        assert (len(grid), len(grid[0])) == (h, w)
        colors = {value for row in grid[3:] for value in row} - {0}
        assert len(colors) == count
        assert gen.self_check(grid) == []


@pytest.mark.parametrize('options', [
    {'typo_axis': 1}, {'grid_h': 8}, {'grid_w': 15}, {'n_colors': 2},
    {'n_colors': 6}, {'grid_h': True}, {'grid_h': '9'}, {'n_colors': 4.5},
])
def test_rejects_invalid_or_unknown_controls(options):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **options)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_mode_four_and_equal_mode_overlap_are_in_default_support(band):
    modes = set()
    repeated = False
    for index in range(6):
        grid = gen.generate(73, index, difficulty=band)
        entries = [grid[1][c] for c, color in enumerate(grid[0]) if color]
        modes.update(entries)
        repeated |= len(entries) > len(set(entries))
    assert modes == {1, 2, 3, 4}
    assert repeated


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
def test_default_canonical_shape_and_palette_support(band):
    profiles = set()
    for index in range(20):
        grid = gen.generate(2100 + index, index, difficulty=band)
        profiles.add((len(grid), len(grid[0]), tuple(sorted({c for row in grid for c in row}))))
    assert (9, 11, (0, 1, 2, 3, 4, 9)) in profiles


def test_canonical_inputs_remain_lawful():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert gen.self_check(pair['input']) == []


@pytest.mark.parametrize('grid', [[], [[]], [[0, 0], [0]], [[True] * 9 for _ in range(9)]])
def test_malformed_input_is_rejected_without_crashing(grid):
    assert gen.self_check(grid)


def test_orphan_legend_mode_and_duplicate_legend_color_are_rejected():
    original = gen.generate(29, 2)
    orphan = [row[:] for row in original]
    empty_col = next(c for c, value in enumerate(orphan[0]) if value == 0)
    orphan[1][empty_col] = 4
    assert gen.self_check(orphan)
    duplicate = [row[:] for row in original]
    columns = [c for c, value in enumerate(duplicate[0]) if value]
    duplicate[0][columns[1]] = duplicate[0][columns[0]]
    assert gen.self_check(duplicate)


def test_default_support_includes_canonical_scale_component_counts():
    def count_components(grid):
        remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
        count = 0
        while remaining:
            count += 1
            point = remaining.pop()
            stack = [point]
            color = grid[point[0]][point[1]]
            while stack:
                r, c = stack.pop()
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                        remaining.remove(neighbor)
                        stack.append(neighbor)
        return count
    counts = [count_components(gen.generate(314, index)) for index in range(20)]
    # Canonical median is 15; the inherited gate allows a tolerance of seven.
    assert min(counts) <= 22, counts
