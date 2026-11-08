"""Generator for arc_additional_puzzles_21_set18_bundle:E126 — Iterative 2x2 fill.

Rule: scan 2x2 windows; whenever 3 of 4 cells are same non-zero, fill
the 4th. Iterate.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_l_pattern, all_complete_squares, mixed_color_l.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b7d1307ff93"
VERSION = "2.0.0"
TASK_ID = "8b7d1307ff93"
SUMMARY = (
    "0-bg grid (h ∈ 7-9 / 10-14, w ∈ "
    "8-11 / 12-16, depending on "
    "difficulty) with: MULTIPLE "
    "L-SHAPED 3-CELL GROUPS — n_shapes "
    "∈ 1-6 placements, each shape is "
    "an L-tromino (3 of the 4 cells of "
    "a 2×2 block) drawn from LSHAPES "
    "(4 rotations: NE / NW / SE / SW). "
    "Each L is painted in a DISTINCT "
    "non-bg color drawn from a 1-6 "
    "color palette. Placements use a "
    "spread-rejection of 4 cells "
    "between origins (no two L origins "
    "within 4 cells of each other). "
    "The 4th cell of each 2×2 block is "
    "0 by construction (since only 3 "
    "cells of the L were painted). "
    "Rule (ITERATIVELY FILL THE 4TH "
    "CELL OF ANY 2×2 WINDOW WHERE 3 "
    "CELLS SHARE A NON-BG COLOR AND "
    "THE 4TH IS 0): REPEATEDLY SCAN "
    "every 2×2 WINDOW of the grid. "
    "When a window has EXACTLY 3 "
    "non-bg cells SHARING THE SAME "
    "COLOR c AND the 4th cell is 0: "
    "PAINT that 4th cell = c. CHAIN: "
    "the newly-filled cell may "
    "complete adjacent 2×2 windows, "
    "cascading further fills. "
    "ITERATE UNTIL no 2×2 window "
    "still has a fillable corner. "
    "Net: each L-tromino becomes a "
    "2×2 solid block; cascading "
    "growth may extend beyond the "
    "initial Ls when filled cells "
    "complete adjacent triples."
)

# Rivals: 'fill once (no iteration)' refuted by ≥1 demo where chained
# fills cascade. 'fill with bg' refuted by any demo (fill matches L's
# color). 'fill solid blocks too' refuted by any demo (only L → 2×2).
# 'merge across colors' refuted by ≥1 demo with multiple colors
# preserved.
# 4 demos with varied L shapes + counts cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "2-3 L-shapes (3 cells of one color forming an L)",
    "each L's missing 4th cell is 0",
    "shapes well-separated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_l_pattern", "all_complete_squares", "mixed_color_l")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "separated_l_shapes",
                       "valid": "separated_l_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

LSHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        n_shapes = rng.randint(1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        n_shapes = rng.randint(4, 6)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 10, 13)
        n_shapes = rng.randint(2, 4)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_shapes)
    placed = []
    for color in palette:
        for _ in range(40):
            shape = rng.choice(LSHAPES)
            r0 = rng.randint(0, h - 2); c0 = rng.randint(0, w - 2)
            if any(abs(r0 - pr) < 4 and abs(c0 - pc) < 4 for pr, pc in placed):
                continue
            for dr, dc in shape:
                g[r0 + dr][c0 + dc] = color
            placed.append((r0, c0))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_l_pattern":
        # blank → no 2x2 windows with 3 same cells
        return g
    if name == "all_complete_squares":
        # 2x2 already filled → no empty corner to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        for dr in range(2):
            for dc in range(2):
                g[4 + dr][5 + dc] = 6
        return g
    if name == "mixed_color_l":
        # 2x2 has 3 cells of 3 different colors → no shared color
        g[1][1] = 4; g[1][2] = 6; g[2][1] = 7
        return g
    return g

def _self_components(grid, colors=None):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if (r, c) in seen or v == 0 or (colors is not None and v not in colors):
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == v:
                        seen.add((nr, nc)); stack.append((nr, nc))
            out.append((v, cells))
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    msgs=[]; comps=_self_components(grid)
    need=1 if difficulty=="easy" else (4 if difficulty=="hard" else 2)
    if len(comps)<need: msgs.append(f"expected at least {need} L-tromino triggers, got {len(comps)}")
    for _,cells in comps:
        rs=[r for r,_ in cells]; cs=[c for _,c in cells]
        if not (len(cells)==3 and max(rs)-min(rs)==1 and max(cs)-min(cs)==1):
            msgs.append("each nonzero component must be a 3-cell L inside a 2x2 bbox"); break
    return msgs
