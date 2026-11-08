"""Geometry, color roles and reproducibility of native extent-projection inputs."""
from collections import Counter
import importlib.util
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
HOME = ROOT / 'generators/48bda9528e71/workspace/parametric'
_spec = importlib.util.spec_from_file_location('_native_projection_sampler_tests', HOME / 'sampler.py')
sampler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sampler)
selected, _, _ = load_selected_generator('48bda9528e71', root=ROOT)


def facts(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 8}
    counts = Counter(grid[r][c] for r, c in cells)
    rare_color = min(counts, key=counts.get)
    rare = {p for p in cells if grid[p[0]][p[1]] == rare_color}
    return cells, counts, rare_color, rare


def bbox(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def rays(cells, n):
    result = set()
    for r in {r for r, _ in cells}:
        cs = [c for rr, c in cells if rr == r]
        result.update((r, c) for c in range(n) if c < min(cs) or c > max(cs))
    for c in {c for _, c in cells}:
        rs = [r for r, cc in cells if cc == c]
        result.update((r, c) for r in range(n) if r < min(rs) or r > max(rs))
    return result


@pytest.mark.parametrize('seed', [0, 1, 17, 2**63 - 1])
def test_every_constructive_role_obeys_shape_color_and_marker_grammar(seed):
    train, test = sampler.sample_inputs(seed, 6, 4)
    assert (len(train), len(test)) == (6, 4)
    for grid in train + test:
        n = len(grid)
        assert type(grid) is list and 5 <= n <= 30
        assert all(type(row) is list and len(row) == n for row in grid)
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
        cells, counts, rare_color, rare = facts(grid)
        assert 7 <= len(cells) <= (n * n - 1) // 2
        assert selected._is_connected(cells)
        assert selected._is_orthogonally_convex(cells)
        r0, c0, r1, c1 = bbox(cells)
        assert r1 - r0 >= 2 and c1 - c0 >= 2
        assert len(counts) in (2, 3)
        assert all(counts[rare_color] < count for color, count in counts.items() if color != rare_color)
        assert rare <= selected._interior_cells(cells)
        markers = selected._extent_positions(cells, n, n)
        assert len(markers) >= 4
        assert markers < rays(cells, n)
        assert not (markers & cells)


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_minimum_lesson_exposes_color_frequency_concavity_and_edge_clipping(seed):
    train, _ = sampler.sample_inputs(seed)
    info = [facts(grid) for grid in train]
    assert [len(counts) for _, counts, _, _ in info] == [3, 2, 3]
    assert info[0][2] != 0 and 0 in info[0][1]
    assert info[1][2] == 0
    assert len({len(rare) for _, _, _, rare in info}) >= 2
    assert len({len(cells) for cells, _, _, _ in info}) == 3
    assert all(selected._lattice_convex_hull(cells) != cells for cells, _, _, _ in info)
    first_cells, first_counts, rare_color, rare = info[0]
    n = len(train[0])
    r0, c0, r1, c1 = bbox(first_cells)
    assert 0 < r0 <= r1 < n - 1 and 0 < c0 <= c1 < n - 1
    assert train[0][(r0 + r1) // 2][(c0 + c1) // 2] != rare_color
    rare_box = bbox(rare)
    rare_area = (rare_box[2] - rare_box[0] + 1) * (rare_box[3] - rare_box[1] + 1)
    common_boxes = []
    for color in first_counts:
        if color != rare_color:
            positions = {p for p in first_cells if train[0][p[0]][p[1]] == color}
            rb, cb, re, ce = bbox(positions)
            common_boxes.append((re - rb + 1) * (ce - cb + 1))
    assert min(common_boxes) < rare_area
    assert any({p for p in first_cells if train[0][p[0]][p[1]] == color}
               <= selected._interior_cells(first_cells)
               for color in first_counts if color != rare_color)
    second_cells = info[1][0]
    n = len(train[1])
    assert any(r in (0, n - 1) or c in (0, n - 1) for r, c in second_cells)
    # Opposite edges of an internal cross have distinct row and column extents.
    row_extents = {(min(c for rr, c in first_cells if rr == r), max(c for rr, c in first_cells if rr == r))
                   for r in {r for r, _ in first_cells}}
    col_extents = {(min(r for r, cc in first_cells if cc == c), max(r for r, cc in first_cells if cc == c))
                   for c in {c for _, c in first_cells}}
    assert len(row_extents) >= 2 and len(col_extents) >= 2


@pytest.mark.parametrize('seed', [0, 17, 2**63 - 1])
def test_query_boundaries_use_substantial_distinct_shapes(seed):
    _, test = sampler.sample_inputs(seed)
    assert [len(grid) for grid in test] == [5, 16, 24, 30]
    assert len(facts(test[0])[0]) == 12
    assert len(facts(test[2])[0]) >= 180
    largest = facts(test[3])[0]
    assert len(largest) in (275, 371)
    assert bbox(largest) == (0, 0, 29, 29)
    assert len({len(facts(grid)[0]) for grid in test}) == 4


def test_fresh_deterministic_prefixes_leave_global_rng_untouched():
    state = random.getstate()
    full = sampler.sample_inputs(1119, 6, 4)
    assert random.getstate() == state
    assert sampler.sample_inputs(1119, 6, 4) == full
    for demos in (3, 4, 5, 6):
        for queries in (1, 2, 3, 4):
            assert sampler.sample_inputs(1119, demos, queries) == (full[0][:demos], full[1][:queries])
    changed = sampler.sample_inputs(1119)
    changed[0][0][0][0] = 99
    assert sampler.sample_inputs(1119)[0][0][0][0] != 99
    assert sampler.sample_inputs(1120) != sampler.sample_inputs(1119)


@pytest.mark.parametrize('seed', [True, False, -1, 2**63, 1.0, '1', None])
def test_invalid_seed(seed):
    with pytest.raises(ValueError):
        sampler.sample_inputs(seed)


@pytest.mark.parametrize('demos', [True, False, 2, 7, 3.0, '3', None])
def test_invalid_demo_count(demos):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, demos, 4)


@pytest.mark.parametrize('queries', [True, False, 0, 5, 1.0, '1', None])
def test_invalid_query_count(queries):
    with pytest.raises(ValueError):
        sampler.sample_inputs(0, 3, queries)
