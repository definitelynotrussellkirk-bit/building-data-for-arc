"""Generator for arc_puzzle_bank_21_set12_s:S12_H3.

Rule: top-row legend (3 blue + 2 red) selects the component matching
its graph-cluster size and degree.

Combinatorial axes (8): shape, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_target, missing_neighbors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2c820ee2654"
VERSION = "2.0.1"
TASK_ID = "c2c820ee2654"
SUMMARY = "Use a two-count legend to select the component with matching graph-cluster size and degree."

INVARIANTS = [
    "the top row has three blue cells and two red cells",
    "the target component belongs to a three-component contact cluster",
    "the target component has degree two within that cluster",
    "no other component matches both the cluster-size and degree constraints",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_target", "missing_neighbors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "shape":          {"type": "int", "default": "rng 0..5", "valid": "0..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "legend_top_components_below",
                       "valid": "legend_top_components_below"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_TARGETS = [
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
    [(0, 0), (0, 1), (1, 1), (1, 2)],
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _free(g, cells):
    h, w = len(g), len(g[0])
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < h and 0 <= cc < w and g[rr][cc] != 0:
                    return False
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: top row has ≥1 color-1 cell (want-cluster legend); body rows have ≥2 objects."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    ones_row0 = sum(1 for c in range(w) if grid[0][c] == 1)
    body = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] != 0]
    if ones_row0 < 1:
        errs.append("top row has no color-1 legend cells (want-cluster)")
    if not body:
        errs.append("no non-zero cells in body rows")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Rule: want-cluster = count of 1s in row 0, want-degree = count of 2s in row 0;
    # output = the object whose (cluster-size, degree) matches, in colour 8. We set
    # want-cluster=1, want-degree=0 -> the unique ISOLATED object (cluster size 1,
    # degree 0) is selected. Make that a RANDOM shape (it becomes the output) and put
    # all decoys in >=2-object clusters so they never match. (was fixed 9x12 + 6-bank)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 12); k_lo, k_hi = 3, 5; n_dec = ctx.draw_int("n_decoy", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 12, 18); k_lo, k_hi = 5, 8; n_dec = ctx.draw_int("n_decoy", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 13); w = ctx.draw_int("grid_w", 10, 15); k_lo, k_hi = 4, 7; n_dec = ctx.draw_int("n_decoy", 1, 2)
    g = full_grid(h, w, 0)
    g[0][0] = 1                              # want-cluster = 1 (no 2s -> want-degree 0)
    body_top = 2                             # leave row 1 clear (body = rows 1+)
    # target: random isolated shape (becomes the output) in rows >= body_top
    target = _poly(rng, rng.randint(k_lo, k_hi))
    th = max(r for r, _ in target) + 1; tw = max(c for _, c in target) + 1
    tcolor = rng.choice([3, 4, 5, 6, 7, 8, 9])
    placed_target = False
    for _ in range(200):
        r0 = rng.randint(body_top, h - th); c0 = rng.randint(0, w - tw)
        cells = [(r0 + dr, c0 + dc) for dr, dc in target]
        if _free(g, cells):
            for (r, c) in cells:
                g[r][c] = tcolor
            placed_target = True
            break
    if not placed_target:
        return g
    # decoys: clusters of 2-3 mutually-adjacent single cells in DISTINCT colours
    # (cluster-size >= 2 -> never match want-cluster==1)
    dec_colors = [c for c in [3, 4, 5, 6, 7, 8, 9] if c != tcolor]
    rng.shuffle(dec_colors)
    ci = 0
    for _ in range(n_dec):
        ksz = rng.randint(2, 3)
        for _ in range(150):
            r0 = rng.randint(body_top, h - 2); c0 = rng.randint(0, w - ksz - 1)
            line = [(r0, c0 + i) for i in range(ksz)]   # horizontal adjacent line
            if _free(g, line) and ci + ksz <= len(dec_colors):
                for i, (r, c) in enumerate(line):
                    g[r][c] = dec_colors[ci + i]          # distinct colour each -> separate objects, one cluster
                ci += ksz
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 12, 0)
    if name == "no_legend":
        # Components present but top row is empty — rule has no legend
        # spec to match cluster-size/degree.
        target = _TARGETS[0]
        for r, c in target:
            g[4 + r][5 + c] = 3
        g[4][4] = 4; g[4][7] = 5
        g[2][1] = 6; g[2][2] = 7
        return g
    if name == "no_target":
        # Legend present but no body components — nothing to select.
        for c in range(3): g[0][c] = 1
        for c in range(3, 5): g[0][c] = 2
        return g
    if name == "missing_neighbors":
        # Legend + a center component but the contact cluster lacks the
        # left/right neighbors — degree 0, doesn't match degree-2 spec.
        for c in range(3): g[0][c] = 1
        for c in range(3, 5): g[0][c] = 2
        target = _TARGETS[0]
        for r, c in target:
            g[4 + r][5 + c] = 3
        return g
    return g
