"""Generator for arc_puzzle_bank_21_set14_s:S14_H5 — abs-diff of row profiles → cyan histogram.

Rule: compute the absolute difference between two object row profiles
as a cyan histogram.

Combinatorial axes (8): grid_h, grid_w, palette_kind, profile,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_separator, no_left_object, no_right_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dcfb4c64c914"
VERSION = "2.2.0"  # add executable row-profile invariants and refresh stale fixed-8x15 summary. distinct only 6 + shape-locked-in: profiles came from a FIXED 6-pair bank on a fixed 8x15 grid. Output is the cyan histogram of |left-right| row-profile diffs. Now RANDOM profiles (bars 1..maxw) + varied panel widths/heights/divider -> many distinct outputs."
TASK_ID = "dcfb4c64c914"
SUMMARY = (
    "Variable-size 0-bg grid with a FULL-HEIGHT color-5 "
    "(gray) DIVIDER splitting the canvas into equal-width "
    "LEFT and RIGHT panels. Each panel contains exactly one "
    "LEFT-JUSTIFIED ROW-PROFILE OBJECT (a stack of "
    "horizontal bars of varying lengths, anchored to the "
    "panel's left edge) drawn in some non-bg color — "
    "left object in color A, right object in color B, A "
    "≠ B. Rule: for each row r where either panel has a "
    "bar, compute the ABSOLUTE DIFFERENCE between the "
    "left bar's length and the right bar's length at "
    "that row. PAINT a left-justified BAR of color 8 "
    "(cyan) of that length on row r (in the right "
    "panel's region, starting at col 8). Originals are "
    "cleared. Net: input is two colored row-profile "
    "stacks across a divider; output is a cyan histogram "
    "of their per-row length differences."
)

INVARIANTS = [
    "one full color-5 column splits the grid into two panels",
    "each panel contains exactly one connected nonzero object",
    "the objects are row-left-justified profile shapes",
    "the output is the left-justified cyan histogram of absolute row-profile differences",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_separator", "no_left_object", "no_right_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "= 2*(maxw+1)+1", "valid": "7..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "maxw":           {"type": "int", "default": "rng 4..6", "valid": "3..7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "two_panels_with_separator",
                       "valid": "two_panels_with_separator"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_PROFILE_PAIRS = [
    ([1, 3, 2], [3, 1, 1]),
    ([3, 2, 1], [1, 1, 3]),
    ([2, 4, 1], [1, 2, 3]),
    ([1, 2, 3, 2], [3, 1, 1]),
    ([4, 1, 3], [2, 3, 1, 2]),
    ([2, 1, 4, 3], [1, 3, 2, 1]),
]


def _paint_profile(g, top, left, profile, color):
    for r, count in enumerate(profile):
        for c in range(count):
            g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # RANDOM row profiles (was a fixed 6-pair bank -> distinct 6) + varied dims.
    # Output = cyan histogram of |left_profile - right_profile| per row; each bar
    # length >= 1 so each profile is one connected left-justified component.
    if difficulty == "easy":
        maxw = ctx.draw_int("maxw", 3, 4); hi_rows = 3
    elif difficulty == "hard":
        maxw = ctx.draw_int("maxw", 5, 7); hi_rows = 6
    else:
        maxw = ctx.draw_int("maxw", 4, 6); hi_rows = 5
    pw = maxw + 1                       # each panel is pw wide (bars 1..maxw)
    w = pw * 2 + 1                      # left panel | divider | right panel
    div = pw
    ha = hb = 2
    prof_a = prof_b = [1, 1]
    for _attempt in range(60):
        ha = rng.randint(2, hi_rows); hb = rng.randint(2, hi_rows)
        prof_a = [rng.randint(1, maxw) for _ in range(ha)]
        prof_b = [rng.randint(1, maxw) for _ in range(hb)]
        n = max(ha, hb)
        pa = prof_a + [0] * (n - ha); pb = prof_b + [0] * (n - hb)
        if any(abs(a - b) > 0 for a, b in zip(pa, pb)):
            break   # ensure the diff histogram is non-empty
    h = max(ha, hb) + rng.randint(2, 4)
    colors = rng.sample([1, 2, 3, 4, 6, 7, 9], 2)
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][div] = 5
    _paint_profile(g, rng.randint(0, h - ha), 0, prof_a, colors[0])
    _paint_profile(g, rng.randint(0, h - hb), div + 1, prof_b, colors[1])
    return g


def _row_profiles(grid, div):
    left = []
    right = []
    left_colors = set()
    right_colors = set()
    w = len(grid[0])
    for row in grid:
        lc = 0
        for c in range(div):
            if row[c] == 0:
                break
            lc += 1
            left_colors.add(row[c])
        rc = 0
        for c in range(div + 1, w):
            if row[c] == 0:
                break
            rc += 1
            right_colors.add(row[c])
        # no stray cells after the left-justified run in either panel
        if any(row[c] != 0 for c in range(lc, div)):
            left.append(-1)
        else:
            left.append(lc)
        if any(row[c] != 0 for c in range(div + 1 + rc, w)):
            right.append(-1)
        else:
            right.append(rc)
    return left, right, left_colors, right_colors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    msgs = []
    divs = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(divs) != 1:
        msgs.append(f"expected exactly one full color-5 divider column, found {len(divs)}")
        return msgs
    div = divs[0]
    if div == 0 or div == w - 1 or div != (w - 1) // 2:
        msgs.append("divider should split two non-empty equal-width panels")
    if any(v == 8 for row in grid for v in row):
        msgs.append("input should not contain output histogram color 8")
    left, right, lc, rc = _row_profiles(grid, div)
    if -1 in left or -1 in right:
        msgs.append("panel object rows must be left-justified with no stray cells")
    if not any(left) or not any(right):
        msgs.append("both panels need a non-empty row-profile object")
    if len(lc) != 1 or len(rc) != 1 or lc == rc:
        msgs.append("left and right profiles should use one distinct non-divider color each")
    if not any(abs(a - b) > 0 for a, b in zip(left, right) if a >= 0 and b >= 0):
        msgs.append("row-profile absolute difference is empty")
    return sorted(set(msgs))


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 15, 0)
    if name == "no_separator":
        # both panels filled but no 5-divider → cannot split
        _paint_profile(g, 2, 1, _PROFILE_PAIRS[0][0], 4)
        _paint_profile(g, 2, 9, _PROFILE_PAIRS[0][1], 6)
        return g
    if name == "no_left_object":
        # separator + right object only → no left profile to subtract
        for r in range(8): g[r][7] = 5
        _paint_profile(g, 2, 9, _PROFILE_PAIRS[0][1], 6)
        return g
    if name == "no_right_object":
        # separator + left object only → no right profile to subtract
        for r in range(8): g[r][7] = 5
        _paint_profile(g, 2, 1, _PROFILE_PAIRS[0][0], 4)
        return g
    return g
