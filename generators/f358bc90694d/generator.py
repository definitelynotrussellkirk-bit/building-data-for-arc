"""Generator for arc_puzzle_bank_21_set16_bundle:easy_p03.

Rule: left-border seeds beam rightward through zeros until the first
nonzero blocker or the row edge.

Combinatorial axes (8): grid_h, grid_w, palette_kind, row_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, blockers_at_col0, all_rows_blocked_immediately.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance, color_counts, has_row_gap, interior_cells, is_full_frame_component, norm

GENERATOR_ID = "f358bc90694d"
VERSION = "2.1.0"  # light widen: bigger grids/rows + blockers from col 2 (was 6-9 grid, blocker col 3+)
TASK_ID = "f358bc90694d"
SUMMARY = (
    "0-bg grid (h~6-9, w~8-12) with: (a) "
    "3-5 ACTIVE ROWS — for each active row, "
    "a SEED CELL placed at COLUMN 0 painted "
    "in a row-specific non-0 color drawn "
    "from a 4-6 color palette; (b) WITHIN "
    "SOME ACTIVE ROWS (with 50% "
    "probability): a BLOCKER CELL placed at "
    "a random column c ∈ [3, w-1] painted "
    "in a DIFFERENT non-0 color (drawn from "
    "the next color in the palette). The "
    "remaining cells stay bg-0. Each "
    "active row has the seed at col 0 and "
    "optionally a blocker further right. "
    "Rule (EACH LEFT-BORDER SEED BEAMS "
    "RIGHTWARD THROUGH ZEROS UNTIL THE "
    "FIRST NONZERO BLOCKER OR THE GRID "
    "EDGE): for EACH ACTIVE ROW with a "
    "color-C seed at (r, 0): SCAN columns "
    "1..w-1 left-to-right. PAINT each bg-0 "
    "cell with COLOR C until you hit a "
    "NON-0 BLOCKER cell — the blocker "
    "stays unchanged, and the beam STOPS "
    "at the cell BEFORE the blocker (the "
    "blocker is not overwritten). If no "
    "blocker exists, the beam extends to "
    "col w-1. The seed stays at col 0. "
    "Other rows are unchanged. Net: each "
    "active row becomes a horizontal "
    "colored beam from the left edge "
    "until its blocker (or the right "
    "edge)."
)

INVARIANTS = [
    "background is 0",
    "active rows have one nonzero seed in column 0",
    "some active rows contain a later nonzero blocker",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "blockers_at_col0", "all_rows_blocked_immediately")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "row_count":      {"type": "int", "default": "rng 3..5", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "left_seed_with_optional_blocker",
                       "valid": "left_seed_with_optional_blocker"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
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
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        row_count = min(ctx.draw_int("row_count", 2, 3), h)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        row_count = min(ctx.draw_int("row_count", 4, 7), h)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 8, 13)
        row_count = min(ctx.draw_int("row_count", 3, 5), h)
    colors = ctx.draw_distinct_colors("colors", n=row_count + 2, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), row_count)
    rows_with_blockers = []
    for i, r in enumerate(rows):
        g[r][0] = colors[i]
        if rng.choice([True, False]):
            g[r][rng.randint(2, w - 1)] = colors[(i + 1) % len(colors)]
            rows_with_blockers.append((i, r))

    # The rule's stop-at-blocker branch is load-bearing.  The old independent
    # 50/50 draw could emit an all-unblocked episode, especially on easy 2-row
    # examples, so every demo showed only the extend-to-edge branch.
    if not rows_with_blockers:
        i = rng.randrange(len(rows))
        r = rows[i]
        g[r][rng.randint(2, w - 1)] = colors[(i + 1) % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank col 0 → no seeds, rule has nothing to beam
        g[2][5] = 4; g[5][8] = 6
        return g
    if name == "blockers_at_col0":
        # cell at col 0 in some rows is non-zero but not the seed (e.g. blockers stacked) →
        # ambiguous which is the seed
        g[1][0] = 4; g[1][1] = 6   # 4 at col 0, 6 immediately to the right
        g[3][0] = 8; g[3][2] = 3   # 8 at col 0, blocker at col 2 leaves no beam path
        return g
    if name == "all_rows_blocked_immediately":
        # blocker at col 1 in every active row → beam extends 0 cells
        g[1][0] = 4; g[1][1] = 6
        g[3][0] = 8; g[3][1] = 3
        g[5][0] = 9; g[5][1] = 7
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    active = [r for r, row in enumerate(grid) if row[0] != 0]
    if not active:
        errs.append("expected at least one left-border seed")
    blockers = 0
    for r in active:
        row_nonzero = [c for c, v in enumerate(grid[r]) if v != 0]
        if row_nonzero[0] != 0:
            errs.append("active row should start with its seed at column 0")
        later = [c for c in row_nonzero if c > 0]
        if later:
            blockers += 1
            if min(later) < 2:
                errs.append("blockers should be at column >= 2 to leave a visible beam")
    if blockers == 0:
        errs.append("at least one active row should contain a later blocker")
    return errs
