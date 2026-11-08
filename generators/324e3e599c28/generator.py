"""Generator for arc_puzzle_bank_fifth21:M35 — point reflection about 9.

The input contains one maroon (9) anchor and one connected colored source
object.  The canonical Racket rule keeps the input and copies every nonzero,
non-9 source cell to the position obtained by a 180-degree rotation around the
anchor.  Generated targets are blank and in-bounds, so every source cell makes
one visible same-color copy.

The sequential sample-index schedule deliberately alternates diagonal,
horizontal, and vertical source/anchor relations.  Thus every normal 3-demo
lesson contains evidence against grid-center reflection, one-axis mirroring,
erasing the source, recoloring the copy, and fixed-quadrant shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "324e3e599c28"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "040d2eefe2c6"
SUMMARY = (
    "One 9-anchor and one connected 3-4 cell source object; copy each source "
    "cell, with its own color, through the anchor by 180-degree point reflection."
)

EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0 and there is exactly one color-9 anchor",
    "the source is one 4-connected object of 3 or 4 non-{0,9} cells",
    "every reflected target is in-bounds, blank, and disjoint from the source",
    "sample indices 0,1,2 cover diagonal, horizontal, and vertical relations",
]

# Every declared axis is exact and observable from the returned input grid.
# Difficulty changes the sampling bias, never the lawful override domain.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased 9..12",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased 9..12",
        "valid": "9..12",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-biased 3..4",
        "valid": "3..4",
    },
    "n_colors": {
        "type": "int",
        "default": "rng 1..2",
        "valid": "1..2",
    },
    "primary_color": {
        "type": "color",
        "default": "rng nonzero/non-9",
        "valid": "1..8",
    },
}

_LAYOUTS = ("diagonal", "horizontal", "vertical")
_DIAGONAL_SHAPES = {
    3: (
        ((1, 1), (1, 2), (2, 1)),
        ((1, 1), (2, 1), (2, 2)),
    ),
    4: (
        ((1, 1), (1, 2), (2, 1), (2, 2)),
        ((1, 1), (2, 1), (2, 2), (3, 1)),
    ),
}


def _blob_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def _anchor_cells(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    start = min(cells)
    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _classify_layout(grid: list[list[int]]) -> str:
    """Return the generated source relation, or ``other`` for arbitrary grids."""
    anchors = _anchor_cells(grid)
    cells = _blob_cells(grid)
    if len(anchors) != 1 or not cells:
        return "other"
    ar, ac = anchors[0]
    if all(r == ar for r, _ in cells):
        return "horizontal"
    if all(c == ac for _, c in cells):
        return "vertical"
    if (
        all(r < ar and c < ac for r, c in cells)
        or all(r < ar and c > ac for r, c in cells)
        or all(r > ar and c < ac for r, c in cells)
        or all(r > ar and c > ac for r, c in cells)
    ):
        return "diagonal"
    return "other"


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    """Recover every exact non-dimension AXES value from a returned grid."""
    cells = sorted(_blob_cells(grid))
    colors = {grid[r][c] for r, c in cells}
    return {
        "n_cells": len(cells),
        "n_colors": len(colors),
        "primary_color": grid[cells[0][0]][cells[0][1]] if cells else -1,
    }


def _anchor_for_layout(
    h: int,
    w: int,
    layout: str,
    sample_index: int,
    rng,
) -> tuple[int, int]:
    """Choose a safe anchor; normal lessons intentionally use off-center anchors."""
    cr, cc = h // 2, w // 2
    # Every four-pair episode has three off-center demonstrations and one
    # centered query-like case.  For bars, shift only orthogonally so a
    # four-cell source and its reflection still fit on the active axis.
    centered = sample_index % 4 == 3
    if centered:
        return cr, cc
    row_sign = rng.choice((-1, 1))
    col_sign = rng.choice((-1, 1))
    if layout == "horizontal":
        return cr + row_sign, cc
    if layout == "vertical":
        return cr, cc + col_sign
    return cr + row_sign, cc + col_sign


def _source_cells(
    ar: int,
    ac: int,
    layout: str,
    n_cells: int,
    sample_index: int,
    rng,
) -> list[tuple[int, int]]:
    """Construct one connected source object whose reflected image is disjoint."""
    if layout == "horizontal":
        side = -1 if (sample_index + rng.randrange(2)) % 2 == 0 else 1
        return [(ar, ac + side * distance) for distance in range(1, n_cells + 1)]
    if layout == "vertical":
        side = -1 if (sample_index + rng.randrange(2)) % 2 == 0 else 1
        return [(ar + side * distance, ac) for distance in range(1, n_cells + 1)]

    row_sign = rng.choice((-1, 1))
    col_sign = rng.choice((-1, 1))
    shape = rng.choice(_DIAGONAL_SHAPES[n_cells])
    return [
        (ar + row_sign * dr, ac + col_sign * dc)
        for dr, dc in shape
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 9, 12)
    w = ctx.draw_int_diff("grid_w", 9, 12)
    n_cells = ctx.draw_int_diff("n_cells", 3, 4)
    n_colors = ctx.draw_int("n_colors", 1, 2)
    primary_color = ctx.draw_color("primary_color", exclude={0, 9})

    layout = _LAYOUTS[sample_index % len(_LAYOUTS)]
    layout_rng = ctx.draw_rng("layout")
    ar, ac = _anchor_for_layout(h, w, layout, sample_index, layout_rng)
    cells = sorted(
        _source_cells(ar, ac, layout, n_cells, sample_index, layout_rng)
    )

    # This is an internal construction assertion, not a fallback.  A failure is
    # loud because silently replacing a requested axis would violate the
    # override contract.
    reflected = {(2 * ar - r, 2 * ac - c) for r, c in cells}
    if (
        len(cells) != n_cells
        or not _is_connected(cells)
        or any(not (0 <= r < h and 0 <= c < w) for r, c in cells)
        or any(not (0 <= r < h and 0 <= c < w) for r, c in reflected)
        or set(cells) & reflected
        or (ar, ac) in cells
        or (ar, ac) in reflected
    ):
        raise RuntimeError("internal point-reflection construction invariant failed")

    secondary_color = None
    if n_colors == 2:
        legal = [value for value in range(1, 9) if value != primary_color]
        secondary_color = layout_rng.choice(legal)

    grid = full_grid(h, w, 0)
    grid[ar][ac] = 9
    for index, (r, c) in enumerate(cells):
        # The reading-order first source cell always carries primary_color, so
        # observe_overrides can recover the exact requested value.  With two
        # colors, every later odd-indexed cell supplies the second color.
        color = (
            primary_color
            if secondary_color is None or index % 2 == 0
            else secondary_color
        )
        grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural gate for lawful point-reflection teaching inputs."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-ARC color"]

    h, w = len(grid), width
    errors: list[str] = []
    anchors = _anchor_cells(grid)
    cells = _blob_cells(grid)

    if len(anchors) != 1:
        errors.append(f"expected exactly one 9-anchor, got {len(anchors)}")
    if len(cells) not in (3, 4):
        errors.append(f"expected a 3-4 cell source object, got {len(cells)}")
    if cells and not _is_connected(cells):
        errors.append("source cells are not one 4-connected object")
    colors = {grid[r][c] for r, c in cells}
    if len(colors) not in (1, 2):
        errors.append(f"expected one or two source colors, got {len(colors)}")

    if len(anchors) == 1 and cells:
        ar, ac = anchors[0]
        cell_set = set(cells)
        reflected = set()
        for r, c in cells:
            rr, cc = 2 * ar - r, 2 * ac - c
            if not (0 <= rr < h and 0 <= cc < w):
                errors.append("a source cell reflects out of bounds")
                continue
            reflected.add((rr, cc))
            if (rr, cc) in cell_set:
                errors.append("source overlaps its point-reflected image")
            elif grid[rr][cc] != 0:
                errors.append("a reflected target is not blank")
        if len(reflected) != len(cells):
            errors.append("reflection is not one-to-one")
    return list(dict.fromkeys(errors))
