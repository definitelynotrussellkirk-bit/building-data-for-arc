"""Generator for ARC puzzle 9f8de559.

A red head (2) and a straight magenta tail (6) form an eight-directional
arrow inside a solid orange rectangle (7).  Starting one cell beyond the
head, the oracle follows the arrow through orange cells and recolors the
first non-orange cell to orange.  Thus the rectangle grows by exactly one
cell at the ray exit point.

Version 3 broadens the teaching distribution from the four cardinal
orientations to all eight canonical orientations, makes every declared axis
observable and override-safe, and strengthens structural rejection.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "b8e2a07c1b6c"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "def70a52d143"

SUMMARY = (
    "A solid ORANGE(7) rectangle lies in a nonzero 5/8/9 background. "
    "Exactly one RED(2) head and a straight MAGENTA(6) tail are embedded "
    "in the rectangle. The arrow points away from the adjacent tail cell "
    "in any of the eight compass directions. Follow that ray through one "
    "or more orange cells and recolor the first non-orange cell to 7; only "
    "that single boundary cell changes."
)

INVARIANTS = [
    "rectangular grid with background palette exactly {5,8,9}",
    "one solid rectangular body whose cells are only 2/6/7",
    "exactly one red(2) head and one straight contiguous magenta(6) tail",
    "the adjacent tail cell uniquely determines one of eight arrow directions",
    "the forward ray crosses at least one orange(7) body cell",
    "the first non-orange ray cell is an in-grid 5/8/9 target",
]

DIRECTION_DELTAS = {
    "right": (0, 1),
    "left": (0, -1),
    "down": (1, 0),
    "up": (-1, 0),
    "down_right": (1, 1),
    "down_left": (1, -1),
    "up_right": (-1, 1),
    "up_left": (-1, -1),
}
DELTA_DIRECTIONS = {delta: name for name, delta in DIRECTION_DELTAS.items()}
ARROW_DIRECTIONS = tuple(DIRECTION_DELTAS)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 12..18",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 12..18",
        "valid": "12..18",
    },
    "arrow_direction": {
        "type": "str",
        "default": "rng over compatible eight-way directions",
        "valid": "right|left|down|up|down_right|down_left|up_right|up_left",
    },
    "shape_h": {
        "type": "int",
        "default": "difficulty-aware 5..h-2",
        "valid": "5..h-2",
    },
    "shape_w": {
        "type": "int",
        "default": "difficulty-aware 5..w-2",
        "valid": "5..w-2",
    },
    "trail_len": {
        "type": "int",
        "default": "difficulty-aware 1..6",
        "valid": "1..6",
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    explicit_h = overrides.get("shape_h") is not None
    explicit_w = overrides.get("shape_w") is not None
    explicit_grid_h = overrides.get("grid_h") is not None
    explicit_grid_w = overrides.get("grid_w") is not None

    # A single shape boundary override must remain constructible.  When the
    # corresponding grid size is free, enlarge its lower bound enough to leave
    # the mandatory one-cell background margin on both sides.
    grid_h_lo = 12
    if explicit_h and not explicit_grid_h:
        grid_h_lo = max(grid_h_lo, int(overrides["shape_h"]) + 2)
    grid_w_lo = 12
    if explicit_w and not explicit_grid_w:
        grid_w_lo = max(grid_w_lo, int(overrides["shape_w"]) + 2)
    if grid_h_lo > 18 or grid_w_lo > 18:
        raise ValueError("incompatible shape and grid boundary overrides")

    h = ctx.draw_int_diff("grid_h", 12 if explicit_grid_h else grid_h_lo, 18)
    w = ctx.draw_int_diff("grid_w", 12 if explicit_grid_w else grid_w_lo, 18)
    trail_len = ctx.draw_int_diff("trail_len", 1, 6)
    needed_span = trail_len + 2  # tail + head + >=1 orange cell ahead

    requested_h = int(overrides["shape_h"]) if explicit_h else None
    requested_w = int(overrides["shape_w"]) if explicit_w else None
    if requested_h is not None and not 5 <= requested_h <= h - 2:
        raise ValueError(
            f"incompatible shape_h={requested_h} for grid_h={h}; "
            f"expected 5..{h - 2}"
        )
    if requested_w is not None and not 5 <= requested_w <= w - 2:
        raise ValueError(
            f"incompatible shape_w={requested_w} for grid_w={w}; "
            f"expected 5..{w - 2}"
        )

    # If one explicit dimension is too short for the requested trail, force the
    # other free dimension to support a cardinal arrow.  With both dimensions
    # free, both support every direction, including diagonals.
    shape_h_lo = 5
    shape_w_lo = 5
    if not explicit_h and not explicit_w:
        shape_h_lo = shape_w_lo = max(5, needed_span)
    elif explicit_h and not explicit_w and requested_h < needed_span:
        shape_w_lo = max(5, needed_span)
    elif explicit_w and not explicit_h and requested_w < needed_span:
        shape_h_lo = max(5, needed_span)

    if shape_h_lo > h - 2 or shape_w_lo > w - 2:
        raise ValueError("incompatible trail length and available body dimensions")

    rh = ctx.draw_int_diff("shape_h", 5 if explicit_h else shape_h_lo, h - 2)
    rw = ctx.draw_int_diff("shape_w", 5 if explicit_w else shape_w_lo, w - 2)

    compatible = [
        name
        for name, (dr, dc) in DIRECTION_DELTAS.items()
        if (dr == 0 or rh >= needed_span) and (dc == 0 or rw >= needed_span)
    ]
    requested_direction = overrides.get("arrow_direction")
    if requested_direction is not None:
        if requested_direction not in DIRECTION_DELTAS:
            raise ValueError(f"unknown arrow_direction={requested_direction!r}")
        if requested_direction not in compatible:
            raise ValueError(
                "incompatible arrow_direction, trail_len, and body dimensions"
            )
    direction = ctx.draw_choice("arrow_direction", compatible)
    dr, dc = DIRECTION_DELTAS[direction]

    background_rng = ctx.draw_rng("background")
    placement_rng = ctx.draw_rng("placement")
    grid = _banded_background(h, w, background_rng)
    rr = placement_rng.randint(1, h - rh - 1)
    rc = placement_rng.randint(1, w - rw - 1)
    draw_rect(grid, rr, rc, rh, rw, 7)
    _place_arrow(grid, rr, rc, rh, rw, dr, dc, trail_len, placement_rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid arrow scene: " + "; ".join(errors))
    return grid


def _banded_background(h, w, rng):
    """Canonical-looking 5/8/9 bands with all colors guaranteed visible."""
    top, bottom, side = rng.sample([5, 8, 9], 3)
    grid = full_grid(h, w, side)
    top_depth = 1 + rng.randrange(max(1, h // 6))
    bottom_depth = 1 + rng.randrange(max(1, h // 6))
    side_width = 1 + rng.randrange(max(1, w // 6))
    for r in range(h):
        for c in range(w):
            if r < top_depth:
                grid[r][c] = top
            elif r >= h - bottom_depth:
                grid[r][c] = bottom
            elif c < side_width or c >= w - side_width:
                grid[r][c] = side
            else:
                grid[r][c] = rng.choice((top, bottom, side))
    # Sparse seams vary texture while preserving the semantic palette.
    seam_c = rng.randint(1, w - 2)
    seam_color = rng.choice((top, bottom, side))
    for r in range(0, h, 2):
        grid[r][seam_c] = seam_color
    return grid


def _axis_head_range(origin, size, delta, trail_len):
    if delta > 0:
        return origin + trail_len, origin + size - 2
    if delta < 0:
        return origin + 1, origin + size - 1 - trail_len
    return origin + 1, origin + size - 2


def _place_arrow(grid, rr, rc, rh, rw, dr, dc, trail_len, rng):
    row_lo, row_hi = _axis_head_range(rr, rh, dr, trail_len)
    col_lo, col_hi = _axis_head_range(rc, rw, dc, trail_len)
    if row_lo > row_hi or col_lo > col_hi:
        raise ValueError("incompatible arrow geometry after placement")
    hr = rng.randint(row_lo, row_hi)
    hc = rng.randint(col_lo, col_hi)
    grid[hr][hc] = 2
    for step in range(1, trail_len + 1):
        grid[hr - dr * step][hc - dc * step] = 6


def _analyze(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["empty or non-list grid"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid is not rectangular"]}
    if any(not isinstance(value, int) for row in grid for value in row):
        errors.append("grid contains a non-integer cell")
        return {"errors": errors}

    colors = {value for row in grid for value in row}
    allowed = {2, 5, 6, 7, 8, 9}
    if not colors <= allowed:
        errors.append(f"unexpected colors: {sorted(colors - allowed)}")
    if not {5, 8, 9} <= colors:
        errors.append("background must visibly contain all of 5, 8, and 9")

    heads = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(heads) != 1:
        errors.append(f"expected exactly one red head, found {len(heads)}")
        return {"errors": errors}
    hr, hc = heads[0]

    adjacent_tail = []
    for dr, dc in DIRECTION_DELTAS.values():
        nr, nc = hr + dr, hc + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 6:
            adjacent_tail.append((dr, dc))
    if len(adjacent_tail) != 1:
        errors.append(
            "head must have exactly one adjacent magenta tail cell, found "
            f"{len(adjacent_tail)}"
        )
        return {"errors": errors}

    tail_dr, tail_dc = adjacent_tail[0]
    dr, dc = -tail_dr, -tail_dc
    direction = DELTA_DIRECTIONS[(dr, dc)]
    expected_tail = set()
    step = 1
    while True:
        r, c = hr - dr * step, hc - dc * step
        if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 6:
            break
        expected_tail.add((r, c))
        step += 1
    trail_len = len(expected_tail)
    all_tail = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 6
    }
    if trail_len < 1:
        errors.append("tail is empty")
    if all_tail != expected_tail:
        errors.append("magenta cells must form one straight contiguous tail")

    body_positions = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in {2, 6, 7}
    ]
    r0 = min(r for r, _ in body_positions)
    r1 = max(r for r, _ in body_positions)
    c0 = min(c for _, c in body_positions)
    c1 = max(c for _, c in body_positions)
    shape_h = r1 - r0 + 1
    shape_w = c1 - c0 + 1
    if shape_h < 5 or shape_w < 5:
        errors.append("orange body must be at least 5x5")
    holes = [
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if grid[r][c] not in {2, 6, 7}
    ]
    if holes:
        errors.append(f"orange body rectangle has {len(holes)} hole(s)")

    r, c = hr + dr, hc + dc
    orange_run = 0
    while 0 <= r < h and 0 <= c < w and grid[r][c] == 7:
        orange_run += 1
        r += dr
        c += dc
    if orange_run < 1:
        errors.append("arrow ray must cross at least one orange cell")
    if not (0 <= r < h and 0 <= c < w):
        errors.append("arrow ray leaves the grid before a target cell")
        target = None
        target_color = None
    else:
        target = (r, c)
        target_color = grid[r][c]
        if target_color not in {5, 8, 9}:
            errors.append("ray target must be a non-orange 5/8/9 background cell")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "arrow_direction": direction,
        "shape_h": shape_h,
        "shape_w": shape_w,
        "trail_len": trail_len,
        "head": (hr, hc),
        "target": target,
        "target_color": target_color,
        "orange_run": orange_run,
        "body_bbox": (r0, c0, r1, c1),
    }


def observe_overrides(grid):
    """Recover every exact declared axis from a returned input grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "arrow_direction": facts["arrow_direction"],
        "shape_h": facts["shape_h"],
        "shape_w": facts["shape_w"],
        "trail_len": facts["trail_len"],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Reject malformed or shortcut-teaching arrow scenes structurally."""
    return list(_analyze(grid)["errors"])
