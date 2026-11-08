"""Generator for acb1cae24892 — connect two same-color endpoints.

For each nonzero color, the two cells are interpreted as the opposite corners
of an axis-aligned bounding rectangle.  The reference paints that rectangle's
outline; same-row and same-column pairs are the corresponding degenerate cases.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "acb1cae24892"
TASK_ID = "acb1cae24892"
VERSION = "2.0.0"
RULE_HASH = "89b3f3e5cc80"
SUMMARY = (
    "One to three colors each appear exactly twice. Their two endpoints define "
    "a row segment, column segment, or rectangle outline."
)

INVARIANTS = [
    "background is 0",
    "1..3 distinct nonzero colors, each with exactly two endpoints",
    "each pair has a visible row, column, or rectangular span",
    "different pairs use disjoint endpoint rows and columns",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware 7..14", "valid": "7..14"},
    "n_colors": {"type": "int", "default": "difficulty-aware 1..3", "valid": "1..3"},
}
_ALLOWED_OVERRIDES = frozenset(AXES)


def _strict_int(overrides, name: str, low: int, high: int):
    value = overrides.get(name)
    if value is None:
        return None
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unsupported override(s): {', '.join(unknown)}")
    _strict_int(overrides, "grid_h", 7, 14)
    _strict_int(overrides, "grid_w", 7, 14)
    _strict_int(overrides, "n_colors", 1, 3)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 7, 14)
    w = ctx.draw_int_diff("grid_w", 7, 14)
    n = ctx.draw_int_diff("n_colors", 1, 3)
    colors = list(ctx.draw_distinct_colors("pair_colors", n=n, exclude={0}))
    rng = ctx.draw_rng("layout")
    rng.shuffle(colors)

    row_pairs = [(i, h - 1 - i) for i in range(n)]
    col_pairs = [(i, w - 1 - i) for i in range(n)]
    pair_order = list(range(n))
    rng.shuffle(pair_order)
    modes = ("row", "col", "rect")
    grid = full_grid(h, w, 0)
    for position, pair_index in enumerate(pair_order):
        color = colors[position]
        r0, r1 = row_pairs[pair_index]
        c0, c1 = col_pairs[pair_index]
        mode = modes[(sample_index + position) % len(modes)]
        if mode == "row":
            points = ((r0, c0), (r0, c1))
        elif mode == "col":
            points = ((r0, c0), (r1, c0))
        else:
            points = ((r0, c0), (r1, c1))
        for r, c in points:
            if grid[r][c] != 0:
                raise RuntimeError("constructive pair placement overlapped")
            grid[r][c] = color
    return [row[:] for row in grid]


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len({v for row in grid for v in row if v != 0}),
    }


def rule_mirror(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = []
    for row in grid:
        for value in row:
            if value != 0 and value not in colors:
                colors.append(value)
    for color in colors:
        points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        lo_r, hi_r = sorted((r0, r1))
        lo_c, hi_c = sorted((c0, c1))
        for r in range(lo_r, hi_r + 1):
            for c in range(lo_c, hi_c + 1):
                if r in (lo_r, hi_r) or c in (lo_c, hi_c):
                    out[r][c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    h = len(grid)
    errors = []
    if not 1 <= h <= 30 or not 1 <= w <= 30:
        errors.append(f"grid dimensions must be in 1..30, got {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be exact ARC integers 0..9")
        return errors

    cells_by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                cells_by_color.setdefault(value, []).append((r, c))
    if not 1 <= len(cells_by_color) <= 3:
        errors.append(f"expected 1..3 endpoint colors, got {len(cells_by_color)}")
    used_rows, used_cols = set(), set()
    for color, cells in sorted(cells_by_color.items()):
        if len(cells) != 2:
            errors.append(f"color {color} has {len(cells)} endpoints; expected 2")
            continue
        (r0, c0), (r1, c1) = cells
        if r0 == r1 and abs(c1 - c0) < 2:
            errors.append(f"color {color} row endpoints are adjacent")
        elif c0 == c1 and abs(r1 - r0) < 2:
            errors.append(f"color {color} column endpoints are adjacent")
        elif r0 != r1 and c0 != c1 and (abs(r1 - r0) < 2 or abs(c1 - c0) < 2):
            errors.append(f"color {color} rectangle span is too small")
        rows, cols = {r0, r1}, {c0, c1}
        if used_rows & rows or used_cols & cols:
            errors.append(f"color {color} shares an endpoint row or column")
        used_rows |= rows
        used_cols |= cols

    requested = {}
    if isinstance(meta, dict):
        if isinstance(meta.get("overrides"), dict):
            requested.update(meta["overrides"])
        for axis in AXES:
            if axis in meta:
                requested[axis] = meta[axis]
    if requested:
        observed = observe_overrides(grid)
        for axis, expected in requested.items():
            if axis in observed and observed[axis] != expected:
                errors.append(f"{axis} requested {expected!r}, observed {observed[axis]!r}")
    return errors

def strict_canonical_like(grid):
    """Expose the selected structural grammar to the semantic review gate."""
    return self_check(grid)

