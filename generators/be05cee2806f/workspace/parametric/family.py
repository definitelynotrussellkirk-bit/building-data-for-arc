"""Matched-input absorb-then-activate family for be05cee2806f.

The alternate first executes the canonical zero-component absorption.  It then
uses only cells newly changed from 0 to 1 as an input-dependent activation mask
and recolors adjacent original colored cells to 1.  Original 1-cells are not
Stage-B activators.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import stable_rng

Grid = list[list[int]]
MODES = ("canonical", "activated_neighbors")
PROFILES = (
    (12, 13),
    (13, 13),
    (15, 15),
    (16, 16),
    (17, 18),
    (18, 21),
    (20, 24),
    (23, 26),
    (27, 29),
    (30, 30),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _grid(value: Any) -> Grid:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(value[0])
            or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
            for row in value
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer ARC colors")
    return [row[:] for row in value]


def _zero_components(grid: Grid) -> list[list[tuple[int, int]]]:
    unseen = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 0
    }
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _CARDINAL:
                neighbor = (r + dr, c + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(cells))
    return components


def _touches_one(grid: Grid, component: list[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        0 <= r + dr < height
        and 0 <= c + dc < width
        and grid[r + dr][c + dc] == 1
        for r, c in component
        for dr, dc in _CARDINAL
    )


def canonical_absorb(value: Any) -> Grid:
    source = _grid(value)
    output = [row[:] for row in source]
    for component in _zero_components(source):
        if _touches_one(source, component):
            for r, c in component:
                output[r][c] = 1
    return output


def _colored_neighbors(source: Grid, cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    height, width = len(source), len(source[0])
    targets: set[tuple[int, int]] = set()
    for r, c in cells:
        for dr, dc in _CARDINAL:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width and source[rr][cc] not in (0, 1):
                targets.add((rr, cc))
    return targets


def activation_intermediate(value: Any) -> dict[str, Any]:
    source = _grid(value)
    stage = canonical_absorb(source)
    newly_absorbed = {
        (r, c)
        for r, row in enumerate(source)
        for c, original in enumerate(row)
        if original == 0 and stage[r][c] == 1
    }
    preserved = {
        (r, c)
        for r, row in enumerate(source)
        for c, original in enumerate(row)
        if original == 0 and stage[r][c] == 0
    }
    targets = _colored_neighbors(source, newly_absorbed)
    original_ones = {
        (r, c)
        for r, row in enumerate(source)
        for c, original in enumerate(row)
        if original == 1
    }
    wrong_targets = _colored_neighbors(source, original_ones)
    return {
        "stage_shape": [len(source), len(source[0])],
        "newly_absorbed_cells": [list(cell) for cell in sorted(newly_absorbed)],
        "preserved_zero_cells": [list(cell) for cell in sorted(preserved)],
        "stage_b_targets": [list(cell) for cell in sorted(targets)],
        "wrong_original_one_targets": [list(cell) for cell in sorted(wrong_targets)],
    }


def _paint(grid: Grid, cells: list[list[int]], color: int = 1) -> Grid:
    output = [row[:] for row in grid]
    for r, c in cells:
        output[r][c] = color
    return output


def solve(value: Any, followup: str = "canonical") -> Grid:
    if type(followup) is not str or followup not in MODES:
        raise ValueError("followup must be canonical or activated_neighbors")
    source = _grid(value)
    stage = canonical_absorb(source)
    if followup == "canonical":
        return stage
    return _paint(stage, activation_intermediate(source)["stage_b_targets"])


def solve_wrong_original_ones(value: Any) -> Grid:
    source = _grid(value)
    stage = canonical_absorb(source)
    return _paint(stage, activation_intermediate(source)["wrong_original_one_targets"])


def _transform(cells: set[tuple[int, int]], rotation: int, reflected: bool) -> set[tuple[int, int]]:
    transformed = set(cells)
    if reflected:
        transformed = {(r, 4 - c) for r, c in transformed}
    for _ in range(rotation % 4):
        transformed = {(c, 4 - r) for r, c in transformed}
    return transformed


def _place(grid: Grid, top: int, left: int, cells: set[tuple[int, int]], value: int) -> None:
    for r, c in cells:
        grid[top + r][left + c] = value


def _active_motif(grid: Grid, top: int, left: int, rotation: int, reflected: bool) -> None:
    zeros = _transform({(2, 1), (2, 2), (1, 2)}, rotation, reflected)
    seed = _transform({(2, 0)}, rotation, reflected)
    _place(grid, top, left, zeros, 0)
    _place(grid, top, left, seed, 1)


def _isolated_motif(grid: Grid, top: int, left: int, rotation: int, reflected: bool) -> None:
    zeros = _transform({(2, 1), (2, 2), (1, 2)}, rotation, reflected)
    _place(grid, top, left, zeros, 0)


def _one_only_motif(grid: Grid, top: int, left: int) -> None:
    grid[top + 2][left + 2] = 1


def scene(seed: int, index: int) -> Grid:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(PROFILES) - 1, "index")
    height, width = PROFILES[index]
    rng = stable_rng(seed, f"be05-parametric-scene-{index}", "1.0.0")
    palette = list(range(2, 10))
    rng.shuffle(palette)
    grid = [
        [palette[(3 * r + 5 * c + index) % len(palette)] for c in range(width)]
        for r in range(height)
    ]

    anchors = [(0, 0), (0, width - 5), (height - 5, 0), (height - 5, width - 5)]
    rng.shuffle(anchors)
    rotations = [rng.randrange(4) for _ in range(3)]
    reflections = [bool(rng.randrange(2)) for _ in range(3)]
    _active_motif(grid, *anchors[0], rotations[0], reflections[0])
    _active_motif(grid, *anchors[1], rotations[1], reflections[1])
    _isolated_motif(grid, *anchors[2], rotations[2], reflections[2])
    _one_only_motif(grid, *anchors[3])

    intermediate = activation_intermediate(grid)
    palette_seen = {value for row in grid for value in row}
    if palette_seen != set(range(10)):
        raise AssertionError(f"constructed scene lost palette coverage: {palette_seen}")
    if not intermediate["newly_absorbed_cells"] or not intermediate["preserved_zero_cells"]:
        raise AssertionError("constructed scene must exercise both canonical branches")
    if len(intermediate["stage_b_targets"]) < 8:
        raise AssertionError("constructed scene needs a substantive Stage-B mask")
    if solve(grid, "activated_neighbors") == solve_wrong_original_ones(grid):
        raise AssertionError("constructed scene collapsed the wrong-intermediate witness")
    return grid
