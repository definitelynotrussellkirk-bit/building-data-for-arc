"""Generator for arc_puzzle_bank_sixth21:H36.

Rule: a full color-9 row and full color-9 column define quadrants; the
lower-left quadrant contains a hollow object whose enclosed hole is
filled.

Combinatorial axes (8): grid_h/w, palette_kind, frame_color,
palette_size, position_bias, n_distinct_colors, hole_size, texture.
Degenerates: no_dividers, solid_object, no_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b7f1df7908e0"
# 2.1.0: vary the lower-left hollow object beyond a plain rectangle frame
# (sometimes add an internal divider -> multiple holes) to exercise the
# multi-region fill-holes rule; larger frame-size range.
VERSION = "2.2.0"
TASK_ID = "b7f1df7908e0"
SUMMARY = (
    "0-bg grid (~10-13 × 12-15) split into 4 QUADRANTS "
    "by EXACTLY ONE full-width color-9 (maroon) ROW "
    "and EXACTLY ONE full-height color-9 COLUMN. The "
    "LOWER-LEFT QUADRANT contains EXACTLY ONE HOLLOW "
    "RECTANGULAR FRAME (border-only, ~3×3 to 5×5) in "
    "some non-{0, 9} color, with its strict interior "
    "all-0. Other quadrants are empty. Rule: identify "
    "the hollow object in the lower-left quadrant. "
    "COMPUTE its bbox CROP and SOLID-FILL its interior "
    "(replace 0 cells inside the bbox with the object's "
    "color). PASTE the now-SOLID rectangle into the "
    "LOWER-RIGHT QUADRANT at the same relative bbox "
    "position. The lower-left frame STAYS hollow. The "
    "9-dividers and the original frame stay. Net: the "
    "hollow frame in the bottom-left gets duplicated as "
    "a solid filled rectangle in the bottom-right."
)

# Rivals: 'output is input' refuted by demos (lower-right fills).
# 'fill hole in place' refuted by demos (lower-left stays hollow).
# 'use bg color for fill' refuted by demos (uses object color).
# 'paste to upper-right' refuted by demos showing lower-right. 3
# demos with varied hollow shapes cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "a full color-9 row and full color-9 column define the active quadrant",
    "the active lower-left quadrant contains one hollow object",
    "the object's enclosed zero region is strictly internal",
    "other quadrants are inert for this rule",
]

PALETTE_KINDS = ("default", "warm_frame", "cool_frame", "varied_frame")
DEGENERATE_TEXTURES = ("no_dividers", "solid_object", "no_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10", "valid": "10"},
    "grid_w":         {"type": "int", "default": "12", "valid": "12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_color":    {"type": "color", "default": "rng", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "lower_left",
                       "valid": "lower_left"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2"},
    "hole_size":      {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    color = ctx.draw_color("frame_color", exclude={0, 9})
    if difficulty == "easy":
        h = rng.randint(9, 11); w = rng.randint(10, 12)
        frame_size = rng.choice([(3, 3), (3, 4), (4, 3)])
    elif difficulty == "hard":
        h = rng.randint(13, 18); w = rng.randint(15, 20)
        frame_size = rng.choice([(4, 4), (4, 5), (5, 5), (3, 5), (5, 3),
                                 (5, 6), (6, 5), (6, 6)])
    else:
        h = rng.randint(10, 13); w = rng.randint(12, 15)
        frame_size = rng.choice([(3, 3), (3, 4), (4, 4), (4, 5), (5, 4), (5, 5)])
    g = full_grid(h, w, 0)
    # Divider row in upper half, but still leave enough rows below it for
    # the chosen hollow frame.  The previous code sampled up to h//2 first and
    # then fell back to top=div_row+1; for small h/large frame pairs that made
    # draw_frame write past the bottom edge.
    fh, fw = frame_size
    min_w = 2 * fw + 3  # divider + one-cell left offset + same-relative paste
    if w < min_w:
        w = min_w
        g = full_grid(h, w, 0)
    row_hi = min(h // 2, h - fh - 1)
    if row_hi < 2:
        # Difficulty ranges should make this unreachable, but fail closed into a
        # slightly taller canvas rather than emitting an out-of-bounds frame.
        h = fh + 4
        g = full_grid(h, w, 0)
        row_hi = min(h // 2, h - fh - 1)
    div_row = rng.randint(2, row_hi)
    div_col = rng.randint(w // 2 - 1, w // 2 + 2)
    div_col = max(fw + 1, min(w - fw - 2, div_col))
    for c in range(w):
        g[div_row][c] = 9
    for r in range(h):
        g[r][div_col] = 9
    # Place hollow frame in lower-left quadrant.  Use the same relative `left`
    # when the rule pastes into the lower-right quadrant, so constrain the left
    # offset by BOTH the lower-left room and the lower-right target room.
    max_top = h - fh
    max_left = min(div_col - fw, w - div_col - fw - 1)
    top = rng.randint(div_row + 1, max_top)
    left = rng.randint(1, max_left)
    draw_frame(g, top, left, top + fh - 1, left + fw - 1, color)
    # Sometimes add an internal divider so the frame encloses MULTIPLE holes,
    # exercising the multi-region fill. The fill paints all strictly-internal
    # 0-regions, so the pasted output is still a solid rectangle, but the
    # input object shape varies (and the rule's region-finding is tested).
    if fh >= 4 and fw >= 5 and rng.random() < 0.5:
        # vertical divider at an interior column
        dc = left + rng.randint(2, fw - 2)
        for r in range(top + 1, top + fh - 1):
            g[r][dc] = color
    elif fh >= 5 and fw >= 4 and rng.random() < 0.5:
        # horizontal divider at an interior row
        dr = top + rng.randint(2, fh - 2)
        for c in range(left + 1, left + fw - 1):
            g[dr][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_dividers":
        # hollow frame but no 9-row/9-col → no quadrant defined
        draw_frame(g, 5, 1, 8, 4, 4)
        return g
    if name == "solid_object":
        # 9-dividers + a SOLID block (no hole) → nothing to fill
        for c in range(12):
            g[3][c] = 9
        for r in range(10):
            g[r][6] = 9
        for r in range(5, 9):
            for c in range(1, 5):
                g[r][c] = 4
        return g
    if name == "no_object":
        # 9-dividers but lower-left quadrant is empty → no object
        for c in range(12):
            g[3][c] = 9
        for r in range(10):
            g[r][6] = 9
        return g
    return g

def _full_rows_cols(grid):
    h, w = len(grid), len(grid[0])
    rows = [r for r, row in enumerate(grid) if all(v == 9 for v in row)]
    cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    return rows, cols


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0])
    rows, cols = _full_rows_cols(grid)
    if len(rows) != 1:
        errs.append(f"expected exactly one full color-9 divider row, got {len(rows)}")
    if len(cols) != 1:
        errs.append(f"expected exactly one full color-9 divider col, got {len(cols)}")
    if len(rows) != 1 or len(cols) != 1:
        return errs
    gr, gc = rows[0], cols[0]
    ll = [(r, c, grid[r][c]) for r in range(gr + 1, h) for c in range(gc)
          if grid[r][c] not in (0, 9)]
    if not ll:
        return errs + ["lower-left quadrant has no hollow object"]
    colors = {v for _, _, v in ll}
    if len(colors) != 1:
        errs.append(f"lower-left object has multiple colors {sorted(colors)}")
    color = next(iter(colors))
    rs = [r for r, _, _ in ll]; cs = [c for _, c, _ in ll]
    top, left, bottom, right = min(rs), min(cs), max(rs), max(cs)
    if not (gr < top <= bottom < h and 0 <= left <= right < gc):
        errs.append("hollow object bbox is not fully inside lower-left quadrant")
    for c in range(left, right + 1):
        if grid[top][c] != color or grid[bottom][c] != color:
            errs.append("hollow object top/bottom border incomplete")
            break
    for r in range(top, bottom + 1):
        if grid[r][left] != color or grid[r][right] != color:
            errs.append("hollow object left/right border incomplete")
            break
    interior = [grid[r][c] for r in range(top + 1, bottom) for c in range(left + 1, right)]
    if not interior or 0 not in interior:
        errs.append("hollow object has no strict internal zero region")
    if gc + 1 + left + (right - left) >= w:
        errs.append("same-relative paste into lower-right would be out of bounds")
    # The generator input should not already contain an object in the target quadrant.
    lr = [(r, c) for r in range(gr + 1, h) for c in range(gc + 1, w) if grid[r][c] not in (0, 9)]
    if lr:
        errs.append("lower-right target quadrant is not empty in the input")
    return errs
