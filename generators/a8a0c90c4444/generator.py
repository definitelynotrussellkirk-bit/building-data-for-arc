"""Generator for arc_puzzle_bank_21_set18_s:S18_M5 — multi-motif gallery pack.

Rule: 3-4 small motifs in distinct colors at distinct positions; output
is a vertical pack.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a8a0c90c4444"
VERSION = "3.1.0"  # all_background fix: the random horizontal color-2 bars and vertical color-3 bars sometimes did not cross, so the row-span x col-span intersection was empty -> all-0 output. Now plant one GUARANTEED crossing (a 2-bar bracketing a col, a 3-bar bracketing its row) so the output always has >=1 eight."
TASK_ID = "a8a0c90c4444"

SUMMARY = (
    "0-bg grid (h~9-11, w~11-13) containing 3-4 "
    "small connected MOTIFS, each in a DISTINCT "
    "non-zero color from {2..9}. Each motif is "
    "3-5 cells (random-walk polyomino) at "
    "scattered non-overlapping positions with "
    "1-cell padding (isolated connected "
    "components). Rule: identify each distinct "
    "non-bg COLOR and extract its motif's "
    "normalized cells. PACK every motif's bbox "
    "into a VERTICAL GALLERY OUTPUT — stack the "
    "motifs top-to-bottom (or in canonical "
    "order by color or size) into a smaller "
    "composite grid, each motif in its original "
    "color. Output size depends on motif count "
    "and dimensions. Net: input has scattered "
    "colored motifs; output is a clean vertical "
    "pack."
)

INVARIANTS = [
    "background is 0",
    "3-4 connected motifs in distinct non-zero colors at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..18"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
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


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # Rule: color-2 cells -> per-row horizontal spans (min..max col); color-3
    # cells -> per-col vertical spans; output 8s at the INTERSECTIONS. v1.x placed
    # random-colored motifs that rarely formed crossing 2/3 spans -> output
    # collapsed (distinct 9, one per grid size). Now place explicit horizontal
    # color-2 bars + vertical color-3 bars that cross.
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 12); k2, k3 = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 13, 18); k2 = ctx.draw_int("k2", 3, 5); k3 = ctx.draw_int("k3", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 11, 15); k2 = ctx.draw_int("k2", 2, 4); k3 = ctx.draw_int("k3", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    def _set2(r, c):
        if g[r][c] == 0:
            g[r][c] = 2

    # horizontal color-2 bars: each in a distinct row, two 2s spanning >=2 cols
    rows2 = rng.sample(range(h), min(k2, h))
    for r in rows2:
        ca, cb = sorted(rng.sample(range(w), 2))
        if cb - ca < 2:
            cb = min(w - 1, ca + 2)
        _set2(r, ca); _set2(r, cb)
    # vertical color-3 bars: each in a distinct col, two 3s spanning >=2 rows
    cols3 = rng.sample(range(w), min(k3, w))
    for c in cols3:
        ra, rb = sorted(rng.sample(range(h), 2))
        if rb - ra < 2:
            rb = min(h - 1, ra + 2)
        if g[ra][c] == 0:
            g[ra][c] = 3
        if g[rb][c] == 0:
            g[rb][c] = 3
    # GUARANTEE >=1 intersection: a color-2 row-span bracketing column gc and a
    # color-3 col-span bracketing row gr -> the closures cross at (gr,gc) -> an
    # 8 in the output, so the result is never all-background.
    for _ in range(40):
        gr = rng.randint(1, h - 2); gc = rng.randint(1, w - 2)
        spots = [(gr, gc - 1), (gr, gc + 1), (gr - 1, gc), (gr + 1, gc), (gr, gc)]
        if all(g[r][c] == 0 for r, c in spots):
            g[gr][gc - 1] = 2; g[gr][gc + 1] = 2
            g[gr - 1][gc] = 3; g[gr + 1][gc] = 3
            break
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """The row-closure of color-2 cells must intersect the col-closure of
    color-3 cells in >=1 cell, so the rule paints >=1 eight (output not all-0)."""
    h, w = len(grid), len(grid[0])
    row_closed = set()
    for r in range(h):
        cs = [c for c in range(w) if grid[r][c] == 2]
        if cs:
            for c in range(min(cs), max(cs) + 1):
                row_closed.add((r, c))
    col_closed = set()
    for c in range(w):
        rs = [r for r in range(h) if grid[r][c] == 3]
        if rs:
            for r in range(min(rs), max(rs) + 1):
                col_closed.add((r, c))
    if not (row_closed & col_closed):
        return ["color-2 row-spans and color-3 col-spans do not intersect "
                "-> all-0 output"]
    return []


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
