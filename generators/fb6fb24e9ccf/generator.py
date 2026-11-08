"""Generator for arc_puzzle_bank_eighteenth_21_bundle:easy_125_crop_the_nonzero_bounding_box.

Rule: crop the grid to the minimal bounding box containing every nonzero cell.

Combinatorial axes (6): grid_h, grid_w, bbox_h, bbox_w, n_components,
n_distinct_colors.  The four-step sample-index schedule guarantees that a
normal four-demonstration lesson includes a connected monochrome crop, a
connected multicolor crop, a disconnected joint-bbox crop, and a second
multicolor crop at different positions and sizes.

Named degenerates: no_motif, full_grid_motif, solid_bbox, three_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fb6fb24e9ccf"
VERSION = "4.0.0"  # exact observable axes + branch-complete four-demo schedule
TASK_ID = "fb6fb24e9ccf"
RULE_HASH = "debb1a8a129a"

SUMMARY = (
    "A zero-background grid contains one or two nonzero components inside a "
    "larger frame. The answer is the tight joint bounding-box crop of every "
    "nonzero cell, preserving colors, interior zero holes, and any gap between "
    "disconnected components."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and the nonzero palette has one to three colors",
    "the nonzero union has exactly one or two 4-connected components",
    "the tight nonzero bounding box is at least 2x2 and contains a zero hole",
    "there is at least one all-background margin cell on every side of the bbox",
    "output is exactly the joint nonzero bounding-box crop, including holes and gaps",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed", "valid": "5..20"},
    "grid_w": {"type": "int", "default": "difficulty-skewed", "valid": "5..22"},
    "bbox_h": {"type": "int", "default": "difficulty-skewed", "valid": "2..8"},
    "bbox_w": {"type": "int", "default": "difficulty-skewed", "valid": "2..8"},
    "n_components": {"type": "int", "default": "sample schedule", "valid": "1..2"},
    "n_distinct_colors": {"type": "int", "default": "sample schedule", "valid": "1..3"},
}

DEGENERATE_TEXTURES = (
    "no_motif",
    "full_grid_motif",
    "solid_bbox",
    "three_components",
)

_COLOR_POOL = (2, 3, 4, 5, 7, 8, 9)


def _neighbors(cell, h, w):
    r, c = cell
    return [
        (nr, nc)
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))
        if 0 <= nr < h and 0 <= nc < w
    ]


def _grow_from_seed(h, w, start, rng, target):
    """Return one connected set of exactly ``target`` cells."""
    cells = {start}
    frontier = set(_neighbors(start, h, w))
    while len(cells) < target:
        choices = sorted(frontier)
        if not choices:
            raise ValueError("connected growth exhausted before target size")
        nxt = rng.choice(choices)
        frontier.remove(nxt)
        cells.add(nxt)
        frontier.update(p for p in _neighbors(nxt, h, w) if p not in cells)
    return cells


def _one_component_cells(bh, bw, rng):
    """Connected corner-L backbone plus random growth, never a solid bbox."""
    orientation = rng.randrange(4)
    if orientation == 0:
        cells = {(0, c) for c in range(bw)} | {(r, 0) for r in range(bh)}
    elif orientation == 1:
        cells = {(0, c) for c in range(bw)} | {(r, bw - 1) for r in range(bh)}
    elif orientation == 2:
        cells = {(bh - 1, c) for c in range(bw)} | {(r, 0) for r in range(bh)}
    else:
        cells = {(bh - 1, c) for c in range(bw)} | {(r, bw - 1) for r in range(bh)}

    max_cells = bh * bw - 1
    lo = len(cells)
    hi = max(lo, min(max_cells, (bh * bw * 3) // 4))
    target = rng.randint(lo, hi)
    frontier = {
        p
        for cell in cells
        for p in _neighbors(cell, bh, bw)
        if p not in cells
    }
    while len(cells) < target:
        choices = sorted(frontier)
        if not choices:
            break
        nxt = rng.choice(choices)
        frontier.remove(nxt)
        cells.add(nxt)
        frontier.update(p for p in _neighbors(nxt, bh, bw) if p not in cells)
    return cells


def _two_component_cells(bh, bw, rng):
    """Two corner-grown components separated by an empty row and column."""
    candidates = []
    for gap_r in range(1, bh - 1):
        for gap_c in range(1, bw - 1):
            ah, aw = gap_r, gap_c
            ch, cw = bh - gap_r - 1, bw - gap_c - 1
            if ah * aw >= 2 and ch * cw >= 2:
                candidates.append((gap_r, gap_c, ah, aw, ch, cw))
    if not candidates:
        raise ValueError(
            "n_components=2 requires bbox dimensions with two multi-cell corner regions"
        )
    gap_r, gap_c, ah, aw, ch, cw = rng.choice(candidates)
    a_target = rng.randint(2, max(2, min(ah * aw, (ah * aw * 2) // 3 + 1)))
    b_target = rng.randint(2, max(2, min(ch * cw, (ch * cw * 2) // 3 + 1)))
    a = _grow_from_seed(ah, aw, (0, 0), rng, a_target)
    b_local = _grow_from_seed(ch, cw, (ch - 1, cw - 1), rng, b_target)
    b = {(gap_r + 1 + r, gap_c + 1 + c) for r, c in b_local}
    return a | b


def _color_cells(cells, n_colors, rng):
    ordered = sorted(cells)
    rng.shuffle(ordered)
    palette = rng.sample(list(_COLOR_POOL), n_colors)
    colored = {}
    for i, cell in enumerate(ordered):
        colored[cell] = palette[i] if i < n_colors else rng.choice(palette)
    return colored


def _component_count(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    count = 0
    h, w = len(grid), len(grid[0])
    while remaining:
        count += 1
        queue = [remaining.pop()]
        while queue:
            cell = queue.pop()
            for neighbor in _neighbors(cell, h, w):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
    return count


def _bbox(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _profiled_int(ctx, name, lo, hi, desired):
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, desired, desired)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            return _draw_from_degenerate(texture)
        raise ValueError(f"unsupported texture override: {texture!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = sample_index % EXAMPLES_NEEDED

    explicit_small = any(
        int(overrides[name]) < limit
        for name, limit in (("grid_h", 6), ("grid_w", 6), ("bbox_h", 4), ("bbox_w", 4))
        if name in overrides and overrides[name] is not None
    )
    desired_components = 1 if explicit_small else (2 if profile == 2 else 1)
    n_components = _profiled_int(ctx, "n_components", 1, 2, desired_components)

    desired_colors = (1, 3, 1, 2)[profile]
    n_colors = _profiled_int(ctx, "n_distinct_colors", 1, 3, desired_colors)

    min_bbox = 4 if n_components == 2 else 2
    grid_h_override = int(overrides["grid_h"]) if overrides.get("grid_h") is not None else None
    grid_w_override = int(overrides["grid_w"]) if overrides.get("grid_w") is not None else None
    bbox_h_hi = min(8, grid_h_override - 2) if grid_h_override is not None else 8
    bbox_w_hi = min(8, grid_w_override - 2) if grid_w_override is not None else 8
    if bbox_h_hi < min_bbox or bbox_w_hi < min_bbox:
        raise ValueError(
            f"n_components={n_components} is incompatible with requested grid dimensions"
        )

    bh = ctx.draw_int_diff("bbox_h", min_bbox, bbox_h_hi)
    bw = ctx.draw_int_diff("bbox_w", min_bbox, bbox_w_hi)

    if grid_h_override is not None:
        h = ctx.draw_int_diff("grid_h", 5, 20)
    else:
        h = ctx.draw_int_diff("grid_h", max(5, bh + 4), 20)
    if grid_w_override is not None:
        w = ctx.draw_int_diff("grid_w", 5, 22)
    else:
        w = ctx.draw_int_diff("grid_w", max(5, bw + 4), 22)
    if bh > h - 2 or bw > w - 2:
        raise ValueError("bbox overrides require at least one background margin on every side")

    rng = ctx.draw_rng("content")
    cells = (
        _one_component_cells(bh, bw, rng)
        if n_components == 1
        else _two_component_cells(bh, bw, rng)
    )
    if len(cells) < n_colors:
        raise ValueError("n_distinct_colors exceeds available nonzero cells")
    colored = _color_cells(cells, n_colors, rng)

    max_top = h - bh - 1
    max_left = w - bw - 1
    placements = (
        (1, 1),
        (max_top, max_left),
        (1, max_left),
        (max_top, 1),
    )
    top, left = placements[profile]
    grid = full_grid(h, w, 0)
    for (r, c), color in colored.items():
        grid[top + r][left + c] = color
    return grid


def _draw_from_degenerate(name):
    h, w = 9, 10
    grid = full_grid(h, w, 0)
    if name == "no_motif":
        return grid
    if name == "full_grid_motif":
        for r in range(h):
            grid[r][0] = 4
            grid[r][w - 1] = 6
        for c in range(w):
            grid[0][c] = 3
            grid[h - 1][c] = 8
        return grid
    if name == "solid_bbox":
        for r in range(2, 6):
            for c in range(3, 7):
                grid[r][c] = 5
        return grid
    if name == "three_components":
        for r, c in ((2, 2), (4, 5), (6, 7)):
            grid[r][c] = 5
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")


def observe_overrides(grid):
    box = _bbox(grid)
    if box is None:
        return {}
    r0, c0, r1, c1 = box
    colors = {value for row in grid for value in row if value != 0}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "bbox_h": r1 - r0 + 1,
        "bbox_w": c1 - c0 + 1,
        "n_components": _component_count(grid),
        "n_distinct_colors": len(colors),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the task's nontrivial teaching grammar, not only palette/shape."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    if not (5 <= h <= 20 and 5 <= w <= 22):
        errs.append(f"grid dimensions outside generator contract: {h}x{w}")
    bad_values = [
        value
        for row in grid
        for value in row
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
    ]
    if bad_values:
        errs.append("grid values must be integer ARC colors 0..9")
        return errs

    box = _bbox(grid)
    if box is None:
        errs.append("no nonzero cells found")
        return errs
    r0, c0, r1, c1 = box
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    colors = {grid[r][c] for r, c in cells}
    bh, bw = r1 - r0 + 1, c1 - c0 + 1

    if 0 not in {value for row in grid for value in row}:
        errs.append("background color 0 missing")
    if not (1 <= len(colors) <= 3):
        errs.append(f"nonzero palette must contain 1..3 colors, got {sorted(colors)}")
    if len(cells) < 3:
        errs.append("at least three nonzero cells are required for a nontrivial crop")
    if bh < 2 or bw < 2:
        errs.append("nonzero bounding box must be at least 2x2")
    if r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1:
        errs.append("nonzero bbox must have a background margin on every side")
    if len(cells) == bh * bw:
        errs.append("nonzero bbox must preserve at least one interior zero hole")
    n_components = _component_count(grid)
    if not (1 <= n_components <= 2):
        errs.append(f"nonzero union must have one or two components, got {n_components}")
    return errs
