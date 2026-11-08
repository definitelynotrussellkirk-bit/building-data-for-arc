"""Generator for arc_puzzle_bank_twelfth21:E81.

Same-color diagonal pairs inside 2x2 boxes are completed to solid blocks.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, full_2x2, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b37eb391ddc0"
VERSION = "1.1.1"
TASK_ID = "b37eb391ddc0"

SUMMARY = "Same-color diagonal pairs inside 2x2 boxes are completed to solid blocks."

INVARIANTS = [
    "background is 0",
    "each target has two opposite same-color corners in a 2x2 box",
    "target 2x2 boxes are separated",
    "the other two cells in each target box are empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "full_2x2", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "isolated_diag_pairs",
                       "valid": "isolated_diag_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 diagonal pair in a 2x2 box (2 same-color cells at opposite corners,
    the other 2 corners empty)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    diag_pair_count = 0
    for r in range(h - 1):
        for c in range(w - 1):
            tl, tr = grid[r][c], grid[r][c + 1]
            bl, br = grid[r + 1][c], grid[r + 1][c + 1]
            # main diagonal pair (tl==br, both non-bg, others are bg)
            if tl != 0 and tl == br and tr == 0 and bl == 0:
                diag_pair_count += 1
            # anti-diagonal pair (tr==bl, both non-bg, others are bg)
            elif tr != 0 and tr == bl and tl == 0 and br == 0:
                diag_pair_count += 1
    if diag_pair_count < 1:
        errs.append(f"expected ≥1 diagonal pair in a 2x2 box; found {diag_pair_count}")
    return errs


def _free_box(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 1), min(h, r + 3)):
        for cc in range(max(0, c - 1), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(120):
        if placed >= target:
            break
        r, c = rng.randint(0, h - 2), rng.randint(0, w - 2)
        if not _free_box(g, r, c):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        if rng.choice([False, True]):
            cells = [(r, c), (r + 1, c + 1)]
        else:
            cells = [(r + 1, c), (r, c + 1)]
        for rr, cc in cells:
            g[rr][cc] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal pairs to complete to solid 2x2
        return g
    if name == "full_2x2":
        # 2x2 already solid → no missing cells to add
        for dr in range(2):
            for dc in range(2):
                g[2 + dr][2 + dc] = 4
        return g
    if name == "single_cell":
        # single cells → not pairs, no diagonal to complete
        g[2][2] = 4
        g[5][5] = 6
        return g
    return g
