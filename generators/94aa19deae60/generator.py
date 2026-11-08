"""Generator for arc_additional_puzzles_21_set11_bundle:M77.

Rule: row 0 has legend colors. For each, find the body object of that
color; concat their bbox crops horizontally with 1-col gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_legend,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_body_match, single_legend_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "94aa19deae60"
VERSION = "3.0.1"  # add self_check  # out_sh=1: body blobs were 3 FIXED shapes so output dims (max h, sum w + gaps) were constant. Rule packs each legend color's body blob horizontally. Use N (2..4) legend colors with RANDOM body polyominoes of varied size -> output dims and content vary.
TASK_ID = "94aa19deae60"
SUMMARY = (
    "0-bg grid with: (a) ROW 0 holds N legend cells (distinct colors, in order) "
    "at cols 0..N-1; (b) N body blobs below row 0, one per legend color, each a "
    "random polyomino, 4-conn isolated. Rule: for each legend color in order, "
    "crop its body blob and hconcat the crops with 1-col gaps. N, blob shapes "
    "and positions, and grid size all vary."
)

INVARIANTS = [
    "row 0 has N distinct non-zero legend cells (in order)",
    "N non-touching body blobs below row 0, one per legend color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_body_match", "single_legend_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 13..15", "valid": "11..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_legend":       {"type": "int", "default": "3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "legend_top_body_below",
                       "valid": "legend_top_body_below"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: row 0 has ≥2 distinct non-zero legend cells; ≥1 body cell below row 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    legend = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if len(legend) < 2:
        errs.append(f"row 0 has <2 legend cells; got {legend}")
    body = sum(1 for r in range(1, h) for c in range(w) if grid[r][c] != 0)
    if body < 1:
        errs.append("no body cells below row 0")
    return errs


def _rand_poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, r0, c0, sh, sw):
    h, w = len(g), len(g[0])
    if r0 < 1 or c0 < 0 or r0 + sh > h or c0 + sw > w:   # row 0 reserved for legend
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
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
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 12, 14); n = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_legend", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_legend", 2, 4)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        for i, color in enumerate(palette):
            g[0][i] = color   # legend, in order
        ok = True
        for color in palette:
            shape = _rand_poly(rng, rng.randint(3, 6))
            sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(1, h - sh); c0 = rng.randint(0, w - sw)
                if _free(g, r0, c0, sh, sw):
                    for dr, dc in shape:
                        g[r0 + dr][c0 + dc] = color
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize legend-pack layout")


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # row 0 empty → no order/colors selected, rule has nothing to extract
        paint_at(g, 3, 1, [(0, 0), (0, 1), (1, 0)], 4)
        paint_at(g, 2, 5, [(0, 0), (0, 1), (1, 0), (1, 1)], 6)
        paint_at(g, 5, 10, [(0, 0), (1, 0), (2, 0), (2, 1)], 7)
        return g
    if name == "no_body_match":
        # legend colors are set but body doesn't contain those colors → empty packing
        g[0][0] = 4; g[0][1] = 6; g[0][2] = 7
        paint_at(g, 3, 1, [(0, 0), (0, 1), (1, 0)], 2)
        paint_at(g, 2, 5, [(0, 0), (0, 1)], 3)
        return g
    if name == "single_legend_color":
        # legend has only 1 color → packing is trivially one crop
        g[0][0] = 4
        paint_at(g, 3, 1, [(0, 0), (0, 1), (1, 0)], 4)
        return g
    return g
