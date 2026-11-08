"""Generator for arc_puzzle_bank_21_set18_bundle:easy_p05 — fill diagonal from seeds.

Rule: each seed fills the whole down-right diagonal with the same
row-column offset.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, multi_cell_blobs, seeds_share_diagonal.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3374854ed70d"
VERSION = "1.1.0"
TASK_ID = "3374854ed70d"
SUMMARY = "Singleton seeds on distinct main-diagonal offsets."

INVARIANTS = [
    "background is 0",
    "all nonzero cells are singleton seeds",
    "no two seeds share the same row-minus-column diagonal",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "multi_cell_blobs", "seeds_share_diagonal")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "distinct_diagonal_seeds",
                       "valid": "distinct_diagonal_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        seed_count = ctx.draw_int("seed_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        seed_count = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        seed_count = ctx.draw_int("seed_count", 2, 4)
    colors = ctx.draw_distinct_colors("colors", n=seed_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    used_diag = set()
    for color in colors:
        for _ in range(300):
            r = rng.randrange(h)
            c = rng.randrange(w)
            diag = r - c
            if g[r][c] == 0 and diag not in used_diag:
                g[r][c] = color
                used_diag.add(diag)
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank → no diagonals to fill
        return g
    if name == "multi_cell_blobs":
        # multi-cell blobs → "singleton seed" precondition fails
        g[2][2] = 4; g[2][3] = 4   # pair
        g[5][5] = 6; g[6][5] = 6   # pair
        return g
    if name == "seeds_share_diagonal":
        # 2 seeds on same diagonal → output overlaps (which color owns the cell?)
        g[1][1] = 4   # diag offset 0
        g[3][3] = 6   # diag offset 0 (collides)
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the diagonal-fill seed input."""
    errors = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    w = len(grid[0])
    cells = []
    for r, row in enumerate(grid):
        if len(row) != w:
            errors.append("grid rows must be rectangular")
            return errors
        for c, v in enumerate(row):
            if not isinstance(v, int) or not (0 <= v <= 9):
                errors.append(f"cell ({r},{c}) has invalid color {v!r}")
            if v != 0:
                cells.append((r, c, v))
    if difficulty == "easy":
        lo, hi = 2, 2
    elif difficulty == "hard":
        lo, hi = 3, 4
    else:
        lo, hi = 2, 4
    if not (lo <= len(cells) <= hi):
        errors.append(f"expected {lo}..{hi} singleton seeds for difficulty={difficulty!r}; got {len(cells)}")
    colors = [v for _, _, v in cells]
    if len(colors) != len(set(colors)):
        errors.append("seed colors must be distinct so diagonal ownership is unambiguous")
    diagonals = [r - c for r, c, _ in cells]
    if len(diagonals) != len(set(diagonals)):
        errors.append("no two seeds may share the same row-minus-column diagonal")
    return errors

