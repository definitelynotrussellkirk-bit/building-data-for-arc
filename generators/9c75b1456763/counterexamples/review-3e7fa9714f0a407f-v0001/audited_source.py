"""Generator for 09c534e7.

Rule: each connected 1+marker shape has a marker; rule recolors interior
1-cells to marker color.

Combinatorial axes (8): grid_h/w, n_rects, rect_h, rect_w, palette_kind,
position_bias, anchor_corner, asymmetry_force.
Degenerates: no_marker, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "9c75b1456763"
VERSION = "1.1.1"
TASK_ID = "9c75b1456763"
SUMMARY = "1-2 solid 1-rectangles >=4x4 with one marker cell inside (different from 1)."

INVARIANTS = [
    "1-2 solid 1-rectangles, each >=4x4",
    "each rectangle has exactly one non-1 cell inside (marker)",
    "rectangles don't touch (>=1 bg cell apart)",
]

POSITION_BIASES = ("scattered", "spread", "stacked", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marker", "full_grid", "single_cell")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 14..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 14..18", "valid": "10..22"},
    "n_rects":        {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "rect_h":         {"type": "int", "default": "rng 4..5", "valid": "4..7"},
    "rect_w":         {"type": "int", "default": "rng 4..5", "valid": "4..7"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 10, 12
        nr_lo, nr_hi = 1, 1
        rh_lo, rh_hi = 4, 4
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
        nr_lo, nr_hi = 2, 3
        rh_lo, rh_hi = 5, 7
    else:
        h_lo, h_hi = 14, 18
        nr_lo, nr_hi = 1, 2
        rh_lo, rh_hi = 4, 5
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    n_rects = int(overrides.get("n_rects",
                                ctx.draw_int("n_rects", nr_lo, nr_hi)))
    n_rects = max(1, min(3, n_rects))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, rng)
    placed = []
    for _ in range(n_rects * 30):
        if len(placed) >= n_rects:
            break
        rh = int(overrides.get("rect_h",
                               rng.randint(rh_lo, rh_hi)))
        rw = int(overrides.get("rect_w",
                               rng.randint(rh_lo, rh_hi)))
        rh = max(4, min(rh, h - 2))
        rw = max(4, min(rw, w - 2))
        r0 = rng.randint(1, max(1, h - rh - 1))
        c0 = rng.randint(1, max(1, w - rw - 1))
        if any(abs(r0 - pr) < (rh + 2) and abs(c0 - pc) < (rw + 2)
               for pr, pc in placed):
            continue
        draw_rect(g, r0, c0, rh, rw, 1)
        marker = rng.choice(pal)
        mr = rng.randint(r0 + 1, r0 + rh - 2)
        mc = rng.randint(c0 + 1, c0 + rw - 2)
        g[mr][mc] = marker
        placed.append((r0, c0))
    return g


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [5, 7, 8]
    elif kind == "primary":
        pool = [2, 3, 4]
    else:
        pool = [2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c not in (0, 1)]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    h, w = 16, 16
    g = full_grid(h, w, 0)
    if name == "no_marker":
        draw_rect(g, 4, 4, 4, 4, 1)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    if name == "single_cell":
        g[7][7] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: >=1 color-1 filled region >=4x4; at least one non-{0,1} marker cell exists."""
    msgs = []
    h, w = len(grid), len(grid[0])
    # Detect color-1 bbox >=4x4 (the marker replaces interior cells, so check filled+marker mix)
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 1)]
    if not ones:
        msgs.append("no color-1 cells found (expected solid rectangles)")
        return msgs
    if not markers:
        msgs.append("no non-{0,1} marker cells found")
        return msgs
    # Check that there's a bounding-box region >=4x4 filled with 1s or markers
    # (the rectangle is drawn with 1, then marker placed inside → interior may be non-1)
    rect_found = False
    for r1 in range(h):
        for c1 in range(w):
            if grid[r1][c1] not in (1,):
                continue
            for r2 in range(r1 + 3, h):
                for c2 in range(c1 + 3, w):
                    if (grid[r2][c2] in (1,) and
                            all(grid[r1][c] in (1,) for c in range(c1, c2 + 1)) and
                            all(grid[r2][c] in (1,) for c in range(c1, c2 + 1)) and
                            all(grid[r][c1] in (1,) for r in range(r1, r2 + 1)) and
                            all(grid[r][c2] in (1,) for r in range(r1, r2 + 1))):
                        rect_found = True
                        break
                if rect_found:
                    break
            if rect_found:
                break
        if rect_found:
            break
    if not rect_found:
        msgs.append("no color-1 rectangle >=4x4 with fully 1-filled perimeter found")
    return msgs
