"""Generator for 95990924.

Rule: each solid 2x2 block of 5s gets corner markers: 1=BR, 2=BL, 3=TR,
4=TL diagonal.

Combinatorial axes (8): grid_h/w, n_blocks, block_separation,
position_bias, palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_block, touching_blocks, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "fae5f5cc923f"
VERSION = "3.0.0"  # random scatter placement by default (deterministic biases caused dup layouts, uniq 0.45) + bigger grids + more blocks
TASK_ID = "fae5f5cc923f"
SUMMARY = (
    "0-bg grid (h, w ∈ 6-14, by "
    "difficulty) with: N_BLOCKS ∈ "
    "1-4 SOLID 2×2 COLOR-5 (GRAY) "
    "BLOCKS, each placed at "
    "non-overlapping interior "
    "positions with ≥BLOCK_"
    "SEPARATION (default 5) cells "
    "between block top-lefts, "
    "ensuring ≥2-cell buffer from "
    "all grid edges. Position "
    "biases ∈ {scattered, "
    "diagonal, row_aligned, "
    "centered}. Rule (FOR EACH "
    "0-CELL (R, C), CHECK THE 4 "
    "DIAGONAL 2×2-RELATIONS TO "
    "5-BLOCKS: IF A 2×2 5-BLOCK "
    "SITS AT (R+1..R+2, C+1..C+2) "
    "(BOTTOM-RIGHT DIAG): PAINT "
    "(R,C) = COLOR 1; IF AT "
    "(R+1..R+2, C-2..C-1) "
    "(BOTTOM-LEFT): COLOR 2; IF "
    "AT (R-2..R-1, C+1..C+2) "
    "(TOP-RIGHT): COLOR 3; IF AT "
    "(R-2..R-1, C-2..C-1) (TOP-"
    "LEFT): COLOR 4; PICK THE "
    "FIRST MATCHING IN BR/BL/TR/"
    "TL ORDER): For EACH 0-cell, "
    "check the 4 diagonal "
    "relations to gray 2×2 "
    "blocks. PAINT with the "
    "first-matching corner "
    "marker (1, 2, 3, or 4). "
    "Blocks preserved. Net: each "
    "2×2 block gains 4 distinct-"
    "colored corner markers at "
    "its diagonal 2-cell offsets."
)

# Rivals: 'output is input' refuted by demos (markers added).
# 'mark cardinal corners (not diagonal)' refuted by demos showing the
# 2-cell diagonal offset. 'use color 5 for markers' refuted by demos.
# 'mark only one corner' refuted by demos with all 4 corners marked.
# 'mark every 0-cell' refuted by demos showing far cells stay 0.
# 'mark all 4 corners with the same color' refuted by demos with
# distinct 1/2/3/4 colors at BR/BL/TR/TL. 3 demos with multiple
# 2×2 blocks pin the 4-corner marker semantics.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "1-3 solid 2×2 blocks of color 5",
    "each block has ≥2 cells of buffer from all grid edges (so markers fit)",
    "blocks are separated by ≥5 cells (so corners of different blocks don't overlap)",
]

POSITION_BIASES = ("scattered", "diagonal", "row_aligned", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_block", "touching_blocks", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "8-11 easy / 11-16 med / 14-22 hard", "valid": "6..24"},
    "grid_w":         {"type": "int", "default": "8-11 easy / 11-16 med / 14-22 hard", "valid": "6..24"},
    "n_blocks":       {"type": "int", "default": "1-2 easy / 2-4 med / 3-6 hard", "valid": "1..6"},
    "block_separation":{"type": "int", "default": "5", "valid": "3..8"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}



def _marker_cells_for_block(r0, c0):
    return {(r0 - 1, c0 - 1), (r0 - 1, c0 + 2),
            (r0 + 2, c0 - 1), (r0 + 2, c0 + 2)}


def _block_compatible(r0, c0, placed):
    new_cells = {(r, c) for r in (r0, r0 + 1) for c in (c0, c0 + 1)}
    new_markers = _marker_cells_for_block(r0, c0)
    for pr, pc in placed:
        old_cells = {(r, c) for r in (pr, pr + 1) for c in (pc, pc + 1)}
        if any(abs(r - rr) + abs(c - cc) == 1 or (r, c) == (rr, cc)
               for r, c in new_cells for rr, cc in old_cells):
            return False
        if new_markers & _marker_cells_for_block(pr, pc):
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
        h_lo, h_hi = 8, 11
        nb_lo, nb_hi = 1, 2
        min_blocks = 1
    elif difficulty == "hard":
        h_lo, h_hi = 14, 22
        nb_lo, nb_hi = 3, 6
        min_blocks = 3
    else:
        h_lo, h_hi = 11, 16
        nb_lo, nb_hi = 2, 4
        min_blocks = 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    requested = int(overrides.get("n_blocks", ctx.draw_int("n_blocks", nb_lo, nb_hi)))
    requested = max(min_blocks, min(6, requested))
    bias = overrides.get("texture") or overrides.get("position_bias")
    sep = int(overrides.get("block_separation", 5))
    for target in range(requested, min_blocks - 1, -1):
        for _layout in range(120):
            g = full_grid(h, w, 0)
            placed = []
            for _try in range(600):
                if len(placed) >= target:
                    break
                if bias:
                    r0, c0 = _pick_block_pos(bias, h, w, len(placed), placed, rng)
                else:
                    r0 = rng.randint(2, h - 4)
                    c0 = rng.randint(2, w - 4)
                r0 = max(2, min(r0, h - 4))
                c0 = max(2, min(c0, w - 4))
                if any(abs(r0 - pr) < sep and abs(c0 - pc) < sep for pr, pc in placed):
                    continue
                if not _block_compatible(r0, c0, placed):
                    continue
                draw_rect(g, r0, c0, 2, 2, 5)
                placed.append((r0, c0))
            if len(placed) == target:
                return g
    # Last-resort layout with guaranteed marker-safe blocks for small boards.
    g = full_grid(h, w, 0)
    positions = [(2, 2), (2, max(2, w - 4)), (max(2, h - 4), 2), (max(2, h - 4), max(2, w - 4))]
    placed = []
    for r0, c0 in positions:
        if len(placed) >= min_blocks:
            break
        if _block_compatible(r0, c0, placed):
            draw_rect(g, r0, c0, 2, 2, 5)
            placed.append((r0, c0))
    return g

def _pick_block_pos(bias, h, w, idx, placed, rng):
    if bias == "diagonal":
        steps = idx + 1
        r0 = 2 + (h - 6) * steps // max(1, idx + 2)
        c0 = 2 + (w - 6) * steps // max(1, idx + 2)
    elif bias == "row_aligned":
        r0 = h // 2 + rng.randint(-1, 1)
        c0 = 2 + idx * (w // 4)
    elif bias == "centered":
        r0 = max(2, h // 2 - 1 + rng.randint(-1, 1))
        c0 = max(2, w // 2 - 1 + rng.randint(-1, 1))
    else:
        r0 = rng.randint(2, h - 4)
        c0 = rng.randint(2, w - 4)
    return r0, c0


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_block":
        g[5][5] = 3
        return g
    if name == "touching_blocks":
        draw_rect(g, 3, 3, 2, 2, 5)
        draw_rect(g, 3, 5, 2, 2, 5)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g

def _sc_blocks(grid):
    blocks = []
    h, w = len(grid), len(grid[0])
    for r in range(h - 1):
        for c in range(w - 1):
            if all(grid[rr][cc] == 5 for rr in (r, r + 1) for cc in (c, c + 1)):
                # top-left of an isolated 2x2 block component
                cells = {(rr, cc) for rr in (r, r + 1) for cc in (c, c + 1)}
                if all(not (0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 5 and (rr, cc) not in cells)
                       for rr in range(r - 1, r + 3) for cc in range(c - 1, c + 3)):
                    blocks.append((r, c))
    return blocks

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    blocks = _sc_blocks(grid)
    lo = 1 if difficulty == "easy" else (3 if difficulty == "hard" else 2)
    errs: list[str] = []
    if len(blocks) < lo: errs.append(f"expected at least {lo} isolated 2x2 blocks, got {len(blocks)}")
    marker_sets = [_marker_cells_for_block(r, c) for r, c in blocks]
    for i, a in enumerate(marker_sets):
        for b in marker_sets[i + 1:]:
            if a & b: errs.append("diagonal marker cells overlap between blocks")
    if any(r < 2 or c < 2 or r + 3 >= len(grid) or c + 3 >= len(grid[0]) for r, c in blocks):
        errs.append("2x2 block lacks the two-cell border needed for markers")
    return errs
