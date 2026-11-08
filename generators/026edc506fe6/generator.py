"""Generator for arc_additional_puzzle_bank_volume20:M134 — Translate color-1 cells by red→green vector.

Rule:
  - a = first red(2) cell, b = first green(3) cell
  - delta = b - a
  - Move every color-1 cell by delta, paint at the new positions with 4.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: zero_delta, no_shape, missing_marker.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "026edc506fe6"
VERSION = "2.1.1"
TASK_ID = "026edc506fe6"
SUMMARY = (
    "0-bg grid (h~6-10, w~10-14) with: (a) a 4-conn SHAPE "
    "of color 1 (blue), 2-5 cells; (b) exactly ONE color-2 "
    "(red) single-cell MARKER 'a'; (c) exactly ONE color-3 "
    "(green) single-cell MARKER 'b'. The translated shape "
    "stays in-bounds and doesn't overlap existing non-bg "
    "cells. Rule: compute delta = (b_row - a_row, "
    "b_col - a_col). For every color-1 cell (r, c), paint "
    "output[r+dr][c+dc] = 4 (yellow). Original color-1 "
    "cells, the red marker, and the green marker stay in "
    "place. Net: a color-4 copy of the blue shape appears "
    "translated by the red→green vector."
)

# Rivals: 'translation is always rightward' refuted by leftward/up
# deltas. 'copy never touches the original' refuted by overlap boards
# where 4 overpaints some 1s. 'copy always fits' refuted by clipped
# boards. 'delta from green to red' refuted by direction. 3 demos
# with varied delta directions + >=1 overlap or clip board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "exactly one red(2) cell and one green(3) cell (the rule crashes "
    "if either is missing)",
    ">=2 color-1 cells (form a shape)",
    "delta between red and green is non-zero",
    "overlap boards: the 4-copy overpaints part of the original shape",
    "clip boards: part of the copy falls off-board (paint-cells clips)",
]

DEGENERATE_TEXTURES = ("no_shape", "adjacent_markers")
HELPFUL_TEXTURES = ("plain", "overlap", "clip")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 6..10 (hard 9..12)",
                "valid": "5..14", "doc": "Grid height."},
    "grid_w":  {"type": "int", "default": "rng 10..14 (hard 13..16)",
                "valid": "8..18", "doc": "Grid width."},
    "n_shape": {"type": "int", "default": "rng 3..5", "valid": "2..6",
                "doc": "Blue shape cell count."},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|overlap|clip|no_shape|adjacent_markers",
                "doc": "Edge-case flavor or a degenerate name."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 red(2) and 1 green(3); >=2 blue(1) cells; delta non-zero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if len(reds) != 1:
        errs.append(f"expected exactly 1 red(2) cell, found {len(reds)}")
    if len(greens) != 1:
        errs.append(f"expected exactly 1 green(3) cell, found {len(greens)}")
    if len(blues) < 2:
        errs.append(f"expected >=2 blue(1) cells (the shape), found {len(blues)}")
    if len(reds) == 1 and len(greens) == 1:
        dr = greens[0][0] - reds[0][0]
        dc = greens[0][1] - reds[0][1]
        if dr == 0 and dc == 0:
            errs.append("red and green markers coincide (delta=0)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "overlap", "clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 10, 11)
        n_shape = ctx.draw_int("n_shape", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 13, 14)
        n_shape = ctx.draw_int("n_shape", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 10, 14)
        n_shape = ctx.draw_int("n_shape", 3, 5)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used = set()

    shape = grow_blob(rng, h - 2, max(3, w // 3), used, n_shape)
    if shape is None:
        shape = {(1, 1)}
    shape_rs = [r for r, _ in shape]; shape_cs = [c for _, c in shape]
    sh = max(shape_rs) - min(shape_rs) + 1
    sw = max(shape_cs) - min(shape_cs) + 1
    sr_off = rng.randint(0, max(0, h - sh - 1))
    sc_off = rng.randint(0, max(0, max(1, w // 2) - sw - 1))
    shape = {(r - min(shape_rs) + sr_off, c - min(shape_cs) + sc_off)
             for r, c in shape}

    for r, c in shape:
        g[r][c] = 1
    used |= shape

    placed_red = False
    for _ in range(80):
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 1)
        if (r, c) in used:
            continue
        # deltas go in EVERY direction (old code: dc >= 0, never leftward)
        dr = rng.randint(-h // 2, h // 2)
        dc = rng.randint(-(w // 3), max(1, w // 3))
        if dr == 0 and dc == 0:
            continue
        translated = {(rr + dr, cc + dc) for rr, cc in shape}
        oob = sum(1 for tr, tc in translated
                  if not (0 <= tr < h and 0 <= tc < w))
        hits_shape = bool(translated & shape)
        if texture == "clip":
            # part (not all) of the copy must fall off-board
            if oob == 0 or oob == len(translated):
                continue
        elif texture == "overlap":
            # the copy must overpaint >=1 original blue cell
            if oob or not hits_shape:
                continue
        else:
            if oob or hits_shape:
                continue
            if any((tr, tc) in used for tr, tc in translated):
                continue
        gr, gc = r + dr, c + dc
        if not (0 <= gr < h and 0 <= gc < w):
            continue
        if (gr, gc) in used or (gr, gc) == (r, c):
            continue
        # markers must not sit where the copy lands (4 would overpaint them
        # deterministically, but keeping them visible reads better)
        if (r, c) in translated or (gr, gc) in translated:
            continue
        g[r][c] = 2
        g[gr][gc] = 3
        used.add((r, c))
        used.add((gr, gc))
        placed_red = True
        break

    if not placed_red:
        for r in range(h):
            for c in range(w - 1):
                if (r, c) not in used and (r, c + 1) not in used:
                    g[r][c] = 2; g[r][c+1] = 3
                    return g
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (both markers always
    exist; the old zero_delta / missing_marker degenerates lacked a
    green cell and CRASHED the rule at (first (find-color g 3))).

    no_shape         — markers only: nothing to translate (identity).
    adjacent_markers — delta (0,1): the copy lands one cell over,
                       almost fully overlapping the original.
    """
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 10, 13)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    if name == "no_shape":
        r = rng.randint(0, h - 1)
        c = rng.randint(0, w - 4)
        g[r][c] = 2
        g[r][c + rng.randint(2, 3)] = 3
        return g
    # adjacent_markers
    for _ in range(40):
        r0 = rng.randint(1, h - 3)
        c0 = rng.randint(1, w - 4)
        cells = {(r0, c0), (r0, c0 + 1), (r0 + 1, c0)}
        mr = rng.randint(0, h - 1)
        mc = rng.randint(0, w - 2)
        if (mr, mc) in cells or (mr, mc + 1) in cells:
            continue
        for r, c in cells:
            g[r][c] = 1
        g[mr][mc] = 2
        g[mr][mc + 1] = 3
        return g
    return g
