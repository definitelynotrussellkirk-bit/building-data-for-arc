"""Inputs for 319f2597: clear original zero-bearing rows/columns, preserving 2.

Version 2 uses observable zero-row/column counts and total palette size.
Default lessons alternate rich separated-zero witnesses with canonical-profile
rectangles. Labels remain exclusively the selected canonical Racket authority.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx, stable_rng

GENERATOR_ID = "09636f05e06e"
TASK_ID = GENERATOR_ID
RULE_HASH = "53141d69f404"
VERSION = "2.0.0"
SUMMARY = "Clear rows or columns containing original zeros, preserving every color-2 cell."

INVARIANTS = [
    "rectangular 8..22 by 8..22 integer ARC grid; fixed cue 0 and protected color 2",
    "1..5 actual zero-bearing rows and columns, with zero-free rows and columns",
    "ordinary cells and protected 2s occur in both row-only and column-only arms",
    "ordinary untouched cells remain outside both zero-bearing row and column sets",
    "palette_size is the exact total number of colors, including 0 and 2",
]
POSITION_BIAS = ("center", "spread", "edge")
HELPFUL_TEXTURES = ("rectangle", "scatter", "single_zero")
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "20 in core profiles; weighted 8..22 otherwise", "valid": "8..22"},
    "grid_w": {"type": "int", "default": "20 in core profiles; weighted 8..22 otherwise", "valid": "8..22"},
    "n_zero_rows": {"type": "int", "default": "profile-dependent 1..5", "valid": "1..5",
                    "doc": "Exact number of original rows containing zero; not sprinkle-strip count."},
    "n_zero_cols": {"type": "int", "default": "profile-dependent 1..5", "valid": "1..5",
                    "doc": "Exact number of original columns containing zero."},
    "palette_size": {"type": "int", "default": "10 in core profiles; 3..10 otherwise", "valid": "3..10",
                     "doc": "Total distinct input colors, including 0 and 2."},
    "twos_density": {"type": "float", "default": "uniform 0.05..0.20", "valid": "0..0.4",
                     "doc": "Bernoulli probability on nonzero fill cells, before two protected-arm witnesses and ordinary/palette witnesses are planted; not an exact realized fraction."},
    "position_bias": {"type": "str", "default": "center|spread|edge", "valid": "center|spread|edge",
                      "doc": "Placement preference for the zero-support hull; edge includes the outermost row/column."},
    "texture": {"type": "str", "default": "rectangle or scatter by lesson profile", "valid": "rectangle|scatter|single_zero",
                "doc": "rectangle fills the Cartesian zero support; scatter covers the support with max(rows,cols) zeros; single_zero requires both counts 1."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "single_zero", "n_zero_rows": [2, 3, 4, 5]},
    {"texture": "single_zero", "n_zero_cols": [2, 3, 4, 5]},
]
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "scatter", "thin")


def schedule_profile(seed, sample_index, difficulty=None):
    """A seed-rotated period four; every five draws contain at least two scatter slots."""
    offset = stable_rng(seed, TASK_ID + "|lesson-phase", VERSION).randrange(4)
    return ("canonical", "scatter", "thin", "scatter")[(offset + sample_index) % 4]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        kind = AXES[name]["type"]
        if kind == "int" and type(value) is not int:
            raise ValueError(f"{name} requires an integer, not {type(value).__name__}")
        if kind == "float" and (isinstance(value, bool) or not isinstance(value, (int, float))
                                or not 0 <= value <= 0.4 or not math.isfinite(value)):
            raise ValueError("twos_density must be a finite number in [0, 0.4]")
        if kind == "str" and (not isinstance(value, str) or value not in AXES[name]["valid"].split("|")):
            raise ValueError(f"invalid {name}: {value!r}")
    if overrides.get("texture") == "single_zero":
        for axis in ("n_zero_rows", "n_zero_cols"):
            if overrides.get(axis) not in (None, 1):
                error = ValueError(f"single_zero is incompatible with {axis} != 1")
                error.incompatible_axes = ("texture", axis)
                raise error


def _integer(ctx, overrides, name, low, high, defaults):
    # All explicit values use the full declared domain in every band. Defaults
    # are recorded through the same public context; no draw is overwritten.
    options = list(range(low, high + 1)) if overrides.get(name) is not None else defaults
    return ctx.draw_choice(name, options)


def _start(length, span, bias, rng):
    last = length - span
    if bias == "edge":
        return rng.choice((0, last))
    if bias == "center":
        return rng.choice((last // 2, (last + 1) // 2))
    return rng.randrange(last + 1)


def _positions(length, count, texture, bias, rng):
    if texture != "scatter" or count == 1:
        first = _start(length, count, bias, rng)
        return list(range(first, first + count))
    # Endpoints plus random interior coordinates guarantee at least one gap,
    # while retaining nonuniform spacings and edge/interior placements.
    span = rng.randint(count + 1, length)
    first = _start(length, span, bias, rng)
    interior = rng.sample(range(1, span - 1), count - 2)
    return [first + x for x in sorted([0, span - 1, *interior])]


def _arm_pair(free, origin):
    """Near/far free coordinates on one side; at least three free positions exist."""
    above = sorted((x for x in free if x > origin))
    below = sorted((x for x in free if x < origin), reverse=True)
    choices = above if len(above) >= 2 else below
    return choices[0], choices[-1]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    core = profile != "scatter"
    favored = list(range(8, 13)) if difficulty == "easy" else list(range(16, 23)) if difficulty == "hard" else list(range(11, 19))
    size_defaults = [20] if core else list(range(8, 23)) + favored * 3
    h = _integer(ctx, overrides, "grid_h", 8, 22, size_defaults)
    w = _integer(ctx, overrides, "grid_w", 8, 22, size_defaults)
    palette_size = _integer(ctx, overrides, "palette_size", 3, 10, [10] if core else list(range(3, 11)))
    texture_options = HELPFUL_TEXTURES if overrides.get("texture") is not None else ["rectangle" if core else "scatter"]
    texture = ctx.draw_choice("texture", texture_options)
    bias = ctx.draw_choice("position_bias", POSITION_BIAS)
    if texture == "single_zero":
        row_defaults = col_defaults = [1]
    elif profile == "canonical":
        row_defaults = col_defaults = [2]
    elif profile == "thin":
        vertical = ctx.draw_choice("thin_direction", (False, True))
        row_defaults, col_defaults = ([4], [1]) if vertical else ([1], [4])
    else:
        row_defaults, col_defaults = [2, 3, 4, 5], None
    nr = _integer(ctx, overrides, "n_zero_rows", 1, 5, row_defaults)
    nc = _integer(ctx, overrides, "n_zero_cols", 1, 5, [nr] if col_defaults is None else col_defaults)
    layout = ctx.draw_rng("layout")
    active_rows = _positions(h, nr, texture, bias, layout)
    active_cols = _positions(w, nc, texture, bias, layout)
    if texture == "rectangle":
        zero_cells = {(r, c) for r in active_rows for c in active_cols}
    else:
        r_order, c_order = active_rows[:], active_cols[:]
        layout.shuffle(r_order)
        layout.shuffle(c_order)
        zero_cells = {(r_order[i % nr], c_order[i % nc]) for i in range(max(nr, nc))}
    colors = ctx.draw_distinct_colors("ordinary_colors", n=palette_size - 2, exclude=(0, 2))
    probability = overrides.get("twos_density")
    if probability is None:
        probability = ctx.draw_rng("twos_density").uniform(0.05, 0.20)
    fill = ctx.draw_rng("fill")
    grid = [[fill.choice(colors) for _ in range(w)] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if (r, c) in zero_cells:
                grid[r][c] = 0
            elif fill.random() < probability:
                grid[r][c] = 2
    free_rows = [r for r in range(h) if r not in active_rows]
    free_cols = [c for c in range(w) if c not in active_cols]
    zr, zc = layout.choice(sorted(zero_cells))
    near_c, far_c = _arm_pair(free_cols, zc)
    near_r, far_r = _arm_pair(free_rows, zr)
    grid[zr][near_c] = grid[near_r][zc] = 2
    grid[zr][far_c] = grid[far_r][zc] = colors[0]
    # An untouched cell inside a row-support gap refutes filling the global hull.
    gaps = [r for r in free_rows if min(active_rows) < r < max(active_rows)]
    if gaps:
        grid[layout.choice(gaps)][layout.choice(free_cols)] = colors[0]
    # Plant each palette representative last. All are ordinary colors, so this
    # preserves the gap witness without erasing a color's final occurrence.
    outside = [(r, c) for r in free_rows for c in free_cols]
    for (r, c), color in zip(layout.sample(outside, len(colors)), colors):
        grid[r][c] = color
    return grid


def _support(grid):
    points = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0}
    return points, {r for r, c in points}, {c for r, c in points}


def observe_overrides(grid):
    _, rows, cols = _support(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_zero_rows": len(rows), "n_zero_cols": len(cols),
            "palette_size": len({v for row in grid for v in row})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer ARC colors 0..9, excluding booleans"]
    if not (8 <= len(grid) <= 22 and 8 <= len(grid[0]) <= 22):
        return ["grid dimensions must each be in 8..22"]
    _, rows, cols = _support(grid)
    if not (1 <= len(rows) <= 5 and 1 <= len(cols) <= 5):
        return ["need 1..5 actual zero-bearing rows and columns"]
    messages = []
    for label, region in (
        ("row-only", [grid[r][c] for r in rows for c in range(len(grid[0])) if c not in cols]),
        ("column-only", [grid[r][c] for r in range(len(grid)) if r not in rows for c in cols]),
    ):
        if 2 not in region or not any(v not in (0, 2) for v in region):
            messages.append(f"{label} arm must show both an erased ordinary cell and a preserved 2")
    if not any(v not in (0, 2) for r, row in enumerate(grid) for c, v in enumerate(row)
               if r not in rows and c not in cols):
        messages.append("need an ordinary untouched cell outside the zero-bearing lines")
    return messages


def strict_canonical_like(grid):
    """Semantic task domain, including all original pairs; profile size is checked separately."""
    return self_check(grid)


# These functions are deliberately incorrect competitors, never label authority.
def _paint_rival(grid, rows, cols, *, intersection=False, preserve=True):
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            touched = (r in rows and c in cols) if intersection else (r in rows or c in cols)
            if touched and (value != 2 or not preserve):
                out[r][c] = 0
    return out


def _hull(grid):
    _, rows, cols = _support(grid)
    return _paint_rival(grid, range(min(rows), max(rows) + 1) if rows else (),
                        range(min(cols), max(cols) + 1) if cols else ())


def _threshold(grid):
    points, rows, cols = _support(grid)
    return _paint_rival(grid, {r for r in rows if sum(rr == r for rr, cc in points) >= 2},
                        {c for c in cols if sum(cc == c for rr, cc in points) >= 2})


def _block_cells(grid):
    points, _, _ = _support(grid)
    supported = set()
    for r, c in points:
        block = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
        if block <= points:
            supported.update(block)
    return supported


def _blocks_only(grid):
    block = _block_cells(grid)
    return _paint_rival(grid, {r for r, c in block}, {c for r, c in block})


def _block_gate(grid):
    if not _block_cells(grid):
        return [list(row) for row in grid]
    _, rows, cols = _support(grid)
    return _paint_rival(grid, rows, cols)


def _component(grid, *, largest=False):
    points, _, _ = _support(grid)
    components = []
    while points:
        start = min(points)
        points.remove(start)
        part, queue = {start}, [start]
        while queue:
            r, c = queue.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in points:
                    points.remove(point)
                    part.add(point)
                    queue.append(point)
        components.append(part)
    chosen = max(components, key=len) if largest and components else components[0] if components else set()
    return _paint_rival(grid, {r for r, c in chosen}, {c for r, c in chosen})


def _largest_component(grid):
    return _component(grid, largest=True)


def _fixed_two(grid):
    _, rows, cols = _support(grid)
    return _paint_rival(grid, range(min(rows), min(rows) + 2) if rows else (),
                        range(min(cols), min(cols) + 2) if cols else ())


def _row_only(grid):
    return _paint_rival(grid, _support(grid)[1], ())


def _column_only(grid):
    return _paint_rival(grid, (), _support(grid)[2])


def _intersection(grid):
    _, rows, cols = _support(grid)
    return _paint_rival(grid, rows, cols, intersection=True)


def _global_erase(grid):
    return _paint_rival(grid, range(len(grid)) if _support(grid)[0] else (), ())


def _erase_twos(grid):
    _, rows, cols = _support(grid)
    return _paint_rival(grid, rows, cols, preserve=False)


def _stop_at_two(grid):
    points, _, _ = _support(grid)
    out = [list(row) for row in grid]
    for r, c in points:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            while 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                if grid[rr][cc] == 2:
                    break
                out[rr][cc] = 0
                rr, cc = rr + dr, cc + dc
    return out


CANONICAL_SHORTCUTS = {
    "global_zero_hull": _hull,
    "at_least_two_zeros_per_line": _threshold,
    "only_zeros_in_2x2_blocks": _blocks_only,
    "requires_any_2x2_block": _block_gate,
    "first_zero_component": _component,
    "largest_zero_component": _largest_component,
    "fixed_two_wide_from_min_zero": _fixed_two,
}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS, row_only=_row_only, column_only=_column_only,
                       row_column_intersection=_intersection, global_erase=_global_erase,
                       erase_twos_too=_erase_twos, rays_stop_at_two=_stop_at_two)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rich_witness(grid):
    points, rows, cols = _support(grid)
    if not (len(points) == len(rows) == len(cols) >= 2):
        return False
    if max(rows) - min(rows) + 1 <= len(rows) or max(cols) - min(cols) + 1 <= len(cols):
        return False
    if self_check(grid):
        return False
    return any(v not in (0, 2) for r, row in enumerate(grid) for c, v in enumerate(row)
               if min(rows) < r < max(rows) and r not in rows and c not in cols)


SEMANTIC_WITNESSES = {"isolated_zeros_with_gaps": _rich_witness}
WITNESS_RIVALS = {"isolated_zeros_with_gaps": list(SEMANTIC_RIVALS)}


def lesson_identifiable(demos, query):
    """Reject a query-changing declared rival that survives all supplied labels."""
    return [f"demonstrations do not refute {name} for this query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
