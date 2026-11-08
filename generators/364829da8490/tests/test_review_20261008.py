from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.364829da8490.generator")

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = _CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _zero_components(grid, directions):
    height, width = len(grid), len(grid[0])
    seen = set()
    regions = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = set()
            while queue:
                current = queue.popleft()
                cells.add(current)
                for delta_row, delta_col in directions:
                    neighbor = current[0] + delta_row, current[1] + delta_col
                    if not (0 <= neighbor[0] < height and 0 <= neighbor[1] < width):
                        continue
                    if neighbor in seen or grid[neighbor[0]][neighbor[1]] != 0:
                        continue
                    seen.add(neighbor)
                    queue.append(neighbor)
            regions.append(cells)
    return regions


def _adjacent_colors(grid, cells, directions):
    height, width = len(grid), len(grid[0])
    return {
        grid[row + delta_row][col + delta_col]
        for row, col in cells
        for delta_row, delta_col in directions
        if 0 <= row + delta_row < height
        and 0 <= col + delta_col < width
        and grid[row + delta_row][col + delta_col] != 0
    }


def _fill_regions(grid, *, connectivity=_CARDINAL, boundary=_CARDINAL, ignore_border=False):
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for cells in _zero_components(grid, connectivity):
        touches_border = any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        )
        colors = _adjacent_colors(grid, cells, boundary)
        if (ignore_border or not touches_border) and len(colors) == 1:
            color = next(iter(colors))
            for row, col in cells:
                output[row][col] = color
    return output


def _fill_only_connected_boundaries(grid):
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for cells in _zero_components(grid, _CARDINAL):
        if any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells):
            continue
        boundary = {
            (row + delta_row, col + delta_col)
            for row, col in cells
            for delta_row, delta_col in _CARDINAL
            if 0 <= row + delta_row < height
            and 0 <= col + delta_col < width
            and grid[row + delta_row][col + delta_col] != 0
        }
        colors = {grid[row][col] for row, col in boundary}
        if len(colors) != 1 or not boundary:
            continue
        seen = {next(iter(boundary))}
        queue = deque(seen)
        while queue:
            row, col = queue.popleft()
            for delta_row, delta_col in _CARDINAL:
                neighbor = row + delta_row, col + delta_col
                if neighbor in boundary and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if seen != boundary:
            continue
        color = next(iter(colors))
        for row, col in cells:
            output[row][col] = color
    return output


def _skip_single_cell_holes(grid):
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for cells in _zero_components(grid, _CARDINAL):
        if len(cells) == 1:
            continue
        if any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells):
            continue
        colors = _adjacent_colors(grid, cells, _CARDINAL)
        if len(colors) == 1:
            color = next(iter(colors))
            for row, col in cells:
                output[row][col] = color
    return output


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 16.9),
        ("grid_h", True),
        ("grid_h", "12"),
        ("grid_h", 8),
        ("grid_h", 17),
        ("grid_w", 11.2),
        ("grid_w", False),
        ("grid_w", "14"),
        ("grid_w", 10),
        ("grid_w", 19),
        ("scene_profile", 1),
        ("scene_profile", "not-a-profile"),
    ],
)
def test_invalid_exact_overrides_are_rejected_before_coercion(axis, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{axis: value})


def test_every_query_rotation_keeps_the_complete_teaching_contract():
    period = gen.LESSON_SCHEDULE_PERIOD
    assert gen.EXAMPLES_NEEDED + 1 == period
    for start in range(period):
        pairs = []
        for offset in range(gen.EXAMPLES_NEEDED + 1):
            grid = gen.generate(811, start + offset, difficulty="medium")
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    start,
                    query_index,
                    name,
                )


def test_open_profile_distinguishes_border_contact_and_zero_connectivity():
    for seed in range(12):
        grid = gen.generate(seed, 0, difficulty="medium", scene_profile="open_vs_closed")
        expected = gen.rule_mirror(grid)
        assert _fill_regions(grid, ignore_border=True) != expected
        assert _fill_regions(grid, connectivity=_EIGHT) != expected


def test_mixed_profile_includes_a_disconnected_single_cell_enclosure():
    for seed in range(12):
        grid = gen.generate(seed, 0, difficulty="medium", scene_profile="mixed_border")
        expected = gen.rule_mirror(grid)
        facts = gen.semantic_observables(grid)
        assert any(region["size"] == 1 for region in facts["fillable_regions"])
        assert _fill_only_connected_boundaries(grid) != expected
        assert _skip_single_cell_holes(grid) != expected


def test_irregular_profile_distinguishes_cardinal_from_diagonal_boundary_color():
    for seed in range(12):
        grid = gen.generate(seed, 0, difficulty="medium", scene_profile="irregular_hole")
        expected = gen.rule_mirror(grid)
        assert _fill_regions(grid, boundary=_EIGHT) != expected


def test_topology_rivals_are_declared_for_source_bound_censuses():
    expected = {
        "ignore_border_contact",
        "use_eight_connected_zero_regions",
        "use_eight_neighbor_boundary_colors",
        "require_connected_boundary",
        "skip_single_cell_holes",
    }
    assert expected <= set(gen.LESSON_COMPETITORS)
    assert expected <= set(gen.SEMANTIC_RIVALS)
    assert expected <= set(gen.CANONICAL_SHORTCUTS)

@pytest.mark.parametrize("profile", ["rect_pair", "open_vs_closed"])
def test_anchor_profiles_match_canonical_dimension_palette_envelope(profile):
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            grid = gen.generate(seed, 0, difficulty=difficulty, scene_profile=profile)
            assert 9 <= len(grid) <= 10
            assert 11 <= len(grid[0]) <= 13
            assert len({value for row in grid for value in row}) == 3
