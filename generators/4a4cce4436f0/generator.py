"""Generator for arc_puzzle_bank_twelfth_21_bundle:hard_81_fill_partitioned_chambers_by_internal_keys.

Combinatorial axes (8): grid_h, grid_w, palette_kind, wall_style,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_keys, multiple_keys_per_chamber.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4a4cce4436f0"
VERSION = "2.0.1"
TASK_ID = "4a4cce4436f0"
SUMMARY = (
    "0-bg square grid "
    "(size~8-15) with "
    "COLOR-5 (gray) WALLS "
    "forming a chamber "
    "lattice: 1-3 FULL "
    "HORIZONTAL wall rows "
    "and 1-3 FULL "
    "VERTICAL wall "
    "columns (with ≥2-row/"
    "col separation), "
    "splitting the grid "
    "into N CHAMBERS. "
    "Most chambers have "
    "EXACTLY ONE KEY cell "
    "in a DISTINCT non-"
    "wall color. Some "
    "chambers may be "
    "EMPTY (0 keys) or "
    "have 2 keys "
    "(ambiguous). Rule "
    "(FILL CHAMBERS WITH "
    "EXACTLY ONE KEY "
    "USING THAT KEY's "
    "COLOR): For EACH "
    "CHAMBER (4-conn non-"
    "5 region bounded by "
    "5-walls): if it "
    "contains EXACTLY ONE "
    "non-wall non-0 KEY "
    "cell with color C, "
    "FILL all 0-cells in "
    "the chamber with C. "
    "0-key and 2-key "
    "chambers stay. Walls "
    "and keys stay. Net: "
    "single-keyed chambers "
    "flood with their "
    "key's color."
)

# Rivals: 'fill all chambers with same color' refuted by ≥2 demos with
# different keys per chamber. 'use wall color (5) for fill' refuted by
# any demo (wall stays 5, fill is key color). 'fill ambiguous chambers'
# refuted by ≥1 demo with 0-key or 2-key chambers left blank.
# 'fill across walls' refuted by ≥1 demo where adjacent chamber stays
# untouched despite having a key.
# 4 demos with varied wall configs cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "color 5 cells form full divider walls that partition the grid into chambers",
    "each fillable chamber contains exactly one non-wall nonzero key color",
    "only zero cells inside those single-key chambers are filled",
    "walls and original key cells are preserved",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_keys", "multiple_keys_per_chamber")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "9", "valid": "9..9"},
    "grid_w":         {"type": "int", "default": "9", "valid": "9..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "wall_style":     {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4..4"},
    "position_bias":  {"type": "str", "default": "5walls_with_internal_keys",
                       "valid": "5walls_with_internal_keys"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PALETTES = [
    [2, 3, 4, 6],
    [1, 7, 8, 9],
    [2, 6, 7, 8],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        size = rng.randint(8, 10)
        n_vsplits, n_hsplits = 1, 1
    elif difficulty == "hard":
        size = rng.randint(11, 15)
        n_vsplits = rng.randint(1, 3)
        n_hsplits = rng.randint(1, 3)
    else:
        size = rng.randint(9, 12)
        n_vsplits = rng.randint(1, 2)
        n_hsplits = rng.randint(1, 2)
    g = full_grid(size, size, 0)
    # Pick wall positions: distinct rows/cols, leaving room for chambers ≥1.
    row_choices = list(range(2, size - 2))
    col_choices = list(range(2, size - 2))
    rng.shuffle(row_choices)
    rng.shuffle(col_choices)
    wall_rows = sorted(row_choices[:n_hsplits])
    wall_cols = sorted(col_choices[:n_vsplits])
    # Make sure walls don't sit on consecutive rows/cols.
    wall_rows = [r for i, r in enumerate(wall_rows)
                 if i == 0 or r - wall_rows[i - 1] >= 2]
    wall_cols = [c for i, c in enumerate(wall_cols)
                 if i == 0 or c - wall_cols[i - 1] >= 2]
    for r in wall_rows:
        for c in range(size):
            g[r][c] = 5
    for c in wall_cols:
        for r in range(size):
            g[r][c] = 5
    # Build chamber list (centers between walls).
    row_bounds = [0] + [r + 1 for r in wall_rows] + [size]
    col_bounds = [0] + [c + 1 for c in wall_cols] + [size]
    chambers = []
    for i in range(len(row_bounds) - 1):
        for j in range(len(col_bounds) - 1):
            r1, r2 = row_bounds[i], row_bounds[i + 1] - 1
            c1, c2 = col_bounds[j], col_bounds[j + 1] - 1
            if r1 <= r2 and c1 <= c2 and any(
                g[rr][cc] == 0 for rr in range(r1, r2 + 1)
                                for cc in range(c1, c2 + 1)):
                chambers.append((r1, c1, r2, c2))
    # Pick distinct colors for the chambers (excluding 0 and 5).
    avail = [c for c in [1, 2, 3, 4, 6, 7, 8, 9]]
    rng.shuffle(avail)
    # Mostly fill each chamber with a unique key, but leave a couple
    # ambiguous (0 keys or 2 keys) so the rule's exactly-one constraint
    # is observable in demos.
    n_chambers = len(chambers)
    if n_chambers == 0:
        return g
    # Number of chambers to leave empty (no fill).
    n_empty = rng.randint(0, max(0, n_chambers // 4))
    # Number of chambers with 2 keys (ambiguous).
    n_double = rng.randint(0, max(0, n_chambers // 4))
    chamber_indices = list(range(n_chambers))
    rng.shuffle(chamber_indices)
    empty_set = set(chamber_indices[:n_empty])
    double_set = set(chamber_indices[n_empty:n_empty + n_double])
    color_idx = 0
    for idx, (r1, c1, r2, c2) in enumerate(chambers):
        if idx in empty_set:
            continue
        cells = [(r, c) for r in range(r1, r2 + 1)
                 for c in range(c1, c2 + 1) if g[r][c] == 0]
        if not cells:
            continue
        rng.shuffle(cells)
        col = avail[color_idx % len(avail)]
        color_idx += 1
        r, c = cells[0]
        g[r][c] = col
        if idx in double_set and len(cells) >= 2:
            col2 = avail[color_idx % len(avail)]
            color_idx += 1
            r2_, c2_ = cells[1]
            g[r2_][c2_] = col2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify chamber-fill input invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    problems = []
    flat = [v for row in grid for v in row]
    # color-5 walls must be present
    if 5 not in flat:
        problems.append("no color-5 wall cells found")
    else:
        wall5 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
        if len(wall5) < 2:
            problems.append(f"too few color-5 wall cells ({len(wall5)})")
    # At least one key color (non-0, non-5) must exist
    keys = [v for v in flat if v not in (0, 5)]
    if not keys:
        problems.append("no key cells found (need >=1 non-{0,5} cell)")
    return problems


def _draw_from_degenerate(name, rng):
    g = full_grid(9, 9, 0)
    if name == "no_walls":
        # keys without 5-walls → no chambers, nothing to fill
        g[2][2] = 4; g[2][6] = 6
        g[6][2] = 7; g[6][6] = 8
        return g
    if name == "no_keys":
        # walls without keys → chambers exist but no fill color
        for c in range(9): g[4][c] = 5
        for r in range(9): g[r][4] = 5
        return g
    if name == "multiple_keys_per_chamber":
        # one chamber has 2 different keys → ambiguous, "exactly one" fails
        for c in range(9): g[4][c] = 5
        for r in range(9): g[r][4] = 5
        g[1][1] = 4; g[2][2] = 6  # both in TL chamber
        g[1][7] = 7
        g[7][1] = 8
        return g
    return g
