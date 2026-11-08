"""Generator for arc_puzzle_bank_21_set17_bundle:medium_p05 — corner-marker mirror.

Rule: (0, 0) holds a 'mirror' marker (1=horizontal mirror to right, 2=vertical
mirror to bottom). A motif elsewhere is mirrored to the opposite half.

Combinatorial axes (8): grid_h, grid_w, palette_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_motif, motif_at_corner, motif_already_mirrored.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4b7b6d3a3a14"
VERSION = "2.0.1"
TASK_ID = "4b7b6d3a3a14"
SUMMARY = (
    "0-bg grid (h ∈ 6-8, w ∈ 7-9) with: "
    "(a) ONE CORNER MARKER at FIXED "
    "position (0, 0) — value ∈ {1, 2} "
    "(1 = horizontal mirror to right; "
    "2 = vertical mirror to bottom); "
    "(b) ONE CONNECTED MOTIF in a "
    "non-{0, 1, 2} color drawn from "
    "{3,4,5,6,7,8,9} — 3-5 cells built "
    "by _build_motif random walk, "
    "placed in the UPPER-LEFT QUADRANT "
    "(rows 1..h//2-1, cols 1..w//2-1) "
    "with no overlap. Rule (READ THE "
    "(0,0) MARKER, MIRROR THE MOTIF "
    "TO THE OPPOSITE HALF; ORIGINAL "
    "MOTIF PRESERVED): READ the "
    "(0, 0) marker value. IF MARKER = "
    "1 (HORIZONTAL): for EACH motif "
    "cell at (r, c) PAINT g[r][w-1-c] "
    "with the same color (mirror "
    "LEFT→RIGHT across the central "
    "column). IF MARKER = 2 "
    "(VERTICAL): PAINT g[h-1-r][c] "
    "(mirror TOP→BOTTOM across the "
    "central row). Original motif "
    "cells and (0, 0) marker stay "
    "untouched. Net: a corner code "
    "drives either an LR or UD "
    "reflection of the motif into "
    "the opposite half of the "
    "grid."
)

INVARIANTS = [
    "background is 0",
    "(0, 0) holds marker 1 or 2",
    "exactly one connected motif (3-5 cells) in some non-{0, 1, 2} color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motif", "motif_at_corner", "motif_already_mirrored")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker":         {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "marker_with_motif",
                       "valid": "marker_with_motif"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


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
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 7, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 7, 9)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    g[0][0] = rng.choice([1, 2])
    color = rng.choice([3, 4, 5, 6, 7, 8, 9])
    cells = _build_motif(rng, rng.randint(3, 5))
    rs = [r for r, _ in cells]; cs = [c for _, c in cells]
    sh = max(rs) - min(rs) + 1; sw = max(cs) - min(cs) + 1
    for _ in range(80):
        r0 = rng.randint(1, max(1, h // 2 - sh))
        c0 = rng.randint(1, max(1, w // 2 - sw))
        cells_p = [(r0 + r - min(rs), c0 + c - min(cs)) for r, c in cells]
        if any(g[r][c] != 0 for r, c in cells_p): continue
        for r, c in cells_p:
            g[r][c] = color
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify corner-marker + motif invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    marker = grid[0][0]
    if marker not in (1, 2):
        problems.append(f"(0,0) should be 1 or 2 (mirror marker), found {marker}")
    motif_cells = [grid[r][c] for r in range(len(grid)) for c in range(len(grid[0]))
                   if grid[r][c] not in (0, 1, 2)]
    if not motif_cells:
        problems.append("no motif cells found (expected >=1 non-{0,1,2} cell)")
    return problems


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    g[0][0] = 1   # horizontal mirror marker
    if name == "no_motif":
        # marker but no motif → rule has nothing to mirror, output is the marker alone
        return g
    if name == "motif_at_corner":
        # motif touches the corner cell → marker ambiguously part of motif
        for (r, c) in [(0, 0), (0, 1), (1, 0)]: g[r][c] = 4
        return g
    if name == "motif_already_mirrored":
        # motif AND its mirror already present → rule's mirror operation is identity
        # left motif at (1,1)-(1,3), mirror at (1, w-4)-(1, w-2)
        for c in range(1, 4): g[1][c] = 4
        for c in range(w - 4, w - 1): g[1][c] = 4
        return g
    return g
