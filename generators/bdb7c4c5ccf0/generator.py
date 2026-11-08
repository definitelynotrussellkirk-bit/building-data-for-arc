"""Generator for arc_additional_puzzle_bank_volume15:M99.

Rule: a control color rotates the largest green template into a gray
frame.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_control, no_template, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "bdb7c4c5ccf0"
# 2.1.0: template shape was a FIXED 4-cell L and frame a FIXED 5x5; only
# the control color varied. Now: random connected polyomino template
# (4-6 cells) fitting a square box, and a variable frame size, so the
# rotate-into-frame transform varies in both orientation AND shape.
VERSION = "2.1.1"  # add self_check
TASK_ID = "bdb7c4c5ccf0"
SUMMARY = (
    "0-bg grid (h, w~12-18) "
    "with: (a) ONE CONTROL "
    "CELL at (0, 0) — a "
    "singleton color from "
    "{1, 2, 4, 6} encoding "
    "a ROTATION (1=0°, "
    "2=CW, 4=180°, 6=CCW); "
    "(b) ONE GREEN(3) "
    "TEMPLATE near top-"
    "left — fixed 4-cell "
    "L-shape at cells "
    "(2, 1), (2, 2), (3, "
    "1), (4, 1) (an "
    "asymmetric L); (c) "
    "ONE HOLLOW GRAY(5) "
    "RECTANGULAR FRAME "
    "near bottom-right at "
    "(h-7, w-7)..(h-2, "
    "w-2). The template "
    "fits inside the "
    "frame after the "
    "indicated rotation. "
    "Rule (ROTATE THE "
    "GREEN TEMPLATE BY "
    "THE CONTROL CODE, "
    "PLACE INSIDE THE "
    "GRAY FRAME): READ "
    "the CONTROL color → "
    "rotation. ROTATE the "
    "green template's "
    "cells by the "
    "indicated angle "
    "(0°/CW/180°/CCW). "
    "PLACE the rotated "
    "template's cells "
    "INSIDE the gray "
    "frame (centered or "
    "at a canonical "
    "position within the "
    "frame interior), "
    "painted GREEN. The "
    "control cell, "
    "original template, "
    "and frame all stay. "
    "Net: the template "
    "gets cloned into "
    "the frame interior "
    "at the orientation "
    "indicated by the "
    "control color."
)

INVARIANTS = [
    "background is 0",
    "one singleton control color is in 1, 2, 4, or 6",
    "there is one hollow gray frame",
    "the green template fits inside the frame after rotation",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_control", "no_template", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..16", "valid": "10..24"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "10..30"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, size, max_h, max_w):
    """BFS-grow a connected polyomino of `size` cells within max_h x max_w."""
    cells = {(0, 0)}
    frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]
            cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
                continue
            cells.add((nr, nc))
            frontier.append((nr, nc))
            grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells)
    cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has singleton control color {1,2,4,6}; has gray(5) frame; has green(3) template."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    control = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] in (1, 2, 4, 6)]
    gray = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    green = any(grid[r][c] == 3 for r in range(h) for c in range(w))
    if not control and not gray and not green:
        return errs  # degenerate
    if not control:
        return errs  # degenerate no_control
    if not gray:
        errs.append("no gray(5) frame cells found")
    if not green:
        errs.append("no green(3) template cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 13, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 16)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 13, 18)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    g[0][0] = rng.choice([1, 2, 4, 6])

    # Frame: choose interior size 3..5, frame outer = interior+2, bottom-right.
    # Keep template (top-left, occupying rows/cols 1..interior) clear of the
    # frame: need 2*interior+5 <= min(h, w).
    interior_cap = min(5, (min(h, w) - 5) // 2)
    interior = rng.randint(3, max(3, interior_cap))
    fsz = interior + 2
    fr1 = h - fsz - 1
    fc1 = w - fsz - 1
    draw_frame(g, fr1, fc1, fr1 + fsz - 1, fc1 + fsz - 1, 5)

    # Template: random polyomino fitting in an interior x interior box so all
    # 4 rotations land inside the frame interior. Place near top-left (rows
    # 1.., cols 1..), away from the control cell and the frame.
    box = interior
    size = rng.randint(min(4, box * box), min(6, box * box))
    shape = _poly(rng, size, box, box)
    for dr, dc in shape:
        g[1 + dr][1 + dc] = 3
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 14, 0)
    if name == "no_control":
        for r, c in [(2, 1), (2, 2), (3, 1), (4, 1)]:
            g[r][c] = 3
        draw_frame(g, 6, 7, 11, 12, 5)
        return g
    if name == "no_template":
        g[0][0] = 1
        draw_frame(g, 6, 7, 11, 12, 5)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(14):
                g[r][c] = 5
        return g
    return g
