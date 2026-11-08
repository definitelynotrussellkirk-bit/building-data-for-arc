"""Generator for arc_additional_puzzles_21_set21_bundle:M141.

Rule: row 0 has 2 palette colors. 1-frame contains 9-seed. From seed
in all 4 cardinal directions, paint cells (alternating palette) until
walls.

Combinatorial axes (8): grid_h/w, palette_kind, frame_size,
palette_size, position_bias, n_distinct_colors, seed_pos, texture.
Degenerates: no_palette, no_frame, no_seed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "0f0d405d5bb8"
VERSION = "2.1.1"  # +self_check
TASK_ID = "0f0d405d5bb8"
SUMMARY = (
    "0-bg grid (h~8-10, w~9-11) "
    "with: (a) ROW 0 cells (0, 1) "
    "and (0, 2) hold 2 DISTINCT "
    "PALETTE COLORS (from {2, 3, "
    "4, 6, 7, 8} — non-1, non-9); "
    "(b) a HOLLOW COLOR-1 (blue) "
    "RECTANGULAR FRAME at "
    "(1, 1)..(h-2, w-2); (c) a "
    "COLOR-9 (maroon) SEED cell "
    "at (h//2, w//2) (center of "
    "frame interior). Rule "
    "(ALTERNATING CARDINAL RAYS "
    "FROM SEED): READ palette = "
    "[g[0][1], g[0][2]]. From "
    "the seed at (sr, sc), WALK "
    "in all 4 CARDINAL "
    "DIRECTIONS (up, down, left, "
    "right) STEP-BY-STEP until "
    "hitting a 1-wall. At step "
    "k (1-indexed), if the cell "
    "is 0, PAINT it with "
    "palette[k % 2]. The seed "
    "and frame stay. Net: "
    "alternating-color rays "
    "fill the frame interior "
    "from seed."
)

# Rivals: 'output is input' refuted by demos (rays painted).
# 'use a fixed color' refuted by demos with alternating 2 colors.
# 'use seed color (9) for rays' refuted. 'rays pass through walls'
# refuted by demos where 1-walls stop the rays. 'alternation period
# is 3 (uses 3 palette colors)' refuted by demos with 2-color period.
# 3 demos with varied palettes + frame sizes pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "row 0 has 2 palette cells at cols 1 and 2 (non-bg, non-1, non-9)",
    "1-frame in body with 9-seed inside",
    "frame interior is non-degenerate (≥1 cell on each cardinal direction from seed)",
]

PALETTE_KINDS = ("default", "warm_palette", "cool_palette", "varied_palette")
DEGENERATE_TEXTURES = ("no_palette", "no_frame", "no_seed")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "7..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_size":     {"type": "str", "default": "fit_grid",
                       "valid": "fit_grid"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "centered",
                       "valid": "centered"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "seed_pos":       {"type": "str", "default": "center", "valid": "center"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 9, 11)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = [2, 3, 4, 6, 7, 8]; rng.shuffle(palette)
    g[0][1] = palette[0]; g[0][2] = palette[1]
    draw_frame(g, 1, 1, h - 2, w - 2, 1)
    # Seed anywhere strictly inside the frame interior (rows 2..h-3,
    # cols 2..w-3). Varying it changes ray lengths in each direction,
    # producing distinct alternating-fill patterns. INVARIANT: every
    # cardinal direction has >=1 interior cell, which holds because the
    # seed stays at least one interior cell away from each wall (rows
    # 3..h-4, cols 3..w-4) so the >=1-cell-per-direction invariant holds.
    sr = rng.randint(3, h - 4)
    sc = rng.randint(3, w - 4)
    g[sr][sc] = 9
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 has palette (non-{0,1,9}) cells at cols 1 and 2; blue (1) frame and maroon (9) seed are present."""
    if not grid or len(grid) < 3 or any(len(row) != len(grid[0]) for row in grid):
        return ["grid too small or not rectangular"]
    errors = []
    h, w = len(grid), len(grid[0])
    if w < 3:
        errors.append("grid too narrow for palette cells at cols 1,2")
        return errors
    p1, p2 = grid[0][1], grid[0][2]
    if p1 == 0 or p1 in (1, 9):
        errors.append(f"palette cell (0,1) should be non-{{0,1,9}}, got {p1}")
    if p2 == 0 or p2 in (1, 9):
        errors.append(f"palette cell (0,2) should be non-{{0,1,9}}, got {p2}")
    has_frame = any(grid[r][c] == 1 for r in range(h) for c in range(w))
    if not has_frame:
        errors.append("no blue (color 1) frame cells found")
    has_seed = any(grid[r][c] == 9 for r in range(h) for c in range(w))
    if not has_seed:
        errors.append("no maroon (color 9) seed cell found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_palette":
        # frame + seed but no palette → alternation source undefined
        draw_frame(g, 1, 1, h - 2, w - 2, 1)
        g[h // 2][w // 2] = 9
        return g
    if name == "no_frame":
        # palette + seed but no 1-frame → no walls to bound rays
        g[0][1] = 4; g[0][2] = 6
        g[h // 2][w // 2] = 9
        return g
    if name == "no_seed":
        # palette + frame but no 9-seed → no rays generated
        g[0][1] = 4; g[0][2] = 6
        draw_frame(g, 1, 1, h - 2, w - 2, 1)
        return g
    return g
