"""Generator for 19b:m129 — apply upward gravity in each walled chamber.

Rule: an 8-rectangular border + 1-2 internal full-height 8-walls form
chambers. Inside each chamber, all non-bg cells fall upward.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_walls,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_walls, all_at_top.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ed98575459d2"
VERSION = "2.1.0"  # add horizontal internal walls -> 2D chamber grid (canonical pair1/pair3); was vertical-only
TASK_ID = "ed98575459d2"
SUMMARY = (
    "0-bg grid (h~7-9, w~11-14) with: (a) a "
    "SOLID COLOR-8 (cyan) OUTER RECTANGULAR "
    "FRAME (entire row 0, row h-1, col 0, col "
    "w-1 painted 8); (b) 1-2 FULL-HEIGHT "
    "INTERNAL VERTICAL 8-WALLS at random "
    "interior columns, splitting the interior "
    "into 2-3 CHAMBERS; (c) each chamber "
    "contains 1-3 SCATTERED non-bg PEBBLES "
    "in distinct non-{0, 8} colors at "
    "interior rows (2..h-2, never row 1 so "
    "input ≠ output). Rule: APPLY GRAVITY-UP "
    "within EACH CHAMBER independently. Each "
    "chamber's non-bg pebbles fall UPWARD "
    "(toward row 1), preserving column "
    "position. Walls and frame stay. Net: "
    "every chamber gets gravity-up applied; "
    "pebbles stack against the top of each "
    "chamber, keeping their column order."
)

INVARIANTS = [
    "background is 0",
    "outer rectangle is solid 8",
    "1-2 full-height internal vertical 8-walls span row 0 to row h-1",
    "each chamber has 1-3 scattered non-bg pebbles, none in row 1 (so input != output)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_walls", "all_at_top")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "10..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_walls":        {"type": "int", "default": "rng 1..2 vertical", "valid": "0..3"},
    "n_hwalls":       {"type": "int", "default": "rng 0..2 horizontal", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "position_bias":  {"type": "str", "default": "frame_with_internal_walls",
                       "valid": "frame_with_internal_walls"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "2..6"},
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
        h = ctx.draw_int("grid_h", 7, 9); w = ctx.draw_int("grid_w", 11, 12)
        max_h = 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 13, 16)
        max_h = 2
    else:
        h = ctx.draw_int("grid_h", 8, 12); w = ctx.draw_int("grid_w", 11, 14)
        max_h = 2
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c in range(w): g[0][c] = 8; g[h - 1][c] = 8
    for r in range(h): g[r][0] = 8; g[r][w - 1] = 8

    # internal vertical walls (full height) + optional horizontal walls (full
    # width) -> a 2D grid of boxed chambers (canonical has both). Walls spaced so
    # each chamber band is >=3 (interior >=2 -> gravity-up actually moves).
    vcols = _spaced(rng, 2, w - 3, ctx.draw_int("n_walls", 1, 2), 3)
    for c in vcols:
        for r in range(h): g[r][c] = 8
    hrows = _spaced(rng, 2, h - 3, ctx.draw_int("n_hwalls", 0, max_h), 3)
    for r in hrows:
        for c in range(w): g[r][c] = 8

    rbands = _bands([0] + sorted(hrows) + [h - 1])
    cbands = _bands([0] + sorted(vcols) + [w - 1])
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    for (r_lo, r_hi) in rbands:
        for (c_lo, c_hi) in cbands:
            if r_hi < r_lo + 1 or c_hi < c_lo:    # need >=2 interior rows to move
                continue
            n = rng.randint(1, 3)
            placed = 0; attempts = 0
            while placed < n and attempts < 30:
                attempts += 1
                # place below the chamber's top interior row so gravity moves it
                r = rng.randint(r_lo + 1, r_hi)
                c = rng.randint(c_lo, c_hi)
                if g[r][c] != 0: continue
                g[r][c] = rng.choice(palette); placed += 1
    return g


def _spaced(rng, lo, hi, k, gap):
    """Pick up to k values in [lo,hi] pairwise >= gap apart."""
    out = []
    for _ in range(40):
        if len(out) >= k:
            break
        v = rng.randint(lo, hi)
        if all(abs(v - u) >= gap for u in out):
            out.append(v)
    return sorted(out)


def _bands(edges):
    """Interior (lo,hi) bands strictly between consecutive wall lines."""
    return [(edges[i] + 1, edges[i + 1] - 1) for i in range(len(edges) - 1)]


def _draw_from_degenerate(name, rng):
    h, w = 8, 12
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # No outer 8-frame — chamber boundaries are undefined.
        g[3][3] = 4; g[5][7] = 5
        return g
    if name == "no_walls":
        # Frame but no internal walls — single chamber, no chamber-by-chamber gravity.
        for c in range(w): g[0][c] = 8; g[h - 1][c] = 8
        for r in range(h): g[r][0] = 8; g[r][w - 1] = 8
        g[4][3] = 4; g[5][7] = 5
        return g
    if name == "all_at_top":
        # Pebbles already at row 1 — gravity-up is a no-op (input == output).
        for c in range(w): g[0][c] = 8; g[h - 1][c] = 8
        for r in range(h): g[r][0] = 8; g[r][w - 1] = 8
        for r in range(h): g[r][6] = 8
        g[1][3] = 4; g[1][9] = 5
        return g
    return g
