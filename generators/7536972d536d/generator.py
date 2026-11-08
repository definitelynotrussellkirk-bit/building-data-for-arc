"""Generator for arc_additional_puzzles_21_set13_bundle:E88 — Mirror non-{0,8} across full 8-row.

Rule: find full row or col of 8s; mirror each non-{0,8} cell across.

Combinatorial axes (8): grid_h, grid_w, palette_kind, orientation,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_content, content_on_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7536972d536d"
VERSION = "2.1.0"
TASK_ID = "7536972d536d"
SUMMARY = (
    "0-bg grid (h~7-9, w=9) with EXACTLY ONE "
    "FULL-WIDTH color-8 ROW (or full-height color-8 "
    "COL — orientation chosen randomly) acting as a "
    "DIVIDER. On ONE SIDE of the divider (top half if "
    "row, left half if col), 2-3 ISOLATED CELLS in "
    "various non-{0, 8} colors are placed at random "
    "positions. The OPPOSITE side is all-0. Rule: for "
    "each non-{0, 8} cell on the content side, MIRROR "
    "it across the 8-divider — paint a copy at the "
    "reflected position on the other side, preserving "
    "its color. The divider itself stays color 8; "
    "originals stay. Net: the empty half fills with a "
    "mirror image of the content half, with the cyan "
    "row/col as the axis of symmetry."
)

INVARIANTS = [
    "exactly one full row or full column of 8s",
    "exactly 2-3 non-{0,8} content cells on one side of the divider",
    "every content cell has an in-bounds mirror target on the empty side",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_content", "content_on_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "9", "valid": "9..9"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "orientation":    {"type": "str", "default": "rng row|col", "valid": "row|col"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "8_divider_with_one_side_content",
                       "valid": "8_divider_with_one_side_content"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_divider|no_content|content_on_both_sides'},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
    w = 9
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    orientation = overrides.get("orientation") or ctx.draw_choice("orientation", ("row", "col"))
    palette = [1, 2, 3, 4, 5, 6, 7, 9]
    n_cells = rng.randint(2, 3)
    if orientation == "row":
        gr = h // 2
        for c in range(w):
            g[gr][c] = 8
        # For even h, row 0 would mirror below the board when gr=h//2.
        # Restrict to the rows whose reflected partner exists.
        r_min = max(0, 2 * gr - (h - 1))
        candidates = [(r, c) for r in range(r_min, gr) for c in range(w)]
        rng.shuffle(candidates)
        for r, c in candidates[:n_cells]:
            g[r][c] = rng.choice(palette)
    else:
        gc = w // 2
        for r in range(h):
            g[r][gc] = 8
        c_min = max(0, 2 * gc - (w - 1))
        candidates = [(r, c) for r in range(h) for c in range(c_min, gc)]
        rng.shuffle(candidates)
        for r, c in candidates[:n_cells]:
            g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # content without 8-divider → no axis to mirror across
        g[1][2] = 4
        g[2][3] = 6
        return g
    if name == "no_content":
        # 8-divider alone → nothing to mirror
        for c in range(w):
            g[3][c] = 8
        return g
    if name == "content_on_both_sides":
        # divider with content on both sides → "one side only" precondition fails
        for c in range(w):
            g[3][c] = 8
        g[1][2] = 4
        g[5][6] = 6  # also on bottom side
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if len(full_rows) + len(full_cols) != 1:
        msgs.append("expected exactly one full 8 divider row/column")
        return msgs
    content = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)]
    if not (2 <= len(content) <= 3):
        msgs.append(f"content count {len(content)} outside 2..3")
    if full_rows:
        gr = full_rows[0]
        if any(r >= gr for r, _c, _v in content):
            msgs.append("row-divider content not confined to one side")
        if any(not (0 <= 2 * gr - r < h) for r, _c, _v in content):
            msgs.append("row-divider content has out-of-bounds mirror target")
    else:
        gc = full_cols[0]
        if any(c >= gc for _r, c, _v in content):
            msgs.append("col-divider content not confined to one side")
        if any(not (0 <= 2 * gc - c < w) for _r, c, _v in content):
            msgs.append("col-divider content has out-of-bounds mirror target")
    return msgs
