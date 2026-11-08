"""Inputs for adding a cyan global bounding-box perimeter, preserving sources.

The canonical Racket program owns labels. Four exact controls are measured from
pixels. Alternating sparse and distributed-extrema pairs teach why all source
cells matter; no generated grid or canonical answer is replayed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a5bda33d14a0"
TASK_ID = GENERATOR_ID
VERSION = "2.0.1"
RULE_HASH = "eb3c0d7afaf9"
SUMMARY = "Fill zero cells on the global nonzero bounding-box perimeter with 8; preserve all sources."

INVARIANTS = [
    "rectangular integer grid, 4..18 rows and columns, background 0",
    "3..12 source cells from colors 1..7 or 9; 1..8 distinct source colors",
    "global source bounding box is at least 3 by 3",
    "at least one empty perimeter cell and one empty interior cell",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-shaped or 4..18", "valid": "4..18"},
    "grid_w": {"type": "int", "default": "canonical-shaped or 4..18", "valid": "4..18"},
    "n_cells": {"type": "int", "default": "3 sparse; 4..12 distributed", "valid": "3..12"},
    "n_distinct_colors": {"type": "int", "default": "4 sparse; 2..9 distributed, including 0", "valid": "2..9"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_LIMITS = {"grid_h": (4, 18), "grid_w": (4, 18),
           "n_cells": (3, 12), "n_distinct_colors": (2, 9)}
_CANONICAL_SHAPES = ((8, 10), (9, 9), (7, 11), (10, 8), (8, 12))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("sparse", "distributed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Every four consecutive positions contain two pairs of each profile."""
    return "sparse" if (seed + sample_index) % 4 < 2 else "distributed"


def _axis(ctx, name, choices):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, *_LIMITS[name])
    return ctx.draw_choice(name, choices)


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _LIMITS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    count = overrides.get("n_cells")
    colors = overrides.get("n_distinct_colors")
    if count is not None and colors is not None and colors > count + 1:
        error = ValueError("n_distinct_colors includes 0 and cannot exceed n_cells + 1")
        error.incompatible_axes = ("n_cells", "n_distinct_colors")
        raise error


def _validate_request(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool, float or string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium or hard")


def _positions(ctx, h, w, count, distributed):
    rng = ctx.draw_rng("layout")
    # Distributed boxes reserve all four corners and one interior zero. With
    # no occupied corners, any three source points miss at least one extremum.
    # Only explicitly dense/small override combinations need the general path.
    distributed = distributed and h * w - 5 >= count
    reserved = 5 if distributed else 2
    sizes = [(bh, bw) for bh in range(3, h + 1) for bw in range(3, w + 1)
             if bh * bw - reserved >= count]
    if not distributed:
        # Ordinary sparse teaching pairs distinguish the source box from the
        # canvas boundary. Dense explicit overrides can still require a full box.
        inset_sizes = [(bh, bw) for bh, bw in sizes if bh < h or bw < w]
        sizes = inset_sizes or sizes
    bh, bw = rng.choice(sizes)
    mr, mc = rng.randrange(1, bh - 1), rng.randrange(1, bw - 1)
    hole = (mr, mc)
    if distributed:
        cells = {(0, mc), (bh - 1, mc), (mr, 0), (mr, bw - 1)}
        blocked = {(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1), hole}
    else:
        cells = {(0, 0), (bh - 1, mc), (mr, bw - 1)}
        blocked = {hole, (0, bw - 1)}
        # A minority retains opposite corners, so the repair does not replace
        # the old forced layout by an equally absolute corner-avoidance rule.
        interior = [(r, c) for r in range(1, bh - 1) for c in range(1, bw - 1)
                    if (r, c) != hole]
        if interior and rng.randrange(3) == 0:
            cells = {(0, 0), (bh - 1, bw - 1), rng.choice(interior)}
    available = [(r, c) for r in range(bh) for c in range(bw)
                 if (r, c) not in cells and (r, c) not in blocked]
    cells.update(rng.sample(available, count - len(cells)))
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    top, left = rng.randrange(h - bh + 1), rng.randrange(w - bw + 1)
    return sorted((top + (bh - 1 - r if flip_r else r),
                   left + (bw - 1 - c if flip_c else c)) for r, c in cells)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    sparse = schedule_profile(seed, sample_index, difficulty) == "sparse"
    shape = ctx.draw_choice("canonical_shape", _CANONICAL_SHAPES)
    if sparse:
        heights, widths = (shape[0],), (shape[1],)
    else:
        favored = list(range(4, 11)) if difficulty == "easy" else list(range(10, 19))
        heights = widths = list(range(4, 19)) + favored
    h = _axis(ctx, "grid_h", heights)
    w = _axis(ctx, "grid_w", widths)
    requested_colors = overrides.get("n_distinct_colors")
    minimum = max(3, (requested_colors or 2) - 1)
    maximum = min(12, h * w - 5)
    choices = (3,) if sparse and minimum == 3 else tuple(range(max(4, minimum), maximum + 1))
    count = _axis(ctx, "n_cells", choices)
    color_choices = (4,) if sparse else tuple(range(2, min(9, count + 1) + 1))
    n_colors = _axis(ctx, "n_distinct_colors", color_choices)
    # A lone color-count override expands the default count before layout;
    # two incompatible exact requests have already failed with their axes.
    if n_colors > count + 1:
        raise RuntimeError("internal palette/count inconsistency")
    cells = _positions(ctx, h, w, count, distributed=(not sparse and count >= 4))
    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(_COLORS, n_colors - 1)
    assignment = list(palette)
    assignment.extend(palette_rng.choice(palette) for _ in range(count - len(palette)))
    palette_rng.shuffle(assignment)
    grid = full_grid(h, w, 0)
    for (r, c), color in zip(cells, assignment):
        grid[r][c] = color
    return grid


def _sources(grid):
    return [(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color != 0]


def _box(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_cells": sum(color != 0 for row in grid for color in row),
            "n_distinct_colors": len({color for row in grid for color in row})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(color) is not int or color not in (0, *_COLORS) for row in grid for color in row):
        return ["cells must be integer colors 0..9 excluding the output color 8"]
    if not (4 <= len(grid) <= 18 and 4 <= len(grid[0]) <= 18):
        return ["canvas outside the declared 4..18 dimension range"]
    cells = _sources(grid)
    if not 3 <= len(cells) <= 12:
        return ["expected 3..12 nonzero source cells"]
    r0, c0, r1, c1 = _box(cells)
    if r1 - r0 < 2 or c1 - c0 < 2:
        return ["source box must be at least 3 by 3"]
    errors = []
    if not any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
               if r in (r0, r1) or c in (c0, c1)):
        errors.append("no empty perimeter cell: identity example")
    if not any(grid[r][c] == 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)):
        errors.append("no empty interior cell to distinguish border from filled box")
    return errors


