"""Generator for arc_additional_puzzles_21_set18_bundle:E123.

Rule: find full-height col of 8s; for each non-bg/non-8 cell on the
left, place same value at mirror col (2*guide - c) on the right.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, source_on_right, source_on_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e6624fe42974"
VERSION = "2.0.0"
TASK_ID = "e6624fe42974"
SUMMARY = (
    "0-bg grid (h~5-12, w~"
    "9-16) with: (a) ONE "
    "FULL-HEIGHT COLOR-8 "
    "(cyan) DIVIDER COLUMN "
    "at col gc (mid-grid "
    "so mirroring fits "
    "both sides); (b) 2-6 "
    "NON-{0, 8} MARKER "
    "CELLS scattered on "
    "the LEFT side of the "
    "divider (c < gc), each "
    "in a color from "
    "{1..9}\\{0, 8}. RIGHT "
    "side (c > gc) starts "
    "all 0. Each left "
    "marker has a valid "
    "in-bounds mirror "
    "position. Rule "
    "(MIRROR LEFT-MARKER "
    "CELLS ACROSS 8-"
    "DIVIDER): For EACH "
    "LEFT-side non-{0, 8} "
    "marker at (r, c): "
    "COMPUTE mc = 2 * gc - "
    "c (mirror position on "
    "the right). PAINT "
    "g[r][mc] with the "
    "same color (overwriting "
    "the 0). Left markers, "
    "divider stay. Net: "
    "left-side markers "
    "reflect across the "
    "cyan divider to the "
    "right side."
)

# Rivals: 'output is input' refuted by demos with non-trivial reflections.
# 'mirror with 8 color' refuted by demos preserving marker colors.
# 'mirror across grid center' refuted by demos where divider is off-
# center. 'mirror vertically' refuted by demos showing horizontal
# reflection only. 'overwrite left markers' refuted by demos showing
# left preserved. 'mirror only one marker' refuted by demos with all
# left markers reflected. 3 demos with varied divider positions pin
# the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly 1 full-height color-8 column (NOT at left/right edge so mirroring has room)",
    "≥2 non-{0,8} markers on the LEFT side of the divider",
    "right side initially all 0 (so mirrored cells are visible against bg)",
    "each left marker has a valid in-bounds mirror position on the right",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "source_on_right", "source_on_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "13", "valid": "13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..8", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..8", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 9, 11)
        n_cells_lo, n_cells_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 13, 16)
        n_cells_lo, n_cells_hi = 4, 6
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 11, 14)
        n_cells_lo, n_cells_hi = 2, 4
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    # Divider in middle-ish so mirroring fits both sides
    gc = rng.randint(max(2, (w + 1) // 2), w - 3) if w >= 6 else w // 2
    for r in range(h):
        g[r][gc] = 8
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    n_cells = rng.randint(n_cells_lo, n_cells_hi)
    placed = 0
    for _ in range(n_cells * 8):
        if placed >= n_cells:
            break
        # Cell must be left of divider AND its mirror must fit right
        c_min = max(0, 2 * gc - w + 1)
        c_max = gc - 1
        if c_min > c_max:
            break
        c = rng.randint(c_min, c_max)
        r = rng.randint(0, h - 1)
        if g[r][c] != 0:
            continue
        g[r][c] = rng.choice(palette)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 13
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # no full-height 8-col → mirror axis is undefined
        g[1][2] = 3; g[3][4] = 7
        return g
    gc = 6
    for r in range(h):
        g[r][gc] = 8
    if name == "source_on_right":
        # all source cells already on the right → rule's "left source" assumption violated
        g[1][8] = 3; g[3][10] = 7
        return g
    if name == "source_on_divider":
        # source overlaps the divider column → ambiguous which side it belongs to
        g[1][gc] = 3
        g[3][2] = 7
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariant check for the mirror-across-8-divider input."""
    errs = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty rectangular list-of-lists"]
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and non-empty"]

    div_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(div_cols) != 1:
        errs.append(f"expected exactly one full-height color-8 divider, found {len(div_cols)}")
        return errs
    gc = div_cols[0]
    if gc == 0 or gc == w - 1:
        errs.append(f"divider must not be on a grid edge, got col {gc}")

    left_markers = []
    right_markers = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v in (0, 8):
                continue
            if c < gc:
                left_markers.append((r, c, v))
            else:
                right_markers.append((r, c, v))

    if len(left_markers) < 2:
        errs.append(f"expected at least two left-side non-{{0,8}} markers, found {len(left_markers)}")
    if right_markers:
        errs.append(f"right side should start empty of source markers, found {right_markers[:4]}")

    for r, c, v in left_markers:
        mc = 2 * gc - c
        if not (0 <= mc < w and mc > gc):
            errs.append(f"marker {(r, c, v)} mirrors out of bounds/to wrong side at col {mc}")
        elif grid[r][mc] != 0:
            errs.append(f"mirror target {(r, mc)} should be background 0 before applying rule")
    return errs
