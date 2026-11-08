"""Generator for v0_original:medium_03.

Rule: each cell of the input becomes a 2×2 block of the same value in
the output (output dims = 2× input dims).

Combinatorial axes (8): grid_h/w, palette_kind, n_marks, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99da65b07d44"
VERSION = "2.0.1"
TASK_ID = "99da65b07d44"
SUMMARY = (
    "Small 0-bg grid (h, w~2-4) with 2-4 "
    "SINGLE-CELL MARKERS at distinct positions "
    "in random non-zero colors from {1..9}. "
    "Other cells are bg. Rule: UPSCALE the "
    "grid by FACTOR 2 — every cell at (r, c) "
    "with value v becomes a 2×2 BLOCK of "
    "color v at output positions (2r, 2c), "
    "(2r, 2c+1), (2r+1, 2c), (2r+1, 2c+1). "
    "Output dimensions: 2h × 2w. Net: input "
    "is a small markered grid; output is the "
    "same pattern but each cell expanded to "
    "a 2×2 block (2× upscale)."
)

INVARIANTS = [
    "background is 0",
    "grid is small (2..4 rows × 2..4 cols)",
    "1-3 distinct non-bg colors at distinct cells (each cell a single marker)",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("empty_grid", "full_grid", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "grid_w":         {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_marks":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: small grid (h ≤ 6, w ≤ 6); ≥1 non-bg cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h > 6 or w > 6:
        errs.append(f"grid {h}x{w} exceeds expected small size ≤6×6")
    if not any(grid[r][c] != 0 for r in range(h) for c in range(w)):
        errs.append("no non-bg cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 2, 3)
        w = ctx.draw_int("grid_w", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 3, 4)
        w = ctx.draw_int("grid_w", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 2, 4)
        w = ctx.draw_int("grid_w", 2, 4)
    n = ctx.draw_int("n_marks", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    for r, c in cells[:n]:
        g[r][c] = rng.randint(1, 9)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 3, 3
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # all-bg input → output is also all-bg (rule's effect invisible)
        return g
    if name == "full_grid":
        # every cell colored → upscale shows pure tiling, no bg islands
        for r in range(h):
            for c in range(w):
                g[r][c] = ((r * w + c) % 7) + 2
        return g
    if name == "single_cell":
        # only 1 marker → output is one 2×2 block, almost trivial
        g[1][1] = 5
        return g
    return g
