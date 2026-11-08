"""Generator for a36cd7dd8e82 — smear cells rightward to color-8 wall.

Rule: find color-8 cells (the wall). Find all non-0 non-8 cells (the
sources). For each source, copy itself rightward to fill subsequent
columns in the same row, stopping just before any wall cell. Sources
in different rows operate independently. Multiple sources in same row
combine their smears (later overrides earlier in column order).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a36cd7dd8e82"
VERSION = "2.1.0"  # keep every source >=1 col left of the wall (col <= wall_col-2) so the block can shift >=1 step; guarantee >=1 source -> rule always smears (was: sources hugged the wall -> t=0 -> identity)
TASK_ID = "a36cd7dd8e82"

SUMMARY = (
    "0-bg grid (h×w, ~4-7 by ~9-13) with: (a) a full-height "
    "vertical WALL of color 8 (cyan) at some column near the "
    "right side; (b) 1-3 'source' rows containing 1-3 non-zero "
    "non-8 cells at columns strictly LEFT of the wall. Other "
    "rows are empty. Rule: scan each row independently. For each "
    "non-0 non-8 cell, copy its color rightward into all "
    "subsequent columns of that row until just before the wall "
    "(or grid edge if no wall). Multiple cells in same row "
    "extend their smears; later cells overwrite earlier in "
    "column order. Wall preserved. Output: smeared rows + wall."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one full-height color-8 vertical wall column",
    "1-3 source rows each with 1-3 non-zero non-8 source cells",
    "all source cells are strictly LEFT of the wall column",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_wall", "no_sources", "sources_right_of_wall")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..7", "valid": "3..10"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..18"},
    "n_source_rows":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "palette_kind":   {"type": "str", "default": "default", "valid": "default"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "wall_right_sources_left",
                       "valid": "wall_right_sources_left"},
    "n_distinct_colors":{"type": "int", "default": "rng 1..3", "valid": "1..4"},
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
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 9, 10)
        n_source_rows = ctx.draw_int("n_source_rows", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 12, 16)
        n_source_rows = ctx.draw_int("n_source_rows", 2, 4)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 10, 13)
        n_source_rows = ctx.draw_int("n_source_rows", 1, 3)

    # Wall column: somewhere in cols ~60%-95% of w, leaving >=2 cols of room
    # to its left so a source can sit at col <= wall_col-2 and still shift.
    wall_col = rng.randint(max(2, int(w * 0.6)), w - 2)
    g = full_grid(h, w, 0)
    # Vertical wall
    for r in range(h):
        g[r][wall_col] = 8

    # Source rows. Sources must stay >=1 col LEFT of the wall (max col =
    # wall_col-2) so the whole block can shift at least one step before any
    # cell would hit the wall -- otherwise the shift distance t is 0 and the
    # output equals the input (identity).
    max_src_col = wall_col - 2
    source_rows = rng.sample(range(h), min(n_source_rows, h))
    color_pool = [1, 2, 3, 4, 5, 6, 7, 9]
    placed_any = False
    for r in source_rows:
        n_cells = rng.randint(1, 3)
        for _ in range(n_cells):
            c = rng.randint(0, max_src_col)
            if g[r][c] == 0:
                g[r][c] = rng.choice(color_pool)
                placed_any = True
    if not placed_any:
        # guarantee at least one source so the rule has something to smear
        r = source_rows[0]
        g[r][rng.randint(0, max_src_col)] = rng.choice(color_pool)
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """One full-height color-8 wall, >=1 source cell strictly left of it with
    room to shift (col <= wall_col-2). Returns violation list."""
    out = []
    h, w = len(grid), len(grid[0])
    wall_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(wall_cols) != 1:
        out.append(f"expected exactly one full-height wall, got {len(wall_cols)}")
        return out
    wc = wall_cols[0]
    srcs = [(r, c) for r in range(h) for c in range(w)
            if grid[r][c] not in (0, 8)]
    if not srcs:
        out.append("no source cells -> rule is a no-op")
    elif max(c for _, c in srcs) > wc - 2:
        out.append("a source hugs the wall (col > wall_col-2) -> shift t=0 -> identity")
    if any(c > wc for _, c in srcs):
        out.append("source right of wall")
    return out


def _draw_from_degenerate(name, rng):
    h, w = 5, 10
    g = full_grid(h, w, 0)
    if name == "no_wall":
        g[1][1] = 2
        g[2][3] = 4
        return g
    if name == "no_sources":
        for r in range(h):
            g[r][7] = 8
        return g
    if name == "sources_right_of_wall":
        for r in range(h):
            g[r][3] = 8
        g[1][6] = 2  # source on right of wall
        return g
    return g
