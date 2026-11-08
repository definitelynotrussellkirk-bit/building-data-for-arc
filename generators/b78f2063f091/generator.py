"""Generator for arc_puzzle_bank_next21:M10 — 6 panels separated by 9-cols, find pair.

Rule: 6 panels separated by full color-9 columns; each has a small motif.

Combinatorial axes (8): panel_h, n_panels, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, empty_panels, single_panel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b78f2063f091"
# 3.0.0: WRONG task (docstring/structure was a 9-divider panel-pair gallery).
# Actual rule: for each color appearing as exactly 2 objects whose ROW RANGES
# OVERLAP, fill the horizontal gap between them in the overlap rows with that
# color (connecting the pair). Rebuilt to that structure: 0-bg grid with pairs
# of same-color blocks at overlapping row bands separated by a column gap.
VERSION = "3.0.1"
TASK_ID = "b78f2063f091"

SUMMARY = (
    "0-bg grid with 1-3 PAIRS of same-color rectangular BLOCKS. The two "
    "blocks of each pair sit at OVERLAPPING ROW BANDS with a horizontal "
    "COLUMN GAP between them; different pairs use distinct colors and sit in "
    "different row bands. Optionally a non-overlapping decoy pair (same color, "
    "disjoint rows) that the rule leaves alone. Rule: for each color with "
    "exactly two objects whose row ranges overlap, FILL the gap rectangle "
    "between their facing edges (over the overlapping rows) with that color, "
    "bridging the pair into one bar."
)

INVARIANTS = [
    "background is 0",
    "each active pair is two same-color blocks with overlapping row ranges and a column gap",
    "different pairs use distinct colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "non_overlapping", "single_block")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_pairs":        {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "band_h":         {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "= n_pairs", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "overlapping_pairs",
                       "valid": "overlapping_pairs"},
    "texture":        {"type": "str", "default": "degenerate selector",
                       "valid": "no_dividers|empty_panels|single_panel"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: each nonzero color forms at most 2 same-color 4-connected regions."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    from collections import defaultdict
    by_color = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].append((r, c))
    errs = []
    for col, cells in by_color.items():
        cell_set = set(cells)
        visited = set()
        n_comps = 0
        for start in cells:
            if start in visited:
                continue
            n_comps += 1
            stack = [start]
            visited.add(start)
            while stack:
                r, c = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nb = (r + dr, c + dc)
                    if nb in cell_set and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
        if n_comps > 2:
            errs.append(f"color {col} has {n_comps} connected regions, expected ≤2")
    return errs


def _place_pair(g, rng, color, r_band, w):
    """Place two same-color blocks in the given row band with overlapping
    rows and a column gap. r_band = (top, bottom) inclusive."""
    h_top, h_bot = r_band
    band_h = h_bot - h_top + 1
    # left block
    lh = rng.randint(1, band_h)
    lr = rng.randint(h_top, h_bot - lh + 1)
    lw = rng.randint(1, max(1, w // 3))
    lc = rng.randint(0, max(0, w // 2 - lw - 2))
    # right block: rows must overlap with left's rows by >=1
    ov_lo = lr
    ov_hi = lr + lh - 1
    rh = rng.randint(1, band_h)
    rr_lo = max(h_top, ov_lo - (rh - 1))
    rr_hi = min(h_bot - rh + 1, ov_hi)
    if rr_hi < rr_lo:
        rr = lr
        rh = lh
    else:
        rr = rng.randint(rr_lo, rr_hi)
    gap = rng.randint(1, 4)
    rc = lc + lw + gap
    rw = rng.randint(1, max(1, w - rc))
    if rc + rw > w:
        rw = w - rc
    if rw < 1:
        return False
    for r in range(lr, lr + lh):
        for c in range(lc, lc + lw):
            g[r][c] = color
    for r in range(rr, rr + rh):
        for c in range(rc, rc + rw):
            g[r][c] = color
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
        band_h = ctx.draw_int("band_h", 2, 3)
        w = ctx.draw_int("grid_w", 8, 11)
    elif difficulty == "hard":
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
        band_h = ctx.draw_int("band_h", 3, 5)
        w = ctx.draw_int("grid_w", 12, 18)
    else:
        n_pairs = ctx.draw_int("n_pairs", 1, 3)
        band_h = ctx.draw_int("band_h", 2, 4)
        w = ctx.draw_int("grid_w", 9, 14)
    rng = ctx.draw_rng("layout")

    sep = 1  # blank row(s) between bands so pairs are separate components
    h = n_pairs * band_h + (n_pairs - 1) * sep
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_pairs)
    r0 = 0
    for pi in range(n_pairs):
        _place_pair(g, rng, colors[pi], (r0, r0 + band_h - 1), w)
        r0 += band_h + sep
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # lone single cells, no same-color pair -> rule does nothing
        g[1][2] = 4; g[4][7] = 6
        return g
    if name == "non_overlapping":
        # a same-color pair whose row ranges DON'T overlap -> no fill
        for r in range(0, 2):
            g[r][1] = 5
        for r in range(4, 6):
            g[r][7] = 5
        return g
    if name == "single_block":
        # only one block of a color (count != 2) -> rule ignores it
        for r in range(1, 3):
            for c in range(1, 3):
                g[r][c] = 4
        return g
    return g
