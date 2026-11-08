"""Generator for 50846271.

Rule: partial color-2 plus signs complete by turning covered color-5
cells to color 8.

Combinatorial axes (8): grid_h/w, plus_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_pluses, single_pixel, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7f0d975b36d2"
VERSION = "3.1.0"  # identity fix: rad 3-4 put the two horizontal tips >4 cols apart, so the rule's per-row <=4 cluster split them and inferred NO plus -> nothing painted. Cap rad at 2 so tips always cluster.
TASK_ID = "7f0d975b36d2"
SUMMARY = (
    "13×13 grid filled mostly with color 5 (gray) background. "
    "At center (6, 6) is a PARTIAL PLUS marked with 4 color-2 "
    "(red) cells at the cardinal arm positions: (6,5)(6,7)"
    "(5,6)(7,6). A few sparse cells outside the center are "
    "noise (random 0 or 5). Rule: scan all color-2 cells. "
    "Cluster them per row by proximity (≤4 cols apart). For "
    "each cluster of ≥2 two-cells, infer the plus's center "
    "column = avg of the cluster's col span, radius = max "
    "distance to avg. Then check column candidates for column "
    "matches. For each inferred plus center (cr, cc): paint "
    "every color-5 cell on the plus's horizontal arm "
    "(cr, cc-r..cc+r) AND vertical arm (cr-r..cr+r, cc) to "
    "color 8 (cyan). Color-2 cells stay. Net effect: complete "
    "the plus by filling its arms in cyan."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "13×13 grid with mostly color-5 background",
    "candidate plus arms are marked by color 2",
    "missing covered cells are color 5",
    "only color-5 cells on inferred plus arms are recolored to 8",
    "all color-2 evidence cells remain unchanged",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_pluses", "single_pixel", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..18", "valid": "9..24"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "9..24"},
    "plus_count":     {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "center", "valid": "center"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        rng = ctx.draw_rng("layout")
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13); w = ctx.draw_int("grid_w", 11, 13)
        K = ctx.draw_int("plus_count", 1, 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 17, 24); w = ctx.draw_int("grid_w", 17, 24)
        K = ctx.draw_int("plus_count", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 13, 18)
        K = ctx.draw_int("plus_count", 1, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 5)

    # Place K pluses, each marked by its 4 color-2 arm tips. Vertically
    # separated so each plus's marked rows form a distinct per-row cluster.
    placed = []
    # The rule clusters per-row 2-cells that are <=4 columns apart. A plus's two
    # HORIZONTAL tips sit 2*rad apart on the center row, so rad>2 (tips >4 apart)
    # splits them into singleton clusters -> no plus inferred -> nothing painted
    # -> identity demo. Cap radius at 2 so the tips always cluster.
    rad_hi = 2
    for _ in range(400):
        if len(placed) >= K:
            break
        rad = rng.randint(1, max(1, min(rad_hi, (h - 1) // 2, (w - 1) // 2)))
        r = rng.randint(rad, h - 1 - rad)
        c = rng.randint(rad, w - 1 - rad)
        if any(abs(r - pr) <= rad + prad + 1 for pr, pc, prad in placed):
            continue
        for tr, tc in [(r, c - rad), (r, c + rad), (r - rad, c), (r + rad, c)]:
            g[tr][tc] = 2
        placed.append((r, c, rad))

    # sparse noise (0 or 5) clear of every plus
    for _ in range(h * w // 6):
        rr = rng.randrange(h); cc = rng.randrange(w)
        if g[rr][cc] == 5 and all(
                abs(rr - pr) + abs(cc - pc) > prad + 3 for pr, pc, prad in placed):
            g[rr][cc] = rng.choice([0, 5])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one row must hold a cluster of >=2 color-2 cells within 4 columns
    (so the rule infers a plus and paints its arms 5->8), else it's a no-op."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    for row in grid:
        cols = [c for c in range(w) if row[c] == 2]
        # greedily cluster columns that are within 4 of the cluster's first col
        cur = []
        for c in cols:
            if not cur or c - cur[0] <= 4:
                cur.append(c)
            else:
                if len(cur) >= 2:
                    return []
                cur = [c]
        if len(cur) >= 2:
            return []
    return ["no row has a 2-cell cluster of >=2 within 4 cols: rule infers no plus"]


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 5)
    if name == "no_pluses":
        return g
    if name == "single_pixel":
        g[6][6] = 2
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g
