"""Generator for arc_puzzle_bank_21_set13_bundle:medium_m04 — area rank recolor (asc, from 1).

Rule: sort blobs ascending by area; recolor smallest=1, next=2, etc.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_areas, single_blob, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "ee850e92b585"
VERSION = "2.1.0"  # vary n_blobs 2-5 (rule ranks any count) + full input colors (rule ignores them)
TASK_ID = "ee850e92b585"
SUMMARY = (
    "0-bg grid (h~8-11, w~"
    "9-12) with 3 BLOBS "
    "of STRICTLY DISTINCT "
    "SIZES drawn from "
    "{2, 3, 4, 5, 6} via "
    "blob-walk, each in a "
    "DISTINCT non-rank "
    "color from {4, 5, "
    "7, 9} (rank colors "
    "are {1, 2, 3} so "
    "input colors don't "
    "overlap output "
    "ranks). Blobs placed "
    "at non-overlapping "
    "positions. Rule "
    "(RANK BLOBS BY AREA "
    "ASCENDING, RECOLOR "
    "BY RANK 1, 2, 3): "
    "identify all "
    "BLOBS. SORT by SIZE "
    "ASCENDING (smallest "
    "first). RECOLOR the "
    "i-th smallest blob "
    "to COLOR i+1 (i.e., "
    "smallest → 1, next "
    "→ 2, largest → 3). "
    "Net: blobs ranked "
    "small→large, "
    "recolored 1→2→3."
)

INVARIANTS = [
    "background is 0",
    "every blob has a strictly distinct size from every other",
    "input colors aren't already the rank colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_areas", "single_blob", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blobs":        {"type": "int", "default": "rng 2..5 by difficulty", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "= n_blobs", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "distinct_size_blobs",
                       "valid": "distinct_size_blobs"},
    "n_distinct_colors": {"type": "int", "default": "= n_blobs", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 9, 11)
        n = ctx.draw_int("n_blobs", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_blobs", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 10, 13)
        n = ctx.draw_int("n_blobs", 3, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # strictly distinct sizes -> unambiguous size ranking
    sizes = rng.sample(range(1, 9), n)
    # input colors are RULE-IGNORED (everything is recolored by rank); use any
    # distinct non-bg colors, incl rank colors 1/2/3 (canonical does, e.g. pair2)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    used: set[tuple[int, int]] = set()
    placed = 0
    for size, color in zip(sizes, palette):
        cells = grow_blob(rng, h, w, used, size, max_attempts=80)
        if cells is None:
            continue
        for r, c in cells:
            g[r][c] = color
        used |= cells
        placed += 1
    if placed < 2:                               # ensure >=2 blobs to rank
        g[1][1] = 4; g[3][3] = 5; g[3][4] = 5
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "tied_areas":
        # 3 blobs same size → rank ordering ambiguous (sort key tied)
        for (r, c) in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4   # size 3
        for (r, c) in [(1, 6), (1, 7), (2, 6)]: g[r][c] = 7   # size 3 (tied)
        for (r, c) in [(6, 3), (6, 4), (7, 3)]: g[r][c] = 9   # size 3 (tied)
        return g
    if name == "single_blob":
        # only 1 blob → trivial ranking, output is just one recoloring to 1
        for (r, c) in [(3, 4), (3, 5), (4, 4), (4, 5)]: g[r][c] = 4
        return g
    if name == "no_blobs":
        # blank → no blobs to rank
        return g
    return g
