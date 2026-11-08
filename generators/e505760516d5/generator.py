"""Generator for 18b:m121 — fill intersections from frame markers.

Rule: an 8-rectangular frame has 2-color markers on its top row and
left column. For each (top-marker column c, left-marker row r), the
interior cell (r, c) becomes color 3.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_top_markers, no_left_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e505760516d5"
VERSION = "2.1.0"  # healthy but marker counts hardcoded 2-3; rule fills the full top-mark x left-mark intersection grid. Vary marker counts (2-5 by difficulty) and enlarge hard frames for more intersections/output diversity.
TASK_ID = "e505760516d5"
SUMMARY = (
    "0-bg grid containing one rectangular cyan(8) frame. The top row of "
    "the frame has 2-3 color-2 markers replacing 8s at interior columns "
    "{cm}. The left column of the frame has 2-3 color-2 markers "
    "replacing 8s at interior rows {rm}. The frame interior is all 0. "
    "Rule: for each (row r in left-markers, col c in top-markers), if "
    "g[r][c] is 0, set it to color 3. Output is the input with those "
    "intersection cells filled in."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one rectangular cyan(8) frame",
    "2-3 markers (color 2) on top row of frame at distinct interior cols",
    "2-3 markers (color 2) on left column of frame at distinct interior rows",
    "frame interior is bg before the rule fires",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_top_markers", "no_left_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "11..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "8frame_with_top_left_markers",
                       "valid": "8frame_with_top_left_markers"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
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
        fh = ctx.draw_int("frame_h", 7, 7)
        fw = ctx.draw_int("frame_w", 9, 9)
        m_lo, m_hi = 2, 2
    elif difficulty == "hard":
        fh = ctx.draw_int("frame_h", 9, 12)
        fw = ctx.draw_int("frame_w", 12, 15)
        m_lo, m_hi = 3, 5
    else:
        fh = ctx.draw_int("frame_h", 7, 10)
        fw = ctx.draw_int("frame_w", 9, 12)
        m_lo, m_hi = 2, 3
    rng = ctx.draw_rng("layout")
    # Random padding around the frame
    pad_top = rng.randint(1, 2)
    pad_left = rng.randint(1, 3)
    pad_bot = rng.randint(1, 2)
    pad_right = rng.randint(1, 3)
    h = fh + pad_top + pad_bot
    w = fw + pad_left + pad_right
    g = full_grid(h, w, 0)
    r1, c1 = pad_top, pad_left
    r2, c2 = r1 + fh - 1, c1 + fw - 1
    for c in range(c1, c2 + 1): g[r1][c] = 8; g[r2][c] = 8
    for r in range(r1, r2 + 1): g[r][c1] = 8; g[r][c2] = 8
    # markers on top row (interior cols); count varies, capped by interior width
    n_top = min(rng.randint(m_lo, m_hi), c2 - c1 - 1)
    top_cols = rng.sample(range(c1 + 1, c2), n_top)
    for c in top_cols: g[r1][c] = 2
    # markers on left column (interior rows); capped by interior height
    n_left = min(rng.randint(m_lo, m_hi), r2 - r1 - 1)
    left_rows = rng.sample(range(r1 + 1, r2), n_left)
    for r in left_rows: g[r][c1] = 2
    return g


def _draw_from_degenerate(name, rng):
    fh, fw = 7, 9
    h = fh + 2; w = fw + 3
    g = full_grid(h, w, 0)
    r1, c1 = 1, 2; r2, c2 = r1 + fh - 1, c1 + fw - 1
    if name == "no_frame":
        # markers without an 8-frame → no container to fill intersections inside
        for c in [4, 6]: g[r1][c] = 2
        for r in [3, 5]: g[r][c1] = 2
        return g
    if name == "no_top_markers":
        # frame + left markers but no top markers → no column intersections defined
        for c in range(c1, c2 + 1): g[r1][c] = 8; g[r2][c] = 8
        for r in range(r1, r2 + 1): g[r][c1] = 8; g[r][c2] = 8
        for r in [3, 5]: g[r][c1] = 2
        return g
    if name == "no_left_markers":
        # frame + top markers but no left markers → no row intersections defined
        for c in range(c1, c2 + 1): g[r1][c] = 8; g[r2][c] = 8
        for r in range(r1, r2 + 1): g[r][c1] = 8; g[r][c2] = 8
        for c in [4, 6]: g[r1][c] = 2
        return g
    return g