def strict_canonical_like(grid):
    """Task-domain geometry, not a test for a particular canvas or palette."""
    return self_check(grid)


def _rival_paint(grid, cells, *, fill=False, overwrite=False):
    """Shared mechanics for explicit rival hypotheses, never training labels."""
    out = [list(row) for row in grid]
    if not cells:
        return out
    r0, c0, r1, c1 = _box(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if (fill or r in (r0, r1) or c in (c0, c1)) and (overwrite or out[r][c] == 0):
                out[r][c] = 8
    return out


def _first_three(grid):
    return _rival_paint(grid, _sources(grid)[:3])


def _row_endpoints(grid):
    cells = _sources(grid)
    return _rival_paint(grid, [cells[0], cells[-1]] if cells else [])


def _filled_box(grid):
    return _rival_paint(grid, _sources(grid), fill=True)


def _overwrite_border(grid):
    return _rival_paint(grid, _sources(grid), overwrite=True)


def _canvas_border(grid):
    return _rival_paint(grid, [(0, 0), (len(grid) - 1, len(grid[0]) - 1)])


def _four_side_extrema(grid):
    r0, c0, r1, c1 = _box(_sources(grid))
    return all(grid[r][c] == 0 for r, c in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)))


def _empty_interior(grid):
    r0, c0, r1, c1 = _box(_sources(grid))
    return any(grid[r][c] == 0 for r in range(r0 + 1, r1) for c in range(c0 + 1, c1))


def _perimeter_sources(grid):
    return bool(_sources(grid))


SEMANTIC_RIVALS = {"first_three": _first_three, "row_endpoints": _row_endpoints,
                   "filled_box": _filled_box, "overwrite_border": _overwrite_border,
                   "canvas_border": _canvas_border}
SEMANTIC_WITNESSES = {"four_side_extrema": _four_side_extrema,
                      "empty_interior": _empty_interior,
                      "perimeter_sources": _perimeter_sources}
WITNESS_RIVALS = {"four_side_extrema": ["first_three"],
                  "empty_interior": ["filled_box"],
                  "perimeter_sources": ["overwrite_border"]}
CANONICAL_SHORTCUTS = {"first_three": _first_three}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
