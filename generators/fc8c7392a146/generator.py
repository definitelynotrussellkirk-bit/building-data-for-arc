"""Generator for arc_additional_puzzles_21_set16_bundle:H111 — legend-ordered canonical gallery.

Rule: row 0 is the color order. Body has one connected component per legend
color. Each component is canonicalized (lex-min over 6 dihedral transforms)
and the canonical crops are concatenated left-to-right in legend order.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend (row 0 empty → rule has no order); no_body
(legend present but no body shapes → rule has nothing to crop);
legend_color_no_shape (a legend color has no body shape → rule's
body lookup returns nothing for that slot).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "fc8c7392a146"
VERSION = "2.1.0"  # random polyomino shapes + more legend colors + wider grids; legend built from placed colors (no crash)
TASK_ID = "fc8c7392a146"

SUMMARY = (
    "0-bg grid (h~8-10, w~14-18). ROW 0 is a LEGEND: "
    "2-3 NON-ZERO cells at distinct columns (in "
    "left-to-right column order). Below row 0 (starting "
    "at row 2) the body contains EXACTLY ONE connected "
    "4-conn SHAPE per legend color, each in the matching "
    "color, sized 3-5 cells. Shapes are 4-conn isolated "
    "from each other. Rule: (1) For each legend color, "
    "locate its body shape and CROP it to its bounding "
    "box. (2) CANONICALIZE the crop by taking the "
    "lex-min over six dihedral variants: identity, "
    "rotate-CW, rotate-180, transpose, flip-LR, flip-UD. "
    "(3) CONCATENATE the canonical crops horizontally in "
    "LEGEND ORDER (left-to-right column order of the row-0 "
    "cells) with a 1-cell gap of bg-0 between each pair. "
    "Output: a wide gallery strip of canonical shapes "
    "arranged in the legend's order."
)

INVARIANTS = [
    "background is 0",
    "row 0 has 2-3 distinct non-zero colors at distinct columns",
    "body has exactly one isolated 4-conn shape per legend color, in that color",
    "shapes are sized 3-5 cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_body", "legend_color_no_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "8-10 easy / 8-12 med / 9-14 hard", "valid": "7..16"},
    "grid_w":            {"type": "int", "default": "12-16 easy / 14-20 med / 16-24 hard", "valid": "12..26"},
    "n_legend":          {"type": "int", "default": "2-3 easy / 2-4 med / 3-4 hard", "valid": "2..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "shape_size":        {"type": "int", "default": "rng 3..6 cells per shape", "valid": "3..7"},
    "palette_size":      {"type": "int", "default": "= n_legend", "valid": "2..4"},
    "position_bias":     {"type": "str", "default": "row0_legend_with_body_shapes",
                          "valid": "row0_legend_with_body_shapes"},
    "n_distinct_colors": {"type": "int", "default": "= n_legend", "valid": "2..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _rand_poly(rng, size, maxdim=4):
    for _ in range(50):
        cells = {(0, 0)}
        frontier = [(0, 0)]
        while len(cells) < size and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc); frontier.append(nc)
        mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
        norm = sorted((r - mr, c - mc) for r, c in cells)
        if (len(norm) == size and max(r for r, _ in norm) + 1 <= maxdim
                and max(c for _, c in norm) + 1 <= maxdim):
            return norm
    return [(0, 0), (0, 1), (1, 0)]


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w:
        return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 12, 16)
        n_legend = ctx.draw_int("n_legend", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 16, 24)
        n_legend = ctx.draw_int("n_legend", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 14, 20)
        n_legend = ctx.draw_int("n_legend", 2, 4)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_legend)

    g = full_grid(h, w, 0)
    # Place one isolated random polyomino per color (rows 2+); track which landed.
    placed_colors = []
    for color in palette:
        shape = _rand_poly(rng, rng.randint(3, 6))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if sh > h - 2 or sw > w:
            continue
        for _ in range(80):
            r0 = rng.randint(2, h - sh)
            c0 = rng.randint(0, w - sw)
            if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            placed_colors.append(color)
            break
    if not placed_colors:                    # guarantee >=1 shape (rule needs a non-empty legend)
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][dc] = palette[0]
        placed_colors = [palette[0]]

    # Row-0 legend lists ONLY placed colors (every legend color has a body shape ->
    # the rule's crop-for never hits an empty filter). Shuffled order at scattered,
    # ascending columns (left-to-right = the output gallery order).
    order = list(placed_colors)
    rng.shuffle(order)
    cols0 = sorted(rng.sample(range(w), len(order)))
    for col, color in zip(cols0, order):
        g[0][col] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 15
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # Row 0 empty — rule has no order.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][2 + dc] = 4
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[3 + dr][8 + dc] = 6
        return g
    if name == "no_body":
        # Legend present but no body shapes.
        g[0][2] = 4; g[0][8] = 6
        return g
    if name == "legend_color_no_shape":
        # Legend has color 4, 6 but body only has color-4 shape (no color-6).
        g[0][2] = 4; g[0][8] = 6
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[3 + dr][2 + dc] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    legend = [v for v in grid[0] if v != 0]
    if difficulty == "hard":
        if not (3 <= len(legend) <= 4):
            msgs.append(f"hard legend should have 3..4 colors, found {len(legend)}")
    elif not (2 <= len(legend) <= 4):
        msgs.append(f"legend should have 2..4 colors, found {len(legend)}")
    if len(set(legend)) != len(legend):
        msgs.append(f"legend colors are not distinct: {legend}")
    body_colors = {v for r, row in enumerate(grid) if r > 0 for v in row if v != 0}
    extra = body_colors - set(legend)
    missing = set(legend) - body_colors
    if extra:
        msgs.append(f"body has colors absent from legend: {sorted(extra)}")
    if missing:
        msgs.append(f"legend colors missing body shapes: {sorted(missing)}")
    for color in sorted(set(legend)):
        comps = components(grid, colors={color})
        body_comps = [comp for comp in comps if any(r > 0 for r, _c in comp["cells"])]
        if len(body_comps) != 1:
            msgs.append(f"legend color {color} should have exactly one body component, found {len(body_comps)}")
    return msgs
