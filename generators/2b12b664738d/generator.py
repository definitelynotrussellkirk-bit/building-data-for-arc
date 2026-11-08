"""Generator for arc_puzzle_bank_eighth21:E54.

Complete each same-color diagonal pair into a filled 2x2 square.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_blocks,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_blocks, full_2x2_filled, mixed_color_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2b12b664738d"
VERSION = "1.2.0"
TASK_ID = "2b12b664738d"

SUMMARY = "Complete each same-color diagonal pair into a filled 2x2 square."

INVARIANTS = [
    "background is 0",
    "each active 2x2 block has one same-color diagonal pair",
    "the other diagonal cells are zero",
    "active blocks are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_blocks", "full_2x2_filled", "mixed_color_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "n_blocks":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "separated_diagonal_pairs",
                       "valid": "separated_diagonal_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_blocks|full_2x2_filled|mixed_color_diagonal'},
}


def _free(g, r0, c0):
    h, w = len(g), len(g[0])
    for r in range(max(0, r0 - 1), min(h, r0 + 3)):
        for c in range(max(0, c0 - 1), min(w, c0 + 3)):
            if g[r][c] != 0:
                return False
    return True


def _diag_blocks(grid):
    h, w = len(grid), len(grid[0])
    out = []
    for r in range(h - 1):
        for c in range(w - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a != 0 and a == e and b == 0 and d == 0:
                out.append((r, c, a, "main"))
            if b != 0 and b == d and a == 0 and e == 0:
                out.append((r, c, b, "anti"))
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for same-color diagonal-pair completion."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errors: list[str] = []
    h, w = len(grid), len(grid[0])
    blocks = _diag_blocks(grid)
    if difficulty == "hard":
        lo, hi = 3, 4
    elif difficulty == "easy":
        lo, hi = 2, 2
    else:
        lo, hi = 2, 4
    if not (lo <= len(blocks) <= hi):
        errors.append(f"expected {lo}..{hi} isolated diagonal-pair 2x2 blocks, got {len(blocks)}")
    active = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    covered = set()
    for r, c, color, diag in blocks:
        if not (1 <= color <= 9):
            errors.append(f"block at {(r, c)} uses invalid color {color}")
        cells = {(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)}
        nz = {p for p in cells if grid[p[0]][p[1]] != 0}
        if len(nz) != 2:
            errors.append(f"block at {(r, c)} should have exactly one occupied diagonal")
        if covered & nz:
            errors.append("diagonal blocks overlap")
        covered |= nz
    if active != covered:
        errors.append("nonzero cells exist outside recognized diagonal-pair blocks")
    return errors

def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("n_blocks", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("n_blocks", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("n_blocks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = 0
    for _ in range(180):
        if placed >= target:
            break
        r0 = rng.randint(0, h - 2)
        c0 = rng.randint(0, w - 2)
        if not _free(g, r0, c0):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        if rng.random() < 0.5:
            g[r0][c0] = color
            g[r0 + 1][c0 + 1] = color
        else:
            g[r0][c0 + 1] = color
            g[r0 + 1][c0] = color
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_blocks":
        # blank → no diagonal pairs to complete
        return g
    if name == "full_2x2_filled":
        # 2x2 already solid → no empty corners to fill
        for dr in range(2):
            for dc in range(2):
                g[1 + dr][1 + dc] = 4
        return g
    if name == "mixed_color_diagonal":
        # diagonal pair has 2 different colors → "same color" precondition fails
        g[1][1] = 4; g[2][2] = 6
        return g
    return g
