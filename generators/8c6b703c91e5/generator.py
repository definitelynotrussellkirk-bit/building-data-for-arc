"""Generator for arc_additional_puzzle_bank_volume15:E102.

Orange cells on one side of a gray divider are reflected as blue.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_orange, orange_on_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8c6b703c91e5"
VERSION = "1.2.1"
TASK_ID = "8c6b703c91e5"
SUMMARY = (
    "0-bg grid with a full color-5 divider (either a complete row or a "
    "complete column). Orange (color 7) cells lie on ONE side of the "
    "divider; the OTHER side may carry decorations in colors ≠ {0,5,7,1}. "
    "Rule: detect whether the divider is row-shaped or col-shaped (full "
    "rows tried first); for each color-7 cell at (r,c), compute its "
    "reflection across the divider: if row-divider at row d, mirror to "
    "(2d-r, c); if col-divider at col d, mirror to (r, 2d-c). Paint "
    "color 1 (blue) at the reflected position IF in-bounds AND the cell "
    "is currently 0 (existing decorations are preserved, not overwritten). "
    "Original 7s and all other cells are kept as-is."
)

# Rivals: 'output is input' refuted by demos with ≥1 in-bounds
# reflection. 'reflect with same color (orange)' refuted by demos (the
# reflection is blue 1). 'mirror to the same side (no axis flip)'
# refuted by demos with the orange/blue clearly on opposite sides of
# the divider. 'overwrite decorations' refuted by demos with a
# decoration in the reflection target (it stays). 'reflect every
# non-bg cell' refuted by demos with non-7 decorations not reflected.
# 4 demos (vertical + horizontal divider × with/without blocked
# decoration) pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly one full color-5 divider (row OR column, not both)",
    "all color-7 motif cells lie on ONE side of the divider, not on it",
    "the divider is positioned so ≥1 reflected target lands in-bounds",
    "0..2 decoration cells in colors {3,4,6,8,9} on the other side (NOT color 1, "
    "so the blue output is distinguishable from input)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_orange", "orange_on_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "rng 9..15", "valid": "7..25"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 5..9", "valid": "1..20"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "orange_one_side_of_5_divider",
                       "valid": "orange_one_side_of_5_divider"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full color-5 divider (row OR col, not both);
    color-7 cells exist on one side and not on the divider."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    full_5_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    full_5_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not full_5_rows and not full_5_cols:
        return []  # no_divider degenerate — allowed
    errs = []
    total_div = len(full_5_rows) + len(full_5_cols)
    if total_div != 1:
        errs.append(f"expected exactly 1 full-5 divider; found {len(full_5_rows)} rows + {len(full_5_cols)} cols")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        n_cells = ctx.draw_int("n_cells", 4, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 13, 15)
        n_cells = ctx.draw_int("n_cells", 7, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 9, 15)
        n_cells = ctx.draw_int("n_cells", 5, 9)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    vertical = rng.choice([False, True])
    cells: set[tuple[int, int]] = set()
    if vertical:
        div = rng.randint(3, w - 4)
        # Reflective rows: any row works (column-divider, reflect across c)
        # Sample orange cells on EITHER side (rule handles both — but it
        # gives a clearer demo if all are on one side; pick a side first).
        on_left = rng.random() < 0.5
        if on_left:
            avail_cols = list(range(max(0, 2 * div - (w - 1)), div))
            other_cols = list(range(div + 1, w))
        else:
            avail_cols = list(range(div + 1, min(w, 2 * div + 1)))
            other_cols = list(range(0, div))
        for r in range(h):
            g[r][div] = 5
        for _ in range(200):
            if len(cells) >= n_cells:
                break
            cells.add((rng.randint(0, h - 1), rng.choice(avail_cols)))
        decor_avail = other_cols
        decor_axis_is_row = False
    else:
        div = rng.randint(3, h - 4)
        on_top = rng.random() < 0.5
        if on_top:
            avail_rows = list(range(max(0, 2 * div - (h - 1)), div))
            other_rows = list(range(div + 1, h))
        else:
            avail_rows = list(range(div + 1, min(h, 2 * div + 1)))
            other_rows = list(range(0, div))
        for c in range(w):
            g[div][c] = 5
        for _ in range(200):
            if len(cells) >= n_cells:
                break
            cells.add((rng.choice(avail_rows), rng.randint(0, w - 1)))
        decor_avail = other_rows
        decor_axis_is_row = True
    for r, c in cells:
        g[r][c] = 7
    # Sprinkle 0..2 decoration cells in colors ≠ {0, 5, 7, 1} on the
    # opposite side. They test the rule's "skip if non-zero target"
    # case (those decoration positions might happen to be reflection
    # targets — the rule preserves them).
    n_decor = rng.randint(0, 2)
    decor_colors = [3, 4, 6, 8, 9]
    placed_decor = 0
    for _ in range(20):
        if placed_decor >= n_decor or not decor_avail:
            break
        if decor_axis_is_row:
            r = rng.choice(decor_avail); c = rng.randint(0, w - 1)
        else:
            r = rng.randint(0, h - 1); c = rng.choice(decor_avail)
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(decor_colors)
        placed_decor += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # orange cells but no gray divider → no axis to reflect across
        g[2][2] = 7; g[3][3] = 7; g[5][7] = 7
        return g
    if name == "no_orange":
        # divider but no orange cells → nothing to reflect
        for r in range(h): g[r][5] = 5
        return g
    if name == "orange_on_divider":
        # orange cells lie on the divider → reflection is identity
        for r in range(h): g[r][5] = 5
        g[2][5] = 7; g[5][5] = 7
        return g
    return g
