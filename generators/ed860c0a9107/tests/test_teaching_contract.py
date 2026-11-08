"""Independent geometry/rival tests for the default four-residue curriculum.

The Python oracle is separate from construction. Racket parity is measured by
retained public apply and census receipts, not by these unit tests.
"""
from __future__ import annotations
import pytest
from reviewer_support import find_root, load_selected_generator, canonical_pairs
from review_diagnostics import structural_signature

ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator("ed860c0a9107", root=ROOT)


def rectangles(grid):
    bg = grid[0][0]
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != bg}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, cells = [start], [start]
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = (r + dr, c + dc)
                    if point in remaining:
                        remaining.remove(point)
                        stack.append(point)
                        cells.append(point)
        result.append((min(r for r, c in cells), min(c for r, c in cells),
                       max(r for r, c in cells), max(c for r, c in cells)))
    return sorted(result)


def independent_overlay(grid, mode='first_visible'):
    bg = grid[0][0]
    ordered = rectangles(grid)
    if mode == 'first_container_only':
        ordered = ordered[:1]
    if mode == 'column_major':
        ordered.sort(key=lambda box: (box[1], box[0]))
    if mode == 'numeric_box_color':
        ordered.sort(key=lambda box: next(grid[r][c] for r in range(box[0], box[2] + 1)
                    for c in range(box[1], box[3] + 1) if grid[r][c] not in (0, bg)))
    palette_rank = {}
    for row in grid:
        for value in row:
            if value not in (0, bg):
                palette_rank.setdefault(value, len(palette_rank))
    top, left, bottom, right = ordered[0]
    output = []
    for r in range(bottom - top + 1):
        row = []
        for c in range(right - left + 1):
            values = [grid[t + r][l + c] for t, l, b, z in ordered
                      if grid[t + r][l + c] not in (0, bg)]
            if not values:
                value = 0
            elif mode == 'last_visible':
                value = values[-1]
            elif mode == 'lowest_color':
                value = min(values)
            elif mode == 'highest_color':
                value = max(values)
            elif mode == 'palette_scan':
                value = min(values, key=palette_rank.get)
            else:
                value = values[0]
            row.append(value)
        output.append(row)
    return output


RIVALS = tuple(gen.LESSON_COMPETITORS)


@pytest.mark.parametrize('rival', tuple(gen.CANONICAL_SHORTCUTS))
def test_independent_rivals_fit_every_canonical_label(rival):
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8
    for pair in pairs:
        assert independent_overlay(pair['input']) == pair['output']
        assert independent_overlay(pair['input'], rival) == pair['output']


@pytest.mark.parametrize('difficulty', ('easy', 'medium', 'hard'))
@pytest.mark.parametrize('seed', (20000, 20006, 20015))
@pytest.mark.parametrize('start', range(4))
def test_every_default_window_refutes_rivals_in_every_query_holdout(difficulty, seed, start):
    grids = [gen.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    labels = [independent_overlay(grid) for grid in grids]
    for grid, label in zip(grids, labels):
        assert gen.rule_mirror(grid) == label
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) == independent_overlay(grid, name)
    for rival in RIVALS:
        disagrees = [independent_overlay(grid, rival) != label for grid, label in zip(grids, labels)]
        assert sum(disagrees) >= 2, (SOURCE_SHA256, difficulty, seed, start, rival, disagrees)
        for held_out in range(4):
            demos = [{'input': grid, 'output': label} for i, (grid, label) in enumerate(zip(grids, labels))
                     if i != held_out]
            query = {'input': grids[held_out], 'output': labels[held_out]}
            assert any(disagrees[i] for i in range(4) if i != held_out)
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize('box_h', range(2, 6))
@pytest.mark.parametrize('box_w', range(2, 6))
@pytest.mark.parametrize('sample_index', (0, 2))
@pytest.mark.parametrize('difficulty', ('easy', 'medium', 'hard'))
def test_strong_default_count_samples_cover_every_legal_box_shape(box_h, box_w, sample_index, difficulty):
    controls = {'grid_h': 14, 'grid_w': 14, 'box_h': box_h, 'box_w': box_w}
    grid = gen.generate(4301 + 10 * box_h + box_w, sample_index, difficulty=difficulty, **controls)
    assert gen.self_check(grid) == []
    measured = gen.observe_overrides(grid)
    assert measured == {**controls, 'n_containers': 4}
    label = independent_overlay(grid)
    for rival in RIVALS:
        assert independent_overlay(grid, rival) != label, (SOURCE_SHA256, box_h, box_w, sample_index, difficulty, rival)
    if sample_index == 0:
        assert structural_signature({'input': grid, 'output': label})['marker_count'] == 0
        assert len({v for row in grid for v in row}) == 4


@pytest.mark.parametrize('n_containers', (2, 3))
@pytest.mark.parametrize('sample_index', range(4))
@pytest.mark.parametrize('box_size', (2, 5))
def test_explicit_count_overrides_remain_exact_without_claiming_extra_identifiability(n_containers, sample_index, box_size):
    controls = {'grid_h': 14, 'grid_w': 14, 'box_h': box_size, 'box_w': box_size,
                'n_containers': n_containers}
    grid = gen.generate(7301, sample_index, **controls)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == controls
    assert independent_overlay(grid, 'last_visible') != independent_overlay(grid)
