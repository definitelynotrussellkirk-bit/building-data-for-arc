"""Generator for v2_meta_puzzles:E6 — recolor yellow plus centers.

Rule: for each yellow plus, recolor only its center cell to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pluses,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pluses, partial_arms, wrong_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b018768ee9e2"
VERSION = "2.2.0"  # n-fallback when n pluses can't fit (easy 5x6 can't host 2 pluses w/ clearance)
TASK_ID = "b018768ee9e2"

SUMMARY = "Several plus-shaped (center + 4 cardinals) color-4 patterns. Rule recolors the CENTER cell of each plus to 8; arms stay color 4."

# Rivals: 'recolor every yellow to 8' refuted by ≥2 demos where only
# centers change (arms stay 4). 'recolor only one plus' refuted by
# ≥1 demo with ≥2 pluses (all centers change). 'use a different
# center color' refuted by any demo (center becomes 8). 'add a new
# yellow cell instead of recoloring' refuted by any demo (positions
# stay). 3 demos with varied plus counts cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "1-2 plus-shaped patterns: center and four cardinal cells are color 4",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pluses", "partial_arms", "wrong_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_pluses":       {"type": "int", "default": "rng 1..2", "valid": "1..7"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "spaced_yellow_pluses",
                       "valid": "spaced_yellow_pluses"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_pluses|partial_arms|wrong_color"},
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
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 6, 9)
        n = ctx.draw_int("n_pluses", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 18)
        n = ctx.draw_int("n_pluses", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        n = ctx.draw_int("n_pluses", 2, 4)

    # Each plus reserves a 3×3 bbox PLUS a 1-cell clearance ring (_free), so two
    # pluses need centers ≥4 apart in one axis or ≥3 in BOTH. On the easy band's
    # smallest grid (h=5, w=6) no 2-plus layout exists (vertical needs h≥7,
    # horizontal w≥7, diagonal h≥6 AND w≥6) — genuine capacity infeasibility, not
    # wedging, so the outer 40× retry can never succeed (~13/300 easy = exactly
    # P(h=5)·P(w=6)·P(n=2)). Fall back to fewer pluses: try n, and only if all 40
    # outer attempts fail drop to n-1 (down to 1 — still a valid layout, INVARIANT
    # allows ≥1 plus). Feasible (h,w,n) succeed in the target_n=n pass with the
    # identical draw stream (byte-identical); only the genuinely-infeasible
    # smallest grids redraw with fewer pluses. Count-exceeds-capacity class.
    for target_n in range(n, 0, -1):
        for outer in range(40):
            g = full_grid(h, w, 0)
            ok = True
            for _ in range(target_n):
                placed = False
                for _ in range(80):
                    r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
                    if not _free(g, r - 1, c - 1, r + 1, c + 1): continue
                    g[r][c] = 4
                    g[r - 1][c] = 4
                    g[r + 1][c] = 4
                    g[r][c - 1] = 4
                    g[r][c + 1] = 4
                    placed = True; break
                if not placed:
                    ok = False; break
            if ok:
                return g
    raise ValueError("could not realize E6 layout")


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_pluses":
        # blank → no plus shapes, rule has no centers to recolor
        return g
    if name == "partial_arms":
        # 4-cell partial pluses (missing one arm) → predicate "exact plus" fails
        g[2][3] = 4; g[1][3] = 4; g[3][3] = 4; g[2][2] = 4  # missing right arm
        return g
    if name == "wrong_color":
        # exact pluses but in color 6 (red→magenta), not 4 (yellow) → predicate fails
        g[2][3] = 6; g[1][3] = 6; g[3][3] = 6; g[2][2] = 6; g[2][4] = 6
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    h, w = len(grid), len(grid[0]) if grid else 0
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 4 and all(grid[r + dr][c + dc] == 4 for dr, dc in ((-1,0),(1,0),(0,-1),(0,1))):
                centers.append((r, c))
    lo = 1 if difficulty == "easy" else (4 if difficulty == "hard" else 2)
    if len(centers) < lo:
        return [f"expected at least {lo} yellow plus centers, got {len(centers)}"]
    return []
