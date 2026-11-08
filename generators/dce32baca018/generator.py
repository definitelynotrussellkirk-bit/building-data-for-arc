"""Generator for additional_bank:M3.

Rule: find 5-divider column; for each cell, mirror left side to right
where right is 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_blob, right_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dce32baca018"
VERSION = "2.1.0"
TASK_ID = "dce32baca018"
SUMMARY = (
    "0-bg grid (h~5-7, w~"
    "7-9, w should be ODD "
    "for a centered "
    "divider) with: (a) "
    "FULL-HEIGHT COLOR-5 "
    "DIVIDER at col w//2 — "
    "every row of col "
    "w//2 painted gray; "
    "(b) LEFT BLOB — 2-4 "
    "CELLS in a single "
    "non-{0, 5} color "
    "placed at random "
    "positions on the "
    "LEFT side (cols 0.."
    "w//2-1) where the "
    "mirrored target on "
    "the right stays in "
    "bounds; (c) RIGHT "
    "SIDE (cols w//2+1.."
    "w-1) is INPUT-EMPTY. "
    "Rule (MIRROR LEFT "
    "BLOB CELLS ACROSS "
    "THE GRAY DIVIDER TO "
    "THE RIGHT): "
    "identify the FULL-"
    "COLUMN GRAY (5) "
    "DIVIDER at col div. "
    "For EACH NON-0 NON-"
    "5 CELL at (r, c) "
    "with c < div: PAINT "
    "(r, 2*div - c) on "
    "the RIGHT with the "
    "SAME COLOR. Divider "
    "and original cells "
    "stay. Net: left "
    "blob appears "
    "mirrored across the "
    "gray divider on the "
    "right side."
)

INVARIANTS = [
    "exactly one full-column 5-divider",
    "left side has 2-4 cells of 1-2 colors",
    "right side is fully 0 (so mirror has somewhere to write)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_blob", "right_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "left_blob_centered_div",
                       "valid": "left_blob_centered_div"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
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
        h = ctx.draw_int("grid_h", 5, 5)
        w = ctx.draw_choice("grid_w", [7])
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_choice("grid_w", [9])
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_choice("grid_w", [7, 9])
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    div = w // 2
    for r in range(h):
        g[r][div] = 5
    color = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
    n = rng.randint(2, 4)
    placed = 0
    while placed < n:
        r = rng.randint(0, h - 1); c = rng.randint(0, div - 1)
        if g[r][c] != 0: continue
        mc = 2 * div - c
        if not (0 <= mc < w): continue
        g[r][c] = color; placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if w % 2 == 0:
        msgs.append("mirror-divider grid width is even; divider is not centered")
    full = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(full) != 1:
        msgs.append("expected exactly one full-height color-5 divider")
        return msgs
    div = full[0]
    if div != w // 2:
        msgs.append("divider is not at the center column")
    left = [(r, c) for r in range(h) for c in range(div)
            if grid[r][c] not in (0, 5)]
    if not (2 <= len(left) <= 4):
        msgs.append("left blob does not have 2-4 non-bg cells")
    for r, c in left:
        mc = 2 * div - c
        if not (0 <= mc < w):
            msgs.append("left blob has no in-bounds mirrored target")
            break
    if any(grid[r][c] != 0 for r in range(h) for c in range(div + 1, w)):
        msgs.append("right side should be empty in the input")
    return msgs


def _draw_from_degenerate(name, rng):
    h, w = 6, 8
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # left blob without divider → no axis to mirror across
        g[1][1] = 4; g[2][2] = 4; g[4][1] = 4
        return g
    if name == "no_blob":
        # divider but no left cells → nothing to mirror
        for r in range(h): g[r][w // 2] = 5
        return g
    if name == "right_already_filled":
        # both sides populated → mirror collides with existing right cells
        for r in range(h): g[r][w // 2] = 5
        g[1][1] = 4; g[2][2] = 4
        g[1][w - 2] = 6; g[2][w - 3] = 6
        return g
    return g
