"""Generator for 12b:m84 — project 2x2 blocks to mini grid.

Rule: detect 2x2 single-color blocks. Project them to a mini grid:
  - rows of mini grid = sorted unique block-top-row positions
  - cols of mini grid = sorted unique block-top-col positions
  - cell (r, c) = block color if a block sits at that (top_row, top_col)

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, blocks_share_row, blocks_share_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b2d893865427"
VERSION = "2.0.0"
TASK_ID = "b2d893865427"

SUMMARY = (
    "0-bg grid (h, w ~ 9-17) with 3-5 (or "
    "up to 6 hard) SOLID 2×2 BLOCKS placed "
    "at random non-overlapping non-touching "
    "positions (1-cell padding via _free). "
    "Each block is painted entirely in a "
    "DISTINCT non-0 color drawn from a "
    "shuffled palette {1..9}. Block top-"
    "left positions may share rows, share "
    "cols, or be all distinct (per "
    "position_bias). Rule (PROJECT 2×2 "
    "BLOCKS TO A MINI GRID — ROWS = SORTED "
    "UNIQUE BLOCK TOP-ROWS, COLS = SORTED "
    "UNIQUE BLOCK TOP-COLS): scan the grid "
    "for SOLID 2×2 monochromatic BLOCKS. "
    "For EACH block, record its top-left "
    "(top_row, top_col) and color. EXTRACT "
    "SORTED UNIQUE top_row values → "
    "rows[0..M-1]. EXTRACT SORTED UNIQUE "
    "top_col values → cols[0..N-1]. "
    "PRODUCE an M × N OUTPUT grid where "
    "output[r][c] = block_color whose "
    "(top_row, top_col) = (rows[r], "
    "cols[c]), or 0 if no block sits at "
    "that intersection. Net: the scattered "
    "2×2 blocks become a small mini grid "
    "encoding their projection onto unique "
    "row/col positions."
)

# Rivals: 'output is input' refuted by demos (output is small).
# 'recolor blocks to one color' refuted by demos (preserves colors).
# 'output 4x4 fixed' refuted by demos with varying M and N. 'output
# top-left only' refuted by demos with multi-block scatter. 3 demos
# with mix of distinct-row, distinct-col, and shared-row/col blocks
# cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-5 solid 2x2 blocks in distinct non-bg colors",
    "blocks don't touch each other (≥1 bg gap between bboxes)",
    "block positions may share rows OR cols, OR be all distinct",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "blocks_share_row", "blocks_share_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "grid_w":         {"type": "int", "default": "rng 10..12", "valid": "9..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_blocks":       {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "distinct_rows_and_cols",
                       "valid": "distinct_rows_and_cols"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = rng.randint(9, 11); w = rng.randint(9, 11)
        n_blocks = rng.randint(3, 4)
    elif difficulty == "hard":
        h = rng.randint(13, 17); w = rng.randint(13, 17)
        n_blocks = rng.randint(4, 6)
    else:
        h = rng.randint(10, 13); w = rng.randint(10, 13)
        n_blocks = rng.randint(3, 5)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_blocks)
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(300):
        if placed >= n_blocks:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        if not _free(g, r0, c0, r0 + 1, c0 + 1):
            continue
        color = palette[placed]
        for dr in (0, 1):
            for dc in (0, 1):
                g[r0 + dr][c0 + dc] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # Empty grid — rule has no 2x2 blocks to project.
        return g
    if name == "blocks_share_row":
        # Two blocks share a top-row — projection collapses them onto same row.
        for dr in (0, 1):
            for dc in (0, 1): g[1 + dr][1 + dc] = 4
        for dr in (0, 1):
            for dc in (0, 1): g[1 + dr][7 + dc] = 5
        return g
    if name == "blocks_share_col":
        # Two blocks share a top-col — projection collapses them onto same col.
        for dr in (0, 1):
            for dc in (0, 1): g[1 + dr][3 + dc] = 4
        for dr in (0, 1):
            for dc in (0, 1): g[7 + dr][3 + dc] = 5
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    blocks = []
    for r in range(h - 1):
        for c in range(w - 1):
            v = grid[r][c]
            if v != 0 and grid[r + 1][c] == v and grid[r][c + 1] == v and grid[r + 1][c + 1] == v:
                blocks.append((r, c, v))
    lo, hi = {"easy": (3, 4), "hard": (4, 6), None: (3, 5)}.get(difficulty, (3, 5))
    if not (lo <= len(blocks) <= hi):
        errs.append(f"expected {lo}..{hi} solid 2x2 blocks, got {len(blocks)}")
    colors = [v for _, _, v in blocks]
    if len(colors) != len(set(colors)):
        errs.append("2x2 block colors should be distinct")
    for i, (r1, c1, _) in enumerate(blocks):
        for r2, c2, _ in blocks[i + 1:]:
            # Their expanded 1-cell boxes should not overlap/touch.
            if not (r1 + 1 < r2 - 1 or r2 + 1 < r1 - 1 or c1 + 1 < c2 - 1 or c2 + 1 < c1 - 1):
                if max(abs(r1 - r2), abs(c1 - c2)) <= 2:
                    errs.append("2x2 blocks should be visibly separated")
                    return errs
    return errs
