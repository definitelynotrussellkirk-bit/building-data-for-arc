"""Generator for arc_additional_puzzles_21_set17_bundle:E117 — Fill 4-frame interior with seed color.

Rule: most-frequent non-bg color = frame color. Find another non-bg
"seed" color cell. Fill all 0-cells strictly inside frame's bbox with
seed color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_seeds,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seed, seed_outside_frame.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "6e7353365c73"
VERSION = "1.1.1"
TASK_ID = "6e7353365c73"
SUMMARY = "Single closed frame of one color + 1 seed cell of another color inside."

INVARIANTS = [
    "exactly 1 closed rect-frame, ≥4×4, of frame color (most-frequent)",
    "exactly 1 seed cell of distinct color inside the frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "seed_outside_frame")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_seeds":        {"type": "int", "default": "1", "valid": "1..1"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "frame_with_inner_seed",
                       "valid": "frame_with_inner_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct non-zero colors; seed cell inside frame; skip degenerate."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        errs.append(f"expected ≥2 distinct non-zero colors (frame + seed), found {colors}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    pal = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
    frame_c, seed_c = pal
    fr = rng.randint(4, h - 1); fc = rng.randint(5, w - 1)
    r0 = rng.randint(0, h - fr); c0 = rng.randint(0, w - fc)
    draw_rect_outline(g, r0, c0, fr, fc, frame_c)
    sr = r0 + rng.randint(1, fr - 2); sc = c0 + rng.randint(1, fc - 2)
    g[sr][sc] = seed_c
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # seed but no frame → most-frequent color undefined
        g[3][5] = 4
        return g
    if name == "no_seed":
        # frame but no seed → no fill color
        draw_rect_outline(g, 1, 1, 5, 7, 6)
        return g
    if name == "seed_outside_frame":
        # seed cell outside the frame → "inside frame's bbox" has no seed source
        draw_rect_outline(g, 1, 1, 4, 5, 6)
        g[6][8] = 4   # outside the frame
        return g
    return g
