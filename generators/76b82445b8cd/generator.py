"""Generator for S10_M3: recolor body cells using a two-row legend.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, body_no_match, identity_mapping.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "76b82445b8cd"
VERSION = "1.1.1"
TASK_ID = "76b82445b8cd"
SUMMARY = "Rows 0 and 1 define old-to-new color mappings used to recolor the body."
INVARIANTS = [
    "legend pairs are vertically aligned in the first two rows",
    "old and new legend colors are nonzero",
    "body contains mapped and optionally unmapped colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "body_no_match", "identity_mapping")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 4..7", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "two_row_legend",
                       "valid": "two_row_legend"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..7", "valid": "2..9"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rows 0 and 1 both have ≥1 non-zero cell (legend pairs), body (rows 2+) has non-zero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 3:
        return ["grid must have ≥3 rows"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    row0_nonzero = any(grid[0][c] != 0 for c in range(w))
    row1_nonzero = any(grid[1][c] != 0 for c in range(w))
    body_nonzero = any(grid[r][c] != 0 for r in range(2, h) for c in range(w))
    if not row0_nonzero:
        errs.append("row 0 (legend old colors) has no non-zero cells")
    if not row1_nonzero:
        errs.append("row 1 (legend new colors) has no non-zero cells")
    if not body_nonzero:
        errs.append("body (rows 2+) has no non-zero cells to recolor")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        n = min(ctx.draw_int("n_pairs", 2, 2), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n = min(ctx.draw_int("n_pairs", 3, 4), w)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        n = min(ctx.draw_int("n_pairs", 2, 4), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = list(range(w))
    rng.shuffle(cols)
    colors = list(ctx.draw_distinct_colors("colors", n=min(9, n * 2 + 1), exclude={0}))
    old_colors = colors[:n]
    new_colors = colors[n:n * 2]
    for i, c in enumerate(cols[:n]):
        g[0][c] = old_colors[i]
        g[1][c] = new_colors[i]
    palette = old_colors + [colors[-1]]
    for r in range(2, h):
        for c in range(w):
            if rng.random() < 0.35:
                g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # rows 0 and 1 are blank → no mapping defined; rule has nothing to apply
        for r in range(2, h):
            for c in range(w):
                if (r + c) % 3 == 0: g[r][c] = 4
        return g
    if name == "body_no_match":
        # legend present but body uses unmapped colors only → rule has no effect
        g[0][1] = 4; g[1][1] = 6  # 4→6
        g[0][3] = 3; g[1][3] = 8  # 3→8
        # body uses 7 and 9 (not in legend's old set)
        for r in range(3, h):
            g[r][2] = 7; g[r][5] = 9
        return g
    if name == "identity_mapping":
        # legend maps each color to itself → rule is identity
        g[0][1] = 4; g[1][1] = 4
        g[0][3] = 6; g[1][3] = 6
        # body uses 4 and 6
        for r in range(3, h):
            g[r][2] = 4; g[r][5] = 6
        return g
    return g
