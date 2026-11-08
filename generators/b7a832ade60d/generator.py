"""Generator for 11b:m77 — border rays until block.

Rule: each non-zero cell on the grid border emits a ray inward in the
cardinal direction perpendicular to its border. The ray paints itself
in the same color until hitting a non-zero cell or the opposite border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_emitters,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_emitters, no_blockers, all_emitters_one_side.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b7a832ade60d"
# 1.2.0: emitters were fixed at 3 positions on 3 edges + 1 block. Now emitters
# spread across ALL 4 edges with variable count, plus several color-5 interior
# blockers (matching the canonical structure where 5 stops rays).
VERSION = "1.2.1"
TASK_ID = "b7a832ade60d"
SUMMARY = (
    "0-bg grid with several BORDER EMITTERS (non-0,non-5 cells on the outer "
    "edge, spread across all 4 edges) and several interior COLOR-5 BLOCKERS. "
    "Rule: each border emitter shoots a ray inward (perpendicular to its "
    "edge) through 0-cells, painting them its color, until it hits any non-0 "
    "cell (a 5-blocker or another ray's tip) or the far border."
)

INVARIANTS = [
    "background is 0",
    "≥2 distinct-color cells on the grid border (emitters)",
    "≥1 non-emitter cell in the interior (acts as ray-block)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_emitters", "no_blockers", "all_emitters_one_side")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_emitters":     {"type": "int", "default": "rng 3..6", "valid": "2..8"},
    "n_blockers":     {"type": "int", "default": "rng 1..4", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "varies", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "border_emitters_plus_blocker",
                       "valid": "border_emitters_plus_blocker"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: corner cells are 0; color-5 (blockers) are not on the border."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    for r, c in corners:
        if grid[r][c] != 0:
            errs.append(f"corner ({r},{c})={grid[r][c]}, expected 0 (emitters avoid corners)")
    border5 = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] == 5 and (r in (0, h - 1) or c in (0, w - 1))]
    if border5:
        errs.append(f"color-5 (blocker) cells on border: {border5}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        n_emit = (2, 4); n_block = (1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 11, 14)
        n_emit = (5, 8); n_block = (2, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_emit = (3, 6); n_block = (1, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    emit_pool = [1, 2, 3, 4, 6, 7, 8, 9]   # non-0, non-5 (5 is the blocker)

    # emitters spread across all 4 edges (interior of each edge, avoiding
    # corners so the ray direction is unambiguous)
    def _edge_cell(edge):
        if edge == "top":    return (0, rng.randint(1, w - 2))
        if edge == "bottom": return (h - 1, rng.randint(1, w - 2))
        if edge == "left":   return (rng.randint(1, h - 2), 0)
        return (rng.randint(1, h - 2), w - 1)   # right

    n = rng.randint(*n_emit)
    placed = 0
    for _ in range(n * 6):
        if placed >= n:
            break
        edge = rng.choice(["top", "bottom", "left", "right"])
        r, c = _edge_cell(edge)
        if g[r][c] == 0:
            g[r][c] = rng.choice(emit_pool)
            placed += 1

    # color-5 interior blockers
    nb = rng.randint(*n_block)
    placed_b = 0
    for _ in range(nb * 8):
        if placed_b >= nb:
            break
        r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
        if g[r][c] == 0:
            g[r][c] = 5
            placed_b += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_emitters":
        # only an interior cell, no border emitters → no rays to draw
        g[3][4] = 4
        return g
    if name == "no_blockers":
        # border emitters with no interior block → rays cross the whole grid
        g[0][3] = 4
        g[h - 1][5] = 6
        g[3][0] = 7
        return g
    if name == "all_emitters_one_side":
        # all emitters on top edge → only downward rays, no contrast for direction
        g[0][2] = 4
        g[0][4] = 6
        g[0][6] = 7
        g[3][3] = 9  # blocker
        return g
    return g
