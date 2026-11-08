"""Input sampler for ARC task 96d4a788da47: slide each object left.

The selected Racket rule extracts every monochromatic connected object and
translates it horizontally by its own minimum column so that its bounding box
touches column 0.  Rows, colors, cell counts, and internal shapes are preserved.
Outputs are generated only by the canonical authority; this module samples
lawful, teachable inputs and declares one canonical-fitting shortcut.
"""
from __future__ import annotations

from itertools import product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96d4a788da47"
TASK_ID = GENERATOR_ID
RULE_HASH = "da14dfe7467e"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "Two or three differently colored 4-connected objects occupy disjoint row "
    "bands and begin strictly right of column 0.  Every sample contains a "
    "nonrectangular object so demonstrations teach that each object moves to "
    "the left border without changing its rows or internal shape."
)

INVARIANTS = [
    "background is color 0; every other color forms exactly one 4-connected object",
    "there are exactly 2 or 3 objects, each with 1..6 cells and a distinct color",
    "every object's bounding-box left column is at least 1, so every object moves",
    "object row spans are separated by at least one blank row, so outputs cannot collide",
    "every generated input contains at least one nonrectangular object",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile/broad mixture over 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile/broad mixture over 8..14",
        "valid": "8..14",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-weighted 2..3",
        "valid": "2..3",
    },
}
# All 8*7*2 advertised products are constructively supported in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Normalized connected polyominoes.  Width <= 4, height <= 3, size <= 6.
# Filled rectangles remain in the distribution, while the generator explicitly
# chooses at least one nonrectangle in every scene.
_SHAPES = (
    # height 1
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3)),
    # height 2
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    # height 3
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
)

_CANONICAL_PROFILES = (
    (7, 9, 2),
    (8, 10, 3),
    (9, 10, 3),
)


def _shape_height(shape) -> int:
    return max(r for r, _ in shape) + 1


def _shape_width(shape) -> int:
    return max(c for _, c in shape) + 1


def _is_filled_rectangle(cells) -> bool:
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return len(cells) == (r1 - r0 + 1) * (c1 - c0 + 1)


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (7, 14), "grid_w": (8, 14), "n_blobs": (2, 3)}
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = bounds[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}] (not bool)")


def _weighted_axis(ctx, name: str, lo: int, hi: int, *, anchor: int, core: bool):
    """Draw from the full public domain while favoring one correlated anchor."""
    options = list(range(lo, hi + 1))
    if core:
        options.extend([anchor] * 96)
    elif ctx.difficulty == "easy":
        midpoint = (lo + hi) // 2
        options.extend(range(lo, midpoint + 1))
    elif ctx.difficulty == "hard":
        midpoint = (lo + hi + 1) // 2
        options.extend(range(midpoint, hi + 1))
    return ctx.draw_choice(name, options)


def _height_tuple(ctx, h: int, n: int, *, core: bool):
    feasible = [
        heights
        for heights in product((1, 2, 3), repeat=n)
        if sum(heights) + (n - 1) <= h and max(heights) >= 2
    ]
    if not feasible:
        raise ValueError(f"no row-band construction for h={h}, n_blobs={n}")
    options = list(feasible)
    canonical = (2, 2) if n == 2 else (2, 2, 1)
    if core and canonical in feasible:
        options.extend([canonical] * 48)
    if ctx.difficulty == "easy":
        smallest = min(sum(item) for item in feasible)
        options.extend(item for item in feasible if sum(item) == smallest)
    elif ctx.difficulty == "hard":
        largest = max(sum(item) for item in feasible)
        options.extend(item for item in feasible if sum(item) == largest)
    return ctx.draw_rng("row_band_heights").choice(options)


def _row_starts(ctx, h: int, heights):
    n = len(heights)
    spare = h - sum(heights) - (n - 1)
    gaps = [0] + [1] * (n - 1) + [0]
    rng = ctx.draw_rng("row_gap_distribution")
    for _ in range(spare):
        gaps[rng.randrange(n + 1)] += 1
    starts = []
    row = gaps[0]
    for index, height in enumerate(heights):
        starts.append(row)
        row += height
        if index < n - 1:
            row += gaps[index + 1]
    return starts


