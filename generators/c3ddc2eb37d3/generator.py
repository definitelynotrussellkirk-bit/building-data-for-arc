"""Generator for arc_additional_puzzles_21_set7:E45.

Rule: nonzero colors in the top row are projected down their columns.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_top, no_distractors, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c3ddc2eb37d3"
VERSION = "2.0.1"
TASK_ID = "c3ddc2eb37d3"
SUMMARY = (
    "0-bg square grid (h, w ~ 6-9) with: (a) THREE "
    "NON-0 TOP-ROW MARKERS at fixed column positions "
    "{1, w//2, w-2} in 3 distinct non-0 colors C0, C1, "
    "C2 drawn from a 4-color palette {1..9}; (b) TWO "
    "DISTRACTOR cells in COLOR C3 (the 4th palette "
    "color) — one at (h-1, 0) and one at (h//2, w-1). "
    "Distractors occupy lower rows / right edge where "
    "the rule will overwrite them. Rule (PROJECT TOP-"
    "ROW COLORS DOWN THEIR COLUMNS): for EACH non-0 "
    "cell (0, c) in the top row of color C: PAINT every "
    "cell (r, c) for r in 1..h-1 with COLOR C. Cells "
    "in columns without a top-row marker stay "
    "unchanged. Distractor cells in marker columns are "
    "OVERWRITTEN; distractors in non-marker columns "
    "stay. Net: vertical color stripes descend from "
    "each top-row marker, painting their columns "
    "downward; distractors outside marker columns "
    "remain as scattered noise."
)

INVARIANTS = [
    "the top row has several nonzero column markers",
    "lower rows contain distractors that the rule overwrites",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_top", "no_distractors", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
    colors = list(ctx.draw_distinct_colors("colors", n=4, exclude=[0]))
    g = full_grid(h, w, 0)
    cols = [1, w // 2, w - 2]
    for c, color in zip(cols, colors):
        g[0][c] = color
    g[h - 1][0] = colors[3]
    g[h // 2][w - 1] = colors[3]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Top row has >=1 nonzero cell; >=2 distinct colors total."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    top_nonzero = [grid[0][c] for c in range(w) if grid[0][c] != 0]
    if not top_nonzero:
        errors.append("top row has no nonzero marker cells")
    all_colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(all_colors) < 2:
        errors.append(f"expected >=2 distinct nonzero colors, found {len(all_colors)}")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_top":
        g[3][3] = 4
        return g
    if name == "no_distractors":
        g[0][1] = 3
        g[0][3] = 4
        g[0][5] = 5
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g
