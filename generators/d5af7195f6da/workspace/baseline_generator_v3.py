"""Generator for arc_puzzle_bank_sixteenth21:H111 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d5af7195f6da"
VERSION = "3.0.0"  # gray-walled arenas like the canonical demos; seed pool excludes 5 (the WALL color — old "seeds" of 5 were silently obstacles); +self_check; AXES synced
RULE_HASH = "ca2bc3cf692f"  # canonical rule this generator was written against
TASK_ID = "d5af7195f6da"

SUMMARY = (
    "0-bg grid (h~10-13, w~12-16) with 3-5 ISOLATED MOTIFS in "
    "distinct non-{0,5} colors (3-5 cells each). Color 5 acts "
    "as walls/barriers but is typically absent. Motifs are "
    "separated by ≥1 bg cell. Rule: split the grid into "
    "connected regions where walls (color 5) act as barriers "
    "(connectivity through non-5 cells). For each region, "
    "collect the non-bg SEED cells inside it. For each bg "
    "cell (r, c) in the region: compute geodesic distance to "
    "each seed (BFS through non-5 cells). Find the minimum "
    "distance. If exactly ONE seed color is at min distance, "
    "paint that cell with that color. Else (ties) leave as 0. "
    "Net effect: Voronoi tessellation by seed color via "
    "geodesic distance."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 connected motifs in distinct non-zero colors at distinct positions",
    "color 5 (walls) optional; if absent, all of grid is one region",
]

# Rivals: 'output is input' refuted by any demo (bg cells fill).
# 'fill with bg' refuted by any demo (uses motif colors). 'fill all
# cells one color' refuted by ≥2 demos with mixed motif colors.
# 'use Euclidean distance' refuted by ≥1 demo where Manhattan/geodesic
# wins. 3 demos with varied motif positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 10-13 med / 14-18 hard",
                       "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "9-12 easy / 12-16 med / 16-20 hard",
                       "valid": "9..20"},
    "n":              {"type": "int", "default": "2-3 easy / 3-5 med / 4-6 hard",
                       "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
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


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def self_check(grid, *, difficulty=None, meta=None):
    """Mirror the rule's reads: >=2 seed COLORS (never 5 — that's the wall
    color), and at least one empty cell for the Voronoi fill to paint."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    seeds = {grid[r][c] for r in range(h) for c in range(w)
             if grid[r][c] not in (0, 5)}
    errs = []
    if len(seeds) < 2:
        errs.append(f"need >=2 seed colors for a visible Voronoi split, got {len(seeds)}")
    if not any(grid[r][c] == 0 for r in range(h) for c in range(w)):
        errs.append("no empty cells — the rule would be an identity")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        n = ctx.draw_int("n", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 18)
        w = ctx.draw_int("grid_w", 16, 20)
        n = ctx.draw_int("n", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n", 3, 5)
    rng = ctx.draw_rng("layout")

    for outer in range(40):
        g = full_grid(h, w, 0)
        # Canonical scenes are GRAY-WALLED arenas (full border frame plus 0-2
        # interior wall segments); 5 is the rule's WALL color and must never
        # be a seed — the old pool included 5, silently turning such "seeds"
        # into obstacles the rule ignores.
        if rng.random() < 0.7:
            for c in range(w):
                g[0][c] = 5; g[h - 1][c] = 5
            for r in range(h):
                g[r][0] = 5; g[r][w - 1] = 5
            for _seg in range(rng.randint(0, 2)):
                if rng.random() < 0.5:
                    rr = rng.randint(2, h - 3)
                    c0 = rng.randint(1, w - 2)
                    for c in range(c0, min(w - 1, c0 + rng.randint(2, max(2, w // 2)))):
                        g[rr][c] = 5
                else:
                    cc = rng.randint(2, w - 3)
                    r0 = rng.randint(1, h - 2)
                    for r in range(r0, min(h - 1, r0 + rng.randint(2, max(2, h // 2)))):
                        g[r][cc] = 5
        colors = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n)
        ok = True
        for color in colors:
            cells = _build_motif(rng, rng.randint(3, 5))
            rs = [r for r, _ in cells]; cs = [c for _, c in cells]
            sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
                for r, c in cells:
                    g[r0 + r - min(rs)][c0 + c - min(cs)] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    return g   # graceful fallback (last attempt); never raise


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather treats
        # them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
        return g
    return g
