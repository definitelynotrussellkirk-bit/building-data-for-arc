"""Portable semantic regressions for separate component bounding-box outlines.

Canonical labels come from reviewer_support. Hand-made labels are executed by
the public Catalog.apply API. The small Python renderer below is explicitly an
independent diagnostic mirror; it is never represented as a Racket execution.
"""
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK_ID = "623cca1dd5a8"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT)


def components(grid):
    """Independent four-neighbor, equal-color component census."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    groups = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        todo = [start]
        unseen.remove(start)
        cells = set()
        while todo:
            r, c = todo.pop()
            cells.add((r, c))
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    todo.append(point)
        groups.append((color, cells))
    return groups


def bounds(cells):
    return min(r for r, _ in cells), min(c for _, c in cells), max(r for r, _ in cells), max(c for _, c in cells)


def outline_mirror(grid, *, group_by_color=False, preserve_input=False):
    groups = components(grid)
    if group_by_color:
        colors = {}
        for color, cells in groups:
            colors.setdefault(color, set()).update(cells)
        groups = list(colors.items())
    result = [row[:] for row in grid] if preserve_input else [[0] * len(grid[0]) for _ in grid]
    for color, cells in groups:
        r0, c0, r1, c1 = bounds(cells)
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if r in (r0, r1) or c in (c0, c1):
                    result[r][c] = color
    return result


REPEATED_COLOR = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 4, 4, 4, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 4, 4, 4, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]

# An occupied center must disappear while the absent upper/right border fills.
INTERIOR_PIXEL = [
    [0, 0, 0, 0, 0],
    [0, 6, 0, 0, 0],
    [0, 6, 6, 0, 0],
    [0, 6, 6, 6, 0],
    [0, 0, 0, 0, 0],
]


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"v{p['variant']}-{p['split']}-{p['pair_index']}")
def test_all_canonical_inputs_are_accepted(pair):
    assert canonical_path(ROOT).is_file()
    assert GEN.self_check(pair["input"]) == []


def test_lawful_disconnected_same_color_components_are_accepted():
    assert GEN.self_check(REPEATED_COLOR) == []
    assert len(components(REPEATED_COLOR)) == 2


@pytest.mark.parametrize("grid", [
    [[4]],
    [[3, 3, 3], [3, 3, 3], [3, 3, 3]],
    [[4, 0], [4, 4]],
    [[4, 0], [0, 4]],
    [[2, 5]],
    [[2, 3], [2, 3], [2, 0]],
], ids=["singleton", "solid", "thin", "diagonal-same-color", "edge-different-colors", "adjacent-thin"])
def test_lawful_boundary_inputs_are_accepted(grid):
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("grid", [
    [], [[]], [[0]], [[10]], [[-1]], [[True]], [[1.0]],
    [[1, 0], [1]], [[1]] * 31,
    [[2, 2, 2], [2, 4, 0], [2, 0, 0]],
], ids=["empty", "empty-row", "blank", "large-color", "negative-color", "bool-color",
        "float-color", "ragged", "too-tall", "overlapping-bboxes"])
def test_malformed_or_colliding_inputs_are_rejected(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


@pytest.mark.parametrize("invalid", [True, False, 1.0, -1, 10, "2", None])
def test_invalid_cell_cannot_hide_beside_an_otherwise_valid_blob(invalid):
    grid = [row[:] for row in INTERIOR_PIXEL]
    grid[0][4] = invalid
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_oversized_canvas_cannot_hide_behind_an_otherwise_valid_blob():
    grid = [row[:] for row in INTERIOR_PIXEL] + [[0] * 5 for _ in range(26)]
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


@pytest.fixture(scope="module")
def hand_made_authority():
    from arcpuzzles.catalog import Catalog

    report = Catalog(ROOT).apply(TASK_ID, [REPEATED_COLOR, INTERIOR_PIXEL])
    assert report["reference"] == "canonical"
    assert report["rule_hash_matches_catalog"] is True
    assert report["generator_sha256"] == SOURCE_SHA256
    results = report["results"]
    assert len(results) == 2
    assert all(row["output"] is not None for row in results), results
    return [row["output"] for row in results]


def test_racket_outlines_each_component_instead_of_color_union(hand_made_authority):
    output = hand_made_authority[0]
    assert output == outline_mirror(REPEATED_COLOR)
    assert output != outline_mirror(REPEATED_COLOR, group_by_color=True)
    assert all(output[r][4] == output[r][5] == 0 for r in range(8))


def test_racket_removes_existing_interior_and_adds_missing_border(hand_made_authority):
    output = hand_made_authority[1]
    assert GEN.self_check(INTERIOR_PIXEL) == []
    assert output == outline_mirror(INTERIOR_PIXEL)
    assert output[2][2] == 0
    assert output[1][2] == output[2][3] == 6
    assert output != outline_mirror(INTERIOR_PIXEL, preserve_input=True)


@pytest.fixture(scope="module", params=["easy", "medium", "hard"])
def generated_population(request):
    return [GEN.generate(seed, index, difficulty=request.param)
            for seed in range(4) for index in range(24)]


def test_generated_population_contains_disconnected_repeated_colors(generated_population):
    assert any(max(Counter(color for color, _ in components(grid)).values(), default=0) > 1
               for grid in generated_population)


def test_generated_population_contains_canonical_thin_boxes(generated_population):
    assert any(min(r1 - r0 + 1, c1 - c0 + 1) <= 2
               for grid in generated_population for _, cells in components(grid)
               for r0, c0, r1, c1 in [bounds(cells)])


def test_generated_population_contains_interior_pixel_removal(generated_population):
    assert any(any(r0 < r < r1 and c0 < c < c1 for r, c in cells)
               for grid in generated_population for _, cells in components(grid)
               for r0, c0, r1, c1 in [bounds(cells)])


def test_generated_population_is_self_checked_and_nonidentity(generated_population):
    for grid in generated_population:
        assert GEN.self_check(grid) == []
        assert outline_mirror(grid) != grid
