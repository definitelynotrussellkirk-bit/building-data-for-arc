"""Matched-input crop-then-boundary-fill family for 25d47dde0246.

The alternative first executes the canonical joint nonzero bounding-box crop.
It then finds zero components touching the *new* crop boundary and recolors
exactly those components cyan(8), leaving enclosed zero holes unchanged.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import stable_rng

Grid = list[list[int]]
MODES = ("canonical", "boundary_fill")
PROFILES = (
    (9, 11),
    (10, 13),
    (12, 14),
    (13, 17),
    (15, 18),
    (18, 21),
    (20, 24),
    (23, 26),
    (27, 29),
    (30, 30),
)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTE = (1, 2, 3, 4, 5, 6, 7, 9)  # reserve cyan(8) for Stage B


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


def _bbox(grid: Grid) -> tuple[int, int, int, int] | None:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return None
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return top, left, bottom, right


def canonical_crop(value: Any) -> Grid:
    source = _grid(value)
    box = _bbox(source)
    if box is None:
        return [[0]]
    top, left, bottom, right = box
    return [row[left : right + 1] for row in source[top : bottom + 1]]


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


def boundary_intermediate(value: Any) -> dict[str, Any]:
    stage = canonical_crop(value)
    height, width = len(stage), len(stage[0])
    boundary: list[tuple[int, int]] = []
    enclosed: list[tuple[int, int]] = []
    boundary_components = 0
    enclosed_components = 0
    for component in _zero_components(stage):
        touches = any(
            r in (0, height - 1) or c in (0, width - 1)
            for r, c in component
        )
        if touches:
            boundary_components += 1
            boundary.extend(component)
        else:
            enclosed_components += 1
            enclosed.extend(component)
    return {
        "stage_shape": [height, width],
        "boundary_zero_cells": [list(cell) for cell in sorted(boundary)],
        "enclosed_zero_cells": [list(cell) for cell in sorted(enclosed)],
        "boundary_component_count": boundary_components,
        "enclosed_component_count": enclosed_components,
        "fill_color": 8,
    }


def _paint(grid: Grid, cells: list[list[int]] | list[tuple[int, int]], color: int) -> Grid:
    output = [row[:] for row in grid]
    for r, c in cells:
        output[r][c] = color
    return output


def solve(value: Any, followup: str = "canonical") -> Grid:
    if type(followup) is not str or followup not in MODES:
        raise ValueError("followup must be canonical or boundary_fill")
    source = _grid(value)
    stage = canonical_crop(source)
    if followup == "canonical":
        return stage
    intermediate = boundary_intermediate(source)
    return _paint(stage, intermediate["boundary_zero_cells"], 8)


def solve_wrong_order(value: Any) -> Grid:
    """Counterfactual: fill original-boundary zeros before applying the crop."""
    source = _grid(value)
    height, width = len(source), len(source[0])
    boundary: list[tuple[int, int]] = []
    for component in _zero_components(source):
        if any(r in (0, height - 1) or c in (0, width - 1) for r, c in component):
            boundary.extend(component)
    return canonical_crop(_paint(source, boundary, 8))


def _ring(grid: Grid, top: int, left: int, height: int, width: int, color: int) -> None:
    bottom = top + height - 1
    right = left + width - 1
    for c in range(left, right + 1):
        grid[top][c] = color
        grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = color
        grid[r][right] = color


def _stage(seed: int, index: int, height: int, width: int) -> Grid:
    rng = stable_rng(seed, f"25d47-parametric-stage-{index}", "1.0.0")
    stage = [[0 for _ in range(width)] for _ in range(height)]
    palette = list(_PALETTE)
    rng.shuffle(palette)

    max_ring_h = max(3, height - 2)
    max_ring_w = max(3, width - 2)
    target_h = max(3, height // 2 + (index % 2))
    target_w = max(3, width // 2 + ((index + 1) % 2))
    ring_h = min(max_ring_h, target_h)
    ring_w = min(max_ring_w, target_w)
    if ring_h % 2 == 0 and ring_h > 3:
        ring_h -= 1
    if ring_w % 2 == 0 and ring_w > 3:
        ring_w -= 1
    ring_top = rng.randint(1, height - ring_h - 1)
    ring_left = rng.randint(1, width - ring_w - 1)
    _ring(stage, ring_top, ring_left, ring_h, ring_w, palette[0])

    # Sparse colored lattice supplies visual/structural diversity without
    # sealing the boundary-connected background or entering the ring cavity.
    row_phase = rng.randrange(2)
    col_phase = rng.randrange(2)
    color_index = 1
    for r in range(1 + row_phase, height - 1, 2):
        for c in range(1 + col_phase, width - 1, 2):
            if ring_top <= r < ring_top + ring_h and ring_left <= c < ring_left + ring_w:
                continue
            stage[r][c] = palette[color_index % len(palette)]
            color_index += 1

    # Add two short asymmetric bars when space permits.  Their gaps make the
    # boundary-connected mask nontrivial without forming another enclosure.
    if width >= 9:
        bar_row = 1 if ring_top > 2 else height - 2
        start = 2
        stop = min(width - 2, start + max(3, width // 3))
        for c in range(start, stop):
            if c != (start + stop) // 2:
                stage[bar_row][c] = palette[2]
    if height >= 9:
        bar_col = 1 if ring_left > 2 else width - 2
        start = 2
        stop = min(height - 2, start + max(3, height // 3))
        for r in range(start, stop):
            if r != (start + stop) // 2:
                stage[r][bar_col] = palette[3]

    # Four colored corners force the canonical joint bbox to be exactly stage.
    for (r, c), color in zip(
        ((0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)),
        palette[4:8],
        strict=True,
    ):
        stage[r][c] = color
    return stage


def scene(seed: int, index: int) -> Grid:
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(index, 0, len(PROFILES) - 1, "index")
    height, width = PROFILES[index]
    rng = stable_rng(seed, f"25d47-parametric-scene-{index}", "1.0.0")
    margin_r = 1 if height < 18 else 1 + rng.randrange(2)
    margin_c = 1 if width < 18 else 1 + rng.randrange(2)
    stage_h = height - 2 * margin_r
    stage_w = width - 2 * margin_c
    stage = _stage(seed, index, stage_h, stage_w)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for r, row in enumerate(stage):
        for c, value in enumerate(row):
            grid[margin_r + r][margin_c + c] = value

    intermediate = boundary_intermediate(grid)
    if not intermediate["boundary_zero_cells"] or not intermediate["enclosed_zero_cells"]:
        raise AssertionError("constructed scene must contain exposed and enclosed zero regions")
    if solve(grid, "boundary_fill") == solve_wrong_order(grid):
        raise AssertionError("constructed scene collapsed the wrong-order witness")
    return grid
