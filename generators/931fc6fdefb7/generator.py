"""Generator for 67c52801.

Rule: blocks are sorted by size and dropped upward into shelf gaps
sorted by width.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, gap_pattern,
n_distinct_colors.
Degenerates: no_blocks, no_shelf, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import fill_box, full_grid

GENERATOR_ID = "931fc6fdefb7"
VERSION = "3.0.1"  # add self_check  # in_sh=out_sh=1: fixed 12x12 + fixed gaps + fixed blocks. Rule generic (shelf=bottom 2 rows, drop blocks into width-sorted gaps); canonical varies size (4x5..9x12). Vary grid size, K gaps of distinct widths, and K blocks sized gap_width x height so the size-sort <-> width-sort pairing stays consistent (block_i.size divisible by gap_i.width).
TASK_ID = "931fc6fdefb7"
SUMMARY = (
    "0-bg grid (size varies). Bottom two rows are the SHELF (a shelf color); "
    "the row above the bottom has K gaps (runs of 0) of DISTINCT widths "
    "separated by shelf cells. Above the shelf sit K solid blocks in distinct "
    "non-shelf colors, block i sized gap_i.width x h_i (so sizes are strictly "
    "increasing and block_i.size is divisible by gap_i.width). Rule: sort gaps "
    "by width and blocks by size, pair them, and drop each block into its gap. "
    "Grid size, gap widths/positions, block heights and count all vary."
)

INVARIANTS = [
    "the bottom-left color is the shelf color",
    "the row above the bottom contains shelf gaps of distinct widths separated by shelf cells",
    "K blocks with strictly distinct sizes, block_i.size divisible by the i-th-narrowest gap width",
    "block colors are distinct and exclude the shelf color",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_blocks", "no_shelf", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "12", "valid": "12"},
    "grid_w":         {"type": "int", "default": "12", "valid": "12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "gap_pattern":    {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bottom row is uniform non-zero (shelf); penultimate row has ≥1 gap; ≥1 block above."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    bottom = [grid[h-1][c] for c in range(w)]
    if len(set(bottom)) != 1 or bottom[0] == 0:
        errs.append(f"bottom row not uniform non-zero (shelf): values={set(bottom)}")
    else:
        shelf = bottom[0]
        gap_row = [grid[h-2][c] for c in range(w)]
        if 0 not in gap_row:
            errs.append("penultimate row has no 0-gaps for blocks to drop into")
        has_block = any(
            grid[r][c] != 0 and grid[r][c] != shelf
            for r in range(h - 2) for c in range(w)
        )
        if not has_block:
            errs.append("no block cells (non-shelf, non-zero) found above the shelf")
    return errs


def _bands(rng, total, sizes):
    """Start positions for blocks of given widths along `total`, with >=1
    separating cell between consecutive blocks; slack distributed randomly."""
    k = len(sizes)
    used = sum(sizes) + (k - 1)
    if used > total:
        return None
    slack = total - used
    gaps = [0] * (k + 1)
    for _ in range(slack):
        gaps[rng.randint(0, k)] += 1
    tops = []; cur = gaps[0]
    for i, s in enumerate(sizes):
        tops.append(cur); cur += s + 1 + gaps[i + 1]
    return tops


def _free(occ, h, w, r0, c0, bh, bw):
    if r0 < 0 or c0 < 0 or r0 + bh > h or c0 + bw > w:
        return False
    for r in range(max(0, r0 - 1), min(h, r0 + bh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + bw + 1)):
            if occ[r][c]:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 10, 12); K = 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 14, 17)
        K = ctx.draw_int("n_gaps", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
        K = ctx.draw_int("n_gaps", 2, 3)
    gr = h - 2
    for _outer in range(40):
        # gap widths: K distinct, ascending; block i (i-th smallest size) pairs
        # with gap i (i-th narrowest). Heights increasing -> sizes increasing.
        gw = sorted(rng.sample([1, 2, 3, 4], K))
        bh = [rng.randint(2, 3) + i for i in range(K)]
        if bh[-1] > gr - 1:
            continue
        sizes = [gw[i] * bh[i] for i in range(K)]
        if len(set(sizes)) != K:   # need strictly distinct sizes
            continue
        # gaps along row gr (placement order shuffled; rule sorts by width)
        order = list(range(K)); rng.shuffle(order)
        starts = _bands(rng, w, [gw[i] for i in order])
        if starts is None:
            continue
        colors = rng.sample([c for c in range(1, 10)], K + 1)
        shelf = colors[0]; block_colors = colors[1:]
        g = full_grid(h, w, 0)
        for c in range(w):
            g[h - 1][c] = shelf; g[gr][c] = shelf
        for slot, st in zip(order, starts):       # carve the gaps
            for c in range(st, st + gw[slot]):
                g[gr][c] = 0
        # place blocks above the shelf as solid bh x gw rects (size = sizes[i])
        occ = [[False] * w for _ in range(h)]
        for c in range(w):
            occ[gr][c] = True; occ[h - 1][c] = True   # keep blocks off the shelf
        ok = True
        for i in range(K):
            placed = False
            for _ in range(80):
                r0 = rng.randint(0, gr - bh[i]); c0 = rng.randint(0, w - gw[i])
                if _free(occ, h, w, r0, c0, bh[i], gw[i]):
                    for r in range(r0, r0 + bh[i]):
                        for c in range(c0, c0 + gw[i]):
                            g[r][c] = block_colors[i]; occ[r][c] = True
                    placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize shelf-drop layout")


def _build_palette(kind, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 0]
    rng.shuffle(pool)
    return pool


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 12, 0)
    if name == "no_blocks":
        for c in range(12):
            g[11][c] = 5
            g[10][c] = 5
        return g
    if name == "no_shelf":
        g[2][1] = 2
        return g
    if name == "full_grid":
        for r in range(12):
            for c in range(12):
                g[r][c] = 5
        return g
    return g
