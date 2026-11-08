"""Generator for ARC task 448aa5bd80ad — marker-count-selected transform.

Count color-9 cells in row 0, erase those markers, crop the single colored
object below the blank separator row, then transform the crop: 1 marker rotates
90° clockwise, 2 markers rotate 180°, and 3 markers transpose the crop.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "448aa5bd80ad"
TASK_ID = "448aa5bd80ad"
VERSION = "4.0.0"
RULE_HASH = "b0b8c9f3ea53"  # sha256[:12] of whitespace-normalized canonical rule
SUMMARY = (
    "A black 7..14 by 7..14 grid has 1..3 maroon (9) selector cells in "
    "row 0, a blank separator row, and one 4-connected monochrome polyomino "
    "of 4..8 cells below it. Count the 9s, erase them, crop the polyomino, "
    "then apply 1=rotate clockwise, 2=rotate 180 degrees, 3=transpose. "
    "Object shape, position, size, selector positions, canvas dimensions, and "
    "color family vary independently; every selected transform changes the crop."
)
INVARIANTS = [
    "row 0 contains only background and exactly 1..3 color-9 selector cells",
    "row 1 is a blank separator and no color 9 occurs below row 0",
    "below the separator is exactly one monochrome 4-connected 2-D polyomino of 4..8 cells",
    "the selected transform is non-identity on the cropped polyomino",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
# Disjoint sets make palette_kind exactly recoverable from a returned grid and
# prevent a requested palette mode from silently collapsing to another mode.
PALETTE_COLORS = {
    "default": (4, 6),
    "warm": (2, 7),
    "cool": (1, 8),
    "varied": (3, 5),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-biased draw over 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-biased draw over 7..14",
        "valid": "7..14",
    },
    "n_nines": {
        "type": "int",
        "default": "uniform draw over 1..3 in every difficulty band",
        "valid": "1..3",
    },
    "blob_cells": {
        "type": "int",
        "default": "difficulty-biased draw over 4..8",
        "valid": "4..8",
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform draw",
        "valid": "|".join(PALETTE_KINDS),
    },
}

_ORTHOGONAL = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _norm_cells(cells):
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return sorted((row - row0, col - col0) for row, col in cells)


def _selected_transform_is_identity(cells, n_nines):
    normalized = _norm_cells(cells)
    source = set(normalized)
    max_row = max(row for row, _ in source)
    max_col = max(col for _, col in source)
    if n_nines == 1:
        transformed = [(col, max_row - row) for row, col in source]
    elif n_nines == 2:
        transformed = [(max_row - row, max_col - col) for row, col in source]
    else:
        transformed = [(col, row) for row, col in source]
    return set(_norm_cells(transformed)) == source


def _rand_poly(rng, size):
    cells = [(0, 0)]
    seen = {(0, 0)}
    while len(cells) < size:
        row, col = rng.choice(cells)
        dr, dc = rng.choice(_ORTHOGONAL)
        candidate = row + dr, col + dc
        if candidate not in seen:
            cells.append(candidate)
            seen.add(candidate)
    return _norm_cells(cells)


def _fallback_poly(size):
    """A connected, 2-D, transform-visible hook with exactly ``size`` cells."""
    return [(0, col) for col in range(size - 1)] + [(1, 0)]


def _shape_dims(cells):
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _palette_kind_for_color(color):
    matches = [kind for kind, colors in PALETTE_COLORS.items() if color in colors]
    return matches[0] if len(matches) == 1 else None


def _analyze(grid):
    errors: list[str] = []
    facts = {
        "grid_h": None,
        "grid_w": None,
        "n_nines": None,
        "blob_cells": None,
        "palette_kind": None,
        "blob_color": None,
        "blob_bbox": None,
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        return facts, ["grid must be a nonempty rectangular list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return facts, ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return facts, ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be literal ARC colors 0..9")

    height = len(grid)
    facts["grid_h"], facts["grid_w"] = height, width
    if not 7 <= height <= 14 or not 7 <= width <= 14:
        errors.append("grid dimensions must each be in 7..14")

    if any(value not in (0, 9) for value in grid[0]):
        errors.append("row 0 may contain only background 0 and selector color 9")
    n_nines = sum(value == 9 for value in grid[0])
    facts["n_nines"] = n_nines
    if n_nines not in (1, 2, 3):
        errors.append("row 0 must contain exactly 1..3 selector cells of color 9")

    if height > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")
    if any(value == 9 for row in grid[1:] for value in row):
        errors.append("selector color 9 may not occur below row 0")

    colored = [
        (row, col, value)
        for row in range(2, height)
        for col, value in enumerate(grid[row])
        if value != 0
    ]
    facts["blob_cells"] = len(colored)
    if not 4 <= len(colored) <= 8:
        errors.append("the body polyomino must contain 4..8 cells")
    if not colored:
        return facts, errors

    colors = {value for _, _, value in colored}
    if len(colors) != 1:
        errors.append("the body must use exactly one non-background color")
        return facts, errors
    color = next(iter(colors))
    facts["blob_color"] = color
    facts["palette_kind"] = _palette_kind_for_color(color)
    if facts["palette_kind"] is None:
        errors.append("body color must belong to exactly one declared palette family")

    cells = {(row, col) for row, col, _ in colored}
    seen = {next(iter(cells))}
    frontier = list(seen)
    while frontier:
        row, col = frontier.pop()
        for dr, dc in _ORTHOGONAL:
            neighbour = row + dr, col + dc
            if neighbour in cells and neighbour not in seen:
                seen.add(neighbour)
                frontier.append(neighbour)
    if seen != cells:
        errors.append("the body must be one 4-connected component")

    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    bbox_h, bbox_w = max_row - min_row + 1, max_col - min_col + 1
    facts["blob_bbox"] = [bbox_h, bbox_w]
    if bbox_h < 2 or bbox_w < 2:
        errors.append("the body must span at least two rows and two columns")
    if n_nines in (1, 2, 3):
        local = [(row - min_row, col - min_col) for row, col in cells]
        if _selected_transform_is_identity(local, n_nines):
            errors.append("the selected transform must change the cropped body")
    return facts, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    return _analyze(grid)[1]


def observe_overrides(grid) -> dict:
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_nines": facts["n_nines"],
        "blob_cells": facts["blob_cells"],
        "palette_kind": facts["palette_kind"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_diff("grid_h", 7, 14)
    width = ctx.draw_int_diff("grid_w", 7, 14)
    n_nines = ctx.draw_int("n_nines", 1, 3)
    blob_cells = ctx.draw_int_diff("blob_cells", 4, 8)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    blob_color = ctx.draw_choice("blob_color", PALETTE_COLORS[palette_kind])

    grid = full_grid(height, width, 0)
    marker_rng = ctx.draw_rng("selector_positions")
    marker_columns = list(range(width))
    marker_rng.shuffle(marker_columns)
    for col in marker_columns[:n_nines]:
        grid[0][col] = 9

    shape_rng = ctx.draw_rng("body_shape_and_position")
    cells = None
    for _ in range(512):
        candidate = _rand_poly(shape_rng, blob_cells)
        shape_h, shape_w = _shape_dims(candidate)
        if shape_h < 2 or shape_w < 2:
            continue
        if shape_h > height - 2 or shape_w > width:
            continue
        if _selected_transform_is_identity(candidate, n_nines):
            continue
        cells = candidate
        break
    if cells is None:
        candidate = _fallback_poly(blob_cells)
        shape_h, shape_w = _shape_dims(candidate)
        if shape_h > height - 2 or shape_w > width:
            raise ValueError(
                "declared grid dimensions cannot fit the requested body size"
            )
        if _selected_transform_is_identity(candidate, n_nines):
            raise ValueError("fallback body aliases the requested transform")
        cells = candidate

    shape_h, shape_w = _shape_dims(cells)
    row0 = shape_rng.randint(2, height - shape_h)
    col0 = shape_rng.randint(0, width - shape_w)
    for row, col in cells:
        grid[row0 + row][col0 + col] = blob_color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid lesson: " + "; ".join(errors))
    return grid
