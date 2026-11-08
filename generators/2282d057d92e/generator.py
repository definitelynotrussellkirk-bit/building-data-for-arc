"""Generator for arc_puzzle_bank_21_set23_bundle:easy_p02.

Rule: sparse row seeds cast their colors rightward until the next seed
or border.

Combinatorial axes (8): grid_h, grid_w, palette_kind, row_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, all_at_right_edge, single_seed_per_row.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2282d057d92e"
VERSION = "2.0.2"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 active row has non-zero seed cells for rightward ray cast."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    active = [r for r in range(h) if any(grid[r][c] != 0 for c in range(w))]
    if not active:
        errs.append("no active rows with non-zero seed cells")
    if not any(_row_has_visible_ray(grid[r], w) for r in active):
        errs.append("no seed has an empty cell to its right before the next seed/border; rule is identity")
    return errs
TASK_ID = "2282d057d92e"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "9-13) with 3-5 ACTIVE "
    "ROWS (chosen randomly) "
    "each containing 1-3 "
    "SEED CELLS at distinct "
    "columns in DISTINCT "
    "colors from {1..9}. "
    "Each row may have "
    "multiple seeds (with "
    "0-cell gaps between "
    "them). Edge case "
    "handled: if a row has "
    "only 1 seed at the "
    "rightmost column, a "
    "second blocker seed "
    "is added. Rule "
    "(CAST EACH SEED's "
    "COLOR RIGHTWARD UNTIL "
    "NEXT SEED OR BORDER): "
    "For EACH ROW r: WALK "
    "left-to-right. For "
    "EACH SEED at (r, c) "
    "with color C: PAINT "
    "every 0-cell to the "
    "RIGHT of (r, c) with "
    "color C, STOPPING at "
    "the next non-0 cell "
    "(another seed) OR the "
    "right border. Seeds "
    "preserved. Net: each "
    "row of seeds becomes "
    "right-flooding color "
    "rays separated by "
    "next-seed blockers."
)

# Rivals: 'output is input' refuted by any demo (rays extend rightward).
# 'cast leftward' refuted by ≥1 demo where left side stays bg.
# 'cast uses different color' refuted by any demo (ray = seed color).
# 'cast extends through other seeds' refuted by any demo where a
# blocker seed truncates the ray. 3 demos with multi-seed rows cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "active rows contain one to three nonzero seeds",
    "each seed has at least one empty cell to its right unless it is a stopper",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "all_at_right_edge", "single_seed_per_row")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..15"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "6..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "row_count":      {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_seeds",
                       "valid": "row_seeds"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 11)
        row_count = min(ctx.draw_int("row_count", 2, 4), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 14, 18)
        row_count = min(ctx.draw_int("row_count", 6, 10), h)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 10, 14)
        row_count = min(ctx.draw_int("row_count", 4, 7), h)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    rows = rng.sample(range(h), row_count)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    for row_index, r in enumerate(rows):
        seed_count = rng.randint(1, 3)
        cols = sorted(rng.sample(range(w), seed_count))
        if not _cols_have_visible_ray(cols, w):
            cols = _force_visible_ray_cols(seed_count, w)
        colors = rng.sample(palette, seed_count)
        for c, color in zip(cols, colors):
            grid[r][c] = color
        if seed_count == 1 and cols[0] == w - 1:
            grid[r][w - 2] = palette[row_index % len(palette)]
    return grid


def _cols_have_visible_ray(cols, w):
    for i, c in enumerate(cols):
        stop = cols[i + 1] if i + 1 < len(cols) else w
        if stop - c > 1:
            return True
    return False


def _force_visible_ray_cols(seed_count, w):
    if seed_count <= 1:
        return [max(0, w - 2)]
    # Put the first seed two columns before a stopper at/near the right edge;
    # this preserves seed_count while guaranteeing at least one painted cell.
    return sorted([max(0, w - seed_count - 1)] + list(range(w - seed_count + 1, w)))


def _row_has_visible_ray(row, w):
    cols = [c for c, v in enumerate(row) if v != 0]
    return _cols_have_visible_ray(cols, w)


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank grid → no seeds to cast, rule is identity
        return g
    if name == "all_at_right_edge":
        # all seeds on the last column → no cell to their right, casts extend 0 cells
        g[1][w - 1] = 4
        g[3][w - 1] = 6
        g[5][w - 1] = 3
        return g
    if name == "single_seed_per_row":
        # one seed per row with no stopper → cast extends all the way to the right border
        # rule effect spans the entire row to the right of seed
        g[1][2] = 4
        g[3][1] = 6
        g[5][3] = 3
        return g
    return g
