"""Generator for arc_puzzle_bank_twentyfirst21:E144 — crop to non-zero bbox.

Rule: output is the input cropped to the bounding box of non-zero cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motif_size,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motif, full_grid_motif, multiple_motifs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b04b767a1685"
VERSION = "2.1.1"  # QUALITY: multi-colour motifs + bigger by difficulty (was 1 colour, small); AXES literals
TASK_ID = "b04b767a1685"

SUMMARY = (
    "0-bg grid with a single connected motif (3-6 cells) in one "
    "non-zero color, surrounded by bg padding. The motif's bbox is "
    "strictly smaller than the grid (so the rule's crop produces a "
    "smaller output). Rule: find the bbox of all non-zero cells. "
    "Output = the subgrid bounded by min/max row and col of non-zero "
    "cells. Output dims = (max_r - min_r + 1) × (max_c - min_c + 1)."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one connected motif (3-6 cells) in some non-zero color",
    "motif has bg padding on at least one side (so output is smaller than input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "full_grid_motif", "multiple_motifs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "motif_size":     {"type": "int", "default": "3-5 easy / 4-8 med / 6-12 hard", "valid": "1..14"},
    "palette_size":   {"type": "int", "default": "1-3 (multi-colour motif)", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "centered_motif",
                       "valid": "centered_motif"},
    "n_distinct_colors": {"type": "int", "default": "1-3", "valid": "1..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_motif|full_grid_motif|multiple_motifs"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one nonzero cell (motif), not all cells filled."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_motif",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    total = h * w
    nonzero = sum(1 for r in range(h) for c in range(w) if grid[r][c] != 0)
    if nonzero == 0:
        errs.append("no nonzero cells found (expected a motif)")
    if nonzero == total:
        errs.append("all cells nonzero (no bg padding; crop would be identity)")
    return errs


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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7); w = ctx.draw_int("grid_w", 6, 7)
        k_lo, k_hi, n_col = 3, 5, 1
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 12, 16)
        k_lo, k_hi, n_col = 6, 12, 3
    else:
        h = ctx.draw_int("grid_h", 8, 11); w = ctx.draw_int("grid_w", 8, 11)
        k_lo, k_hi, n_col = 4, 8, 2
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    k = min(rng.randint(k_lo, k_hi), (h - 1) * (w - 1))   # keep bbox strictly < grid
    cells = _build_motif(rng, k)
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    if sh >= h: sh = h - 1
    if sw >= w: sw = w - 1
    # multi-colour motif: each cell drawn from a small palette (crop rule is
    # colour-agnostic -> output stays the correct bbox crop)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_col)
    r0 = rng.randint(0, max(0, h - sh)); c0 = rng.randint(0, max(0, w - sw))
    for r, c in cells:
        rr, cc = r0 + r - min(rs), c0 + c - min(cs)
        if rr < h and cc < w:
            g[rr][cc] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 7
    g = full_grid(h, w, 0)
    if name == "no_motif":
        # blank → nothing to crop
        return g
    if name == "full_grid_motif":
        # nonzero cells fill the grid → crop is identity
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    if name == "multiple_motifs":
        # two separated motifs → bbox spans both
        g[1][1] = 4; g[1][2] = 4
        g[5][5] = 6; g[5][6] = 6
        return g
    return g
