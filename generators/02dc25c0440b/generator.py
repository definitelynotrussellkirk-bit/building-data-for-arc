"""Generator for arc_additional_puzzles_21_set12_bundle:E80 — Mirror left half across full-9 column.

Rule: find the full-height col of 9s; for each non-bg cell on the
left side at (r, c), set (r, 2*gc - c) on the right side to that
color (if in-bounds).

Combinatorial axes (8): grid_h, grid_w, palette_kind, shape,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_guide, no_shape, cells_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "02dc25c0440b"
VERSION = "1.3.0"
TASK_ID = "02dc25c0440b"
SUMMARY = "Full-height col of 9s; left side has 1-3 small shapes; rule mirrors every left cell to the right."

# Rivals: 'mirror with fixed color' refuted by ≥2 demos with different
# left-side colors. 'mirror only the first cell' refuted by ≥1 demo
# with multiple shapes on the left. 'erase left side' refuted by any
# demo (left preserved). 'erase guide column' refuted by any demo.
# 'mirror around grid center, not guide column' refuted by ≥2 demos
# where guide column gc != w//2.
# 4 demos with varied gc positions, shape counts, and colors.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly 1 full-height col of 9s",
    "left side has >=1 shape whose mirror lands at least partly in-bounds "
    "(a fully-clipped lone shape made the output identical to the input)",
    "right side is empty (so the mirror is visible)",
]

DEGENERATE_TEXTURES = ("no_shape", "cells_both_sides")
HELPFUL_TEXTURES = ("plain", "partial_clip")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "grid_w":  {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|partial_clip|no_shape|cells_both_sides",
                "doc": "partial_clip: a mirror lands partly off-board "
                       "(no_guide was dropped — no full 9-column crashes "
                       "the rule's (in-range gc) with gc = #f)."},
}



def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "plain",
                                              "partial_clip"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 11, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")

    # Guide column: anywhere that leaves room on the left for shapes
    # AND room on the right for mirrored copies. Symmetric range so
    # 'gc = w//2' isn't a shortcut.
    gc_lo = max(3, (w - 1) // 2 - 2)
    gc_hi = min(w - 4, (w - 1) // 2 + 2)
    gc = rng.randint(gc_lo, gc_hi)
    for r in range(h):
        g[r][gc] = 9

    # Shape bank — 8 entries spanning sizes 3-5 with varied bboxes.
    shape_bank = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],            # L-tet
        [(0, 0), (0, 1), (1, 0)],                    # L-tromino
        [(0, 0), (1, 0), (1, 1), (2, 1)],            # S-tet
        [(0, 0), (0, 1), (0, 2), (1, 1)],            # T-tet
        [(0, 0), (0, 1), (1, 0), (1, 1)],            # O
        [(0, 0), (1, 0), (2, 0)],                    # I3-vert
        [(0, 0), (0, 1), (0, 2)],                    # I3-horiz
        [(0, 1), (1, 0), (1, 1), (1, 2)],            # T-tet down
    ]

    # Place 1-3 shapes on the left side (c < gc), each in its own color,
    # non-overlapping and non-4-touching. The rule mirrors every cell
    # so this trivially works.
    n_shapes = rng.randint(1, 3 if difficulty == "hard" else 2)
    colors_pool = [1, 2, 3, 4, 5, 6, 7, 8]
    rng.shuffle(colors_pool)
    placed = 0
    for _ in range(40):
        if placed >= n_shapes:
            break
        shape = rng.choice(shape_bank)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h or sw > gc:
            continue
        top = rng.randint(0, h - sh)
        left = rng.randint(0, gc - sw)
        # check overlap + 4-touch margin with existing non-zero cells
        # (excluding the guide column, which is intentionally adjacent)
        bad = False
        for dr, dc in shape:
            r, c = top + dr, left + dc
            if g[r][c] != 0:
                bad = True; break
            for ar, ac in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + ar, c + ac
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0 and g[nr][nc] != 9 and nc != gc:
                    bad = True; break
            if bad: break
        if bad:
            continue
        # mirror landing: count in-bounds mirror cells
        in_mirror = sum(1 for dr, dc in shape
                        if 2 * gc - (left + dc) < w)
        if texture == "partial_clip" and placed == 0:
            # first shape must clip partly (not fully) off the right edge
            if in_mirror == 0 or in_mirror == len(shape):
                continue
        elif in_mirror == 0 and placed == 0:
            continue  # fully-clipped lone shape -> identity output
        color = colors_pool[placed]
        paint_at(g, top, left, shape, color)
        placed += 1
    if placed == 0:
        # guaranteed visible mirror: dot adjacent to the guide column
        r = h // 2
        g[r][gc - 1] = colors_pool[0]
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied so each board differs.

    no_shape         — guide only: identity output.
    cells_both_sides — right-side content gets partially overwritten
                       by the mirror (deterministic, looks confusing).
    """
    h = ctx.draw_int("grid_h", 7, 9)
    w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("degenerate_layout")
    g = full_grid(h, w, 0)
    gc = rng.randint(4, w - 5)
    for r in range(h):
        g[r][gc] = 9
    if name == "no_shape":
        return g
    # cells_both_sides
    for _ in range(rng.randint(2, 3)):
        g[rng.randrange(h)][rng.randint(0, gc - 1)] = rng.randint(1, 8)
    for _ in range(rng.randint(2, 3)):
        g[rng.randrange(h)][rng.randint(gc + 1, w - 1)] = rng.randint(1, 8)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    guide_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(guide_cols) != 1:
        msgs.append("expected exactly one full-height 9 guide column")
        return msgs
    gc = guide_cols[0]
    extra_9 = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] == 9 and c != gc]
    if extra_9:
        msgs.append("9 should appear only in the guide column")
    left_cells = [(r, c, grid[r][c]) for r in range(h) for c in range(gc)
                  if grid[r][c] not in (0, 9)]
    if not left_cells:
        msgs.append("normal instance should contain at least one left-side colored cell")
    if not any(0 <= 2 * gc - c < w and 2 * gc - c != gc for _r, c, _v in left_cells):
        msgs.append("at least one left-side cell should mirror in bounds")
    right_nonzero = [(r, c) for r in range(h) for c in range(gc + 1, w)
                     if grid[r][c] != 0]
    if right_nonzero:
        msgs.append("right side should be empty before the mirror rule")
    return msgs
