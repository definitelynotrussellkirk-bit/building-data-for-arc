"""Generator for arc_additional_puzzle_bank_volume5:H31.

Rule: a bottom legend recolors a multicolor template; maroon anchors
stamp the recolored copies above the legend.

Combinatorial axes (8): grid_h/w, palette_kind, n_anchors, palette_size,
position_bias, n_distinct_colors, legend_count, texture.
Degenerates: no_legend, no_template, no_anchors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "61a55c0c7ee8"
VERSION = "2.0.1"
TASK_ID = "61a55c0c7ee8"
SUMMARY = (
    "0-bg grid (h~10-14, w~12-17) with: (a) MULTICOLOR "
    "TEMPLATE in the TOP-LEFT corner — fixed cells at "
    "(0,0)=1, (0,1)=2, (1,0)=3, (1,1)=1, (2,1)=2 "
    "forming a small 3-color motif using source colors "
    "{1, 2, 3}; (b) TWO MAROON (color 9) ANCHORS — one "
    "at (3, w//2) and one at (5, w-5) — interior "
    "anchor positions where copies of the template can "
    "be stamped; (c) BOTTOM LEGEND ROWS — rows h-2 and "
    "h-1, columns 0..2 hold three (source, "
    "destination) color pairs encoded as adjacent "
    "cells: (1,4) at col 0, (2,6) at col 1, (3,7) at "
    "col 2. The legend defines a recolor mapping {1→4, "
    "2→6, 3→7}. Rule (RECOLOR THE TEMPLATE BY THE "
    "LEGEND'S SRC→DST MAPPING, STAMP A COPY AT EACH "
    "MAROON ANCHOR): read the BOTTOM LEGEND (rows "
    "h-2/h-1) to build a SRC→DST color map. find the "
    "MULTICOLOR TEMPLATE in the top-left; APPLY the "
    "recolor map to every template cell, producing a "
    "RECOLORED TEMPLATE. find every MAROON (color 9) "
    "ANCHOR; STAMP a copy of the recolored template "
    "at each anchor's position (anchor as anchor "
    "position, replacing the 9 with the template's "
    "anchor-position color). Original template, "
    "anchors, and legend stay or are cleared per "
    "demos. Net: the small top-left template "
    "multiplies into recolored copies at each maroon "
    "anchor location."
)

INVARIANTS = [
    "the bottom two rows contain exactly three legend columns",
    "the template uses only source legend colors",
    "one or more maroon anchors appear above the legend",
    "all recolored template stamps fit above the legend rows",
]

PALETTE_KINDS = ("default", "warm_legend", "cool_legend", "varied_legend")
DEGENERATE_TEXTURES = ("no_legend", "no_template", "no_anchors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..24"},
    "grid_w":         {"type": "int", "default": "rng 12..17", "valid": "10..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_anchors":      {"type": "int", "default": "2", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "6", "valid": "6"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "6"},
    "legend_count":   {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 16, 17)
    else:
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 17)
    rng = ctx.draw_rng("layout")
    for _ in range(40):
        g = full_grid(h, w, 0)
        # Pick 3 distinct source colors and 3 distinct destination colors
        # (no overlap so the recolor is a real change).
        src_pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        rng.shuffle(src_pool)
        srcs = src_pool[:3]
        dst_pool = [c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in srcs
                    and c != 9]
        if len(dst_pool) < 3:
            continue
        rng.shuffle(dst_pool)
        dsts = dst_pool[:3]
        # Bottom legend at random 3 contiguous columns.
        leg_c0 = rng.randint(0, w - 4)
        for i in range(3):
            g[h - 2][leg_c0 + i] = srcs[i]
            g[h - 1][leg_c0 + i] = dsts[i]
        # Multicolor template in the TOP region using all 3 source colors.
        # Pick a small 2x2-3x3 patch with random cells covering all src colors.
        templates = [
            [(0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 0), (2, 1, 1)],
            [(0, 0, 0), (0, 1, 1), (0, 2, 2), (1, 0, 1), (1, 2, 0)],
            [(0, 0, 0), (1, 0, 1), (1, 1, 2), (2, 0, 0), (2, 1, 1)],
            [(0, 0, 0), (0, 1, 2), (1, 0, 1), (1, 1, 0)],
            [(0, 0, 0), (0, 1, 1), (1, 0, 2), (2, 0, 0), (2, 1, 2)],
        ]
        tpl = rng.choice(templates)
        th = max(r for r, _, _ in tpl) + 1
        tw = max(c for _, c, _ in tpl) + 1
        tr = rng.randint(0, max(0, h // 4))
        tc = rng.randint(0, max(0, w // 4))
        if tr + th > h - 3 or tc + tw > w - 1:
            continue
        for dr, dc, idx in tpl:
            g[tr + dr][tc + dc] = srcs[idx]
        # Maroon anchors at random interior positions (above legend rows).
        n_anchors = rng.randint(1, 3)
        placed = 0
        for _ in range(60):
            if placed >= n_anchors:
                break
            ar = rng.randint(tr + th, h - 4)
            ac = rng.randint(1, w - 2)
            # Anchor must have room for a 3x3 stamp in-bounds, and not overlap template
            if g[ar][ac] != 0:
                continue
            if (tr <= ar < tr + th and tc <= ac < tc + tw):
                continue
            # Need stamp space (3x3 around anchor) above legend
            if ar - 1 < 0 or ar + 2 > h - 2 or ac - 1 < 0 or ac + 2 > w:
                continue
            g[ar][ac] = 9
            placed += 1
        if placed >= 1:
            return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Bottom 2 rows have legend colors; maroon(9) anchors present."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    # bottom 2 rows must have nonzero legend cells
    bottom_2 = [grid[h-2][c] for c in range(w) if grid[h-2][c] != 0]
    bottom_1 = [grid[h-1][c] for c in range(w) if grid[h-1][c] != 0]
    if not bottom_2 or not bottom_1:
        errors.append("bottom 2 legend rows do not both have nonzero cells")
    # maroon(9) anchor cells must exist
    has_anchor = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_anchor:
        errors.append("no maroon(9) anchor cells found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # template + anchors but no legend — recolor mapping undefined
        g[0][0] = 1; g[0][1] = 2; g[1][0] = 3; g[1][1] = 1; g[2][1] = 2
        g[3][w // 2] = 9
        return g
    if name == "no_template":
        # legend + anchors but no template to recolor and stamp
        g[3][w // 2] = 9
        for c, (src, dst) in enumerate([(1, 4), (2, 6), (3, 7)]):
            g[h - 2][c] = src
            g[h - 1][c] = dst
        return g
    if name == "no_anchors":
        # template + legend but no maroon anchors — no copies stamped
        g[0][0] = 1; g[0][1] = 2; g[1][0] = 3; g[1][1] = 1; g[2][1] = 2
        for c, (src, dst) in enumerate([(1, 4), (2, 6), (3, 7)]):
            g[h - 2][c] = src
            g[h - 1][c] = dst
        return g
    return g
