"""Generator for arc_puzzle_bank_21_set23_bundle:medium_p02 — recolor by touch-degree.

Rule: each connected component is recolored according to how many other
components it "touches" (Manhattan distance ≤ 2). Colors: degree 0→2, 1→3,
2→4, 3→5, 4→6, else→7.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: all_isolated, all_touching, single_component.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c143a649adc4"
VERSION = "2.1.0"  # out_shapes 9: normal grid range narrow (9..11 x 12..14). Output=same dims; widen h/w toward valid (8..14 x 10..18) -> more output shapes."
TASK_ID = "c143a649adc4"

SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "12-14) with 3-4 "
    "ISOLATED 4-CONN "
    "COMPONENTS, each a 2-"
    "or 3-cell shape (L-"
    "tromino/I-domino/"
    "square-corner) in a "
    "DISTINCT color from "
    "{1..9}. Components "
    "placed at scattered "
    "positions with varying "
    "Manhattan-2 "
    "neighborhood degrees "
    "(some isolated, some "
    "touching others). "
    "Rule (RECOLOR EACH "
    "COMPONENT BY ITS "
    "MANHATTAN-2 TOUCH "
    "DEGREE): For EACH "
    "COMPONENT: COUNT the "
    "number of OTHER "
    "COMPONENTS within "
    "MANHATTAN-2 distance "
    "(any pair of cells in "
    "different components "
    "with Chebyshev ≤ 2 "
    "or Manhattan ≤ 2). "
    "MAP DEGREE → COLOR: "
    "0→2, 1→3, 2→4, 3→5, "
    "4→6, ≥5→7. RECOLOR "
    "all component cells "
    "to the mapped color. "
    "Net: each shape "
    "repaints by how many "
    "neighbors it has "
    "within Manhattan-2."
)

INVARIANTS = [
    "background is 0",
    "3-4 isolated 4-conn components in distinct colors",
    "components have varying touch-2 neighborhoods (so output uses multiple colors)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_isolated", "all_touching", "single_component")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "10..18"},
    "n_components":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_components",
                       "valid": "scattered_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 12)
        n = ctx.draw_int("n_components", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_components", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 14)
        w = ctx.draw_int("grid_w", 10, 18)
        n = ctx.draw_int("n_components", 3, 4)
    rng = ctx.draw_rng("layout")
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color in palette:
            shape = rng.choice([
                [(0, 0), (0, 1), (1, 0)],
                [(0, 0), (1, 0), (1, 1)],
                [(0, 0), (0, 1), (1, 1)],
                [(0, 0), (0, 1)],
            ])
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for dr, dc in shape:
                    g[r0 + dr][c0 + dc] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not place {0} components".format(n))


def self_check(grid, *, difficulty=None, meta=None):
    """Verify isolated 4-conn components invariants for c143a649adc4."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    nz_colors = {v for v in flat if v != 0}
    if len(nz_colors) < 3:
        errs.append(f"only {len(nz_colors)} non-zero colors (expected 3-4 distinct components)")
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "all_isolated":
        for r, c in [(1, 1), (1, 2)]: g[r][c] = 1
        for r, c in [(1, 10), (1, 11)]: g[r][c] = 3
        for r, c in [(8, 1), (8, 2)]: g[r][c] = 4
        for r, c in [(8, 10), (8, 11)]: g[r][c] = 5
        return g
    if name == "all_touching":
        for r, c in [(2, 4), (2, 5)]: g[r][c] = 1
        for r, c in [(4, 4), (4, 5)]: g[r][c] = 3
        for r, c in [(2, 7), (2, 8)]: g[r][c] = 4
        for r, c in [(4, 7), (4, 8)]: g[r][c] = 5
        return g
    if name == "single_component":
        for r, c in [(4, 5), (4, 6), (5, 6)]: g[r][c] = 6
        return g
    return g
