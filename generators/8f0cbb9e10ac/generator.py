"""Generator for arc_puzzle_bank_21_set12_s:S12_M6.

Combinatorial axes (8): grid_h, grid_w, palette_kind, winner_orientation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_winner, tied_variety, single_cluster.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f0cbb9e10ac"
VERSION = "2.0.1"
TASK_ID = "8f0cbb9e10ac"

SUMMARY = "0-bg grid with a WINNER cluster (random connected blob colored with 4 distinct colors) and 1-2 distractor clusters (fewer distinct colors), all separated. Rule: among adjacency-clusters of touching objects, pick the one with the most distinct colors and output its cell-union cropped, recolored to 8. Winner shape, colors, positions and grid size vary."

INVARIANTS = [
    "background is 0",
    "one contact cluster contains four distinct component colors",
    "a larger distractor cluster has fewer distinct colors",
    "the winning cluster is unique by distinct-color count",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_winner", "tied_variety", "single_cluster")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..15"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "winner_orientation": {"type": "str", "default": "rng horizontal|vertical",
                           "valid": "horizontal|vertical"},
    "palette_size":   {"type": "int", "default": "6", "valid": "6..6"},
    "position_bias":  {"type": "str", "default": "winner_plus_distractor",
                       "valid": "winner_plus_distractor"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "6..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=2 distinct non-bg colors present (winner + distractor clusters)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_winner", "tied_variety", "single_cluster"):
        return errs
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"need >=2 distinct non-bg colors (winner + distractor), found {len(colors)}")
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
    if r0 < 0 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _place_blob(g, rng, k, palette):
    """Place a random k-cell connected blob, each cell colored from palette
    (every palette color used at least once). Returns True on success."""
    h, w = len(g), len(g[0])
    poly = _rand_poly(rng, k)
    sh = max(r for r, _ in poly) + 1; sw = max(c for _, c in poly) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, sh, sw):
            continue
        cell_colors = list(palette)
        while len(cell_colors) < len(poly):
            cell_colors.append(rng.choice(palette))
        rng.shuffle(cell_colors)
        for (dr, dc), col in zip(poly, cell_colors):
            g[r0 + dr][c0 + dc] = col
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 12, 14); nd = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 18)
        nd = ctx.draw_int("n_distractors", 2, 2)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 16)
        nd = ctx.draw_int("n_distractors", 1, 2)
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        pool = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 4 + 2 * nd)
        win_colors = pool[:4]                       # winner: 4 distinct colors
        # winner blob (uniquely most distinct colors)
        if not _place_blob(g, rng, rng.randint(5, 10), win_colors):
            continue
        ok = True
        for i in range(nd):                          # distractors: 2 distinct colors each
            dpal = pool[4 + 2 * i:6 + 2 * i]
            if not _place_blob(g, rng, rng.randint(3, 7), dpal):
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize cluster layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "no_winner":
        # only the 2-color distractor → no max-variety cluster to select
        for i, color in enumerate([6, 7, 6, 7, 6]):
            g[h - 2][1 + i] = color
        return g
    if name == "tied_variety":
        # two clusters tie at 4 distinct colors → ambiguous winner
        for i, color in enumerate([1, 2, 3, 4]):
            g[2][2 + i] = color
        for i, color in enumerate([5, 6, 7, 9]):
            g[h - 2][2 + i] = color
        return g
    if name == "single_cluster":
        # only one cluster, no contrast → "uniqueness by distinct count" trivial
        for i, color in enumerate([1, 2, 3, 4]):
            g[3][3 + i] = color
        return g
    return g