def _choose_shape(ctx, index: int, height: int, *, require_nonrectangle: bool):
    candidates = [shape for shape in _SHAPES if _shape_height(shape) == height]
    if require_nonrectangle:
        candidates = [shape for shape in candidates if not _is_filled_rectangle(shape)]
    if not candidates:
        raise ValueError(f"no shape candidate for height={height}")
    weighted = list(candidates)
    if ctx.difficulty == "easy":
        weighted.extend(shape for shape in candidates if len(shape) <= 4)
    elif ctx.difficulty == "hard":
        weighted.extend(shape for shape in candidates if len(shape) >= 5)
    shape = ctx.draw_rng(f"shape_{index}").choice(weighted)
    if ctx.draw_rng(f"shape_reflect_{index}").randrange(2):
        width = _shape_width(shape)
        shape = tuple(sorted((r, width - 1 - c) for r, c in shape))
    return shape


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    core = ctx.draw_choice("curriculum_profile", ("core", "broad")) == "core"
    profile = ctx.draw_rng("canonical_profile").choice(_CANONICAL_PROFILES)
    h = _weighted_axis(ctx, "grid_h", 7, 14, anchor=profile[0], core=core)
    w = _weighted_axis(ctx, "grid_w", 8, 14, anchor=profile[1], core=core)
    n = _weighted_axis(ctx, "n_blobs", 2, 3, anchor=profile[2], core=core)

    heights = list(_height_tuple(ctx, h, n, core=core))
    # Select a row band of height >=2 for the mandatory nonrectangular witness.
    witness_choices = [i for i, height in enumerate(heights) if height >= 2]
    witness_index = ctx.draw_rng("shape_witness_band").choice(witness_choices)
    starts = _row_starts(ctx, h, heights)
    colors = ctx.draw_distinct_colors("object_colors", n=n, exclude={0})

    grid = full_grid(h, w, 0)
    for index, (row0, height, color) in enumerate(zip(starts, heights, colors)):
        shape = _choose_shape(
            ctx,
            index,
            height,
            require_nonrectangle=index == witness_index,
        )
        width = _shape_width(shape)
        col0 = ctx.draw_rng(f"object_col_{index}").randint(1, w - width)
        for dr, dc in shape:
            r, c = row0 + dr, col0 + dc
            if grid[r][c] != 0:
                raise RuntimeError("constructive row-band placement collided")
            grid[r][c] = color
    return grid


def _coerce_grid(grid) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    rows = []
    width = None
    for row in grid:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError("expected nonempty list/tuple rows")
        values = list(row)
        if width is None:
            width = len(values)
        elif len(values) != width:
            raise ValueError("ragged grid")
        if any(type(value) is not int or not 0 <= value <= 9 for value in values):
            raise ValueError("cells must be integer ARC colors 0..9 (not bool)")
        rows.append(values)
    return rows


def _components_by_color(grid):
    rows = _coerce_grid(grid)
    h, w = len(rows), len(rows[0])
    by_color = {}
    for r, row in enumerate(rows):
        for c, color in enumerate(row):
            if color:
                by_color.setdefault(color, set()).add((r, c))

    components = []
    for color in sorted(by_color):
        remaining = set(by_color[color])
        color_components = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            stack = [start]
            cells = [start]
            while stack:
                r, c = stack.pop()
                for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if point in remaining:
                        remaining.remove(point)
                        stack.append(point)
                        cells.append(point)
            color_components.append(tuple(sorted(cells)))
        if len(color_components) != 1:
            raise ValueError(
                f"color {color} must form exactly one 4-connected object, "
                f"found {len(color_components)}"
            )
        components.append((color, color_components[0]))
    return rows, components


def _inspect(grid):
    rows, components = _components_by_color(grid)
    h, w = len(rows), len(rows[0])
    if not 7 <= h <= 14 or not 8 <= w <= 14:
        raise ValueError(f"expected dimensions within 7..14 by 8..14, got {h}x{w}")
    if not 2 <= len(components) <= 3:
        raise ValueError(f"expected 2 or 3 objects, found {len(components)}")

    intervals = []
    for color, cells in components:
        size = len(cells)
        if not 1 <= size <= 6:
            raise ValueError(f"color {color} object size {size} outside 1..6")
        rows_used = [r for r, _ in cells]
        cols_used = [c for _, c in cells]
        r0, r1 = min(rows_used), max(rows_used)
        c0, c1 = min(cols_used), max(cols_used)
        if c0 == 0:
            raise ValueError(f"color {color} object already touches column 0")
        if r1 - r0 + 1 > 3 or c1 - c0 + 1 > 4:
            raise ValueError(f"color {color} object bbox exceeds declared 3x4 support")
        intervals.append((r0, r1, color))

    intervals.sort()
    for (_, previous_end, previous_color), (next_start, _, next_color) in zip(
        intervals, intervals[1:]
    ):
        if next_start <= previous_end + 1:
            raise ValueError(
                f"object row bands for colors {previous_color} and {next_color} "
                "must have at least one blank row between them"
            )
    return rows, components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        _inspect(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid) -> dict[str, int]:
    rows, components = _inspect(grid)
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "n_blobs": len(components),
    }


def strict_canonical_like(grid):
    """Return diagnostics for inputs outside this task's declared manifold."""
    return self_check(grid)


def _bbox_fill_left(grid):
    """Rival: move each object's filled bounding rectangle to the left edge."""
    rows, components = _inspect(grid)
    out = full_grid(len(rows), len(rows[0]), 0)
    for color, cells in components:
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        width = c1 - c0 + 1
        for r in range(r0, r1 + 1):
            for c in range(width):
                if out[r][c] not in (0, color):
                    raise ValueError("rival rectangles collide")
                out[r][c] = color
    return out


def _has_nonrectangular_object(grid) -> bool:
    try:
        _, components = _inspect(grid)
    except (TypeError, ValueError):
        return False
    return any(not _is_filled_rectangle(cells) for _, cells in components)


SEMANTIC_WITNESSES = {"shape_preservation": _has_nonrectangular_object}
SEMANTIC_RIVALS = {"bbox_fill_left": _bbox_fill_left}
WITNESS_RIVALS = {"shape_preservation": ["bbox_fill_left"]}
CANONICAL_SHORTCUTS = {"bbox_fill_left": _bbox_fill_left}
LESSON_COMPETITORS = {"bbox_fill_left": _bbox_fill_left}
