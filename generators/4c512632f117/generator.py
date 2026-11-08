"""Generator for 5833af48.

Rule (informal): three components on the grid:
  - source stamp (small box) at top-left with red 2 corners + visible color
  - tile mask (cyan 8 + optional bg) somewhere to the right
  - background-color target rectangle below
The output tiles the stamp through the mask into the target rectangle.

Combinatorial axes (8): grid_h/w, palette_kind, visible_color, target_w,
target_h, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_stamp, no_mask, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "4c512632f117"
VERSION = "3.1.0"  # canonical-scale scene (defect-lint coverage: area 60 vs 306): margins everywhere, 4 red bbox corners, canonical-style {2,8} stamps half the time, template upscaled by cell 1..2, bigger stamps/fund grids; fund/stamp axes declared honestly (old target_h/w axes lied)
TASK_ID = "4c512632f117"
RULE_HASH = "f4651f51f6a5"  # canonical rule this generator was written against
SUMMARY = "Red 2 + visible-color stamp at TL, cyan 8 tile mask, and a background-color target rectangle below. Rule tiles the stamp through the mask into the rectangle."

# Rivals: 'output is the stamp scaled up' refuted by ≥2 demos where
# mask has a 'gap' (bg cell) and target rect has a corresponding hole.
# 'output is the rectangle filled with bg' refuted by any demo (output
# contains stamp colors). 'use red 2 in output' refuted by any demo
# where output uses only visible + bg. 3 demos with varied visible
# color + rect size + mask toggle cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "stamp contains red 2, background 3, and one visible stamp color",
    "tile mask uses cyan 8 to select stamp placements",
    "a background-color rectangle below the tile defines output size",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_stamp", "no_mask", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "fund_h":         {"type": "int", "default": "2 easy / 2-3 med / 3-4 hard",
                       "valid": "2..4"},
    "fund_w":         {"type": "int", "default": "2 easy / 2-3 med / 3-4 hard",
                       "valid": "2..4"},
    "stamp_h":        {"type": "int", "default": "2-3 easy / 2-4 med / 3-5 hard",
                       "valid": "2..5"},
    "stamp_w":        {"type": "int", "default": "2-3 easy / 2-4 med / 3-5 hard",
                       "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "TL_stamp_RT_mask_B_rect",
                       "valid": "TL_stamp_RT_mask_B_rect"},
    "visible_color":  {"type": "color", "default": "rng !{2,3,8}",
                       "valid": "1|4..7|9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    visible = ctx.draw_color("visible_color", exclude={2, 3, 8})
    bg = rng.choice([c for c in (1, 3, 4, 5, 6, 7, 9) if c not in (visible, 2, 8)])
    # Scene mirrors the canonical demos (16x18-scale, margins everywhere):
    # STAMP (red-2 bbox corners; interior canonical-style {2,8} or bg/visible),
    # TEMPLATE right of a 0-gap: a fund_h x fund_w pattern of {8,bg}, upscaled
    # by cell 1..2, and a bg TARGET RECT of (fund_h*sh) x (fund_w*sw) below.
    if difficulty == "easy":
        sh = ctx.draw_int("stamp_h", 2, 3); sw = ctx.draw_int("stamp_w", 2, 3)
        fund_h = ctx.draw_int("fund_h", 2, 2); fund_w = ctx.draw_int("fund_w", 2, 2)
    elif difficulty == "hard":
        sh = ctx.draw_int("stamp_h", 3, 5); sw = ctx.draw_int("stamp_w", 3, 5)
        fund_h = ctx.draw_int("fund_h", 3, 4); fund_w = ctx.draw_int("fund_w", 3, 4)
    else:
        sh = ctx.draw_int("stamp_h", 2, 4); sw = ctx.draw_int("stamp_w", 2, 4)
        fund_h = ctx.draw_int("fund_h", 2, 3); fund_w = ctx.draw_int("fund_w", 2, 3)
    # ARC cap: h = 1 + max(sh, th) + gaps + rect_h (+margins) <= 30 — shave the
    # fund grid first, then the stamp
    while fund_h * sh + sh + 8 > 30 and fund_h > 2:
        fund_h -= 1
    while fund_h * sh + sh + 8 > 30 and sh > 2:
        sh -= 1
    while fund_w * sw + sw + 8 > 30 and fund_w > 2:
        fund_w -= 1
    while fund_w * sw + sw + 8 > 30 and sw > 2:
        sw -= 1
    if sh == 2 and sw == 2:
        sw = 3          # a 2x2 stamp is ALL red corners — no interior pattern

    # stamp pattern (sh x sw): 4 red bbox corners; interior either
    # canonical-style {2,8} (bg-scan skips the whole stamp) or bg/visible
    # (then the FIRST non-{0,2,8} cell row-major must be bg — pin (0,1)).
    canonical_stamp = rng.random() < 0.5
    corners = {(0, 0), (0, sw - 1), (sh - 1, 0), (sh - 1, sw - 1)}
    interior = [(r, c) for r in range(sh) for c in range(sw) if (r, c) not in corners]
    if canonical_stamp:
        stamp = [[8 if rng.random() < 0.6 else 2 for _ in range(sw)] for _ in range(sh)]
    else:
        stamp = [[rng.choice([bg, visible, visible]) for _ in range(sw)] for _ in range(sh)]
        # the rule detects bg as the FIRST non-{0,2,8} cell row-major, so the
        # first INTERIOR stamp cell must be bg (corners are red; (0,1) is a
        # corner when sw==2 — that pin once got overwritten and `visible` was
        # misdetected as bg, crashing the rule on an empty rect-bg)
        pr, pc = interior[0]
        stamp[pr][pc] = bg
    for r, c in corners:
        stamp[r][c] = 2                # red corners define the stamp bbox
    # the stamp must SHOW something after 2->bg mapping: guarantee an interior
    # non-red cell AFTER the corners are painted (corners used to erase them)
    marker = 8 if canonical_stamp else visible
    if not any(stamp[r][c] == marker for r, c in interior):
        r, c = interior[-1]
        if not canonical_stamp and (r, c) == interior[0]:
            r, c = interior[len(interior) // 2]
        stamp[r][c] = marker

    # template (fund_h x fund_w) of {8, bg}, corners 8 so its bbox is full;
    # upscaled by cell 1..2 when it fits (the rule divides exactly)
    mask = [[8 if rng.random() < 0.55 else bg for _ in range(fund_w)] for _ in range(fund_h)]
    mask[0][0] = 8; mask[0][fund_w - 1] = 8
    mask[fund_h - 1][0] = 8; mask[fund_h - 1][fund_w - 1] = 8

    rect_h = fund_h * sh
    rect_w = fund_w * sw
    cell = rng.choice([1, 1, 2])
    th, tw = fund_h * cell, fund_w * cell

    sr, scol = 1, 1                                  # stamp margin (canonical)
    gap = rng.randint(1, 2)
    mask_c = scol + sw + gap
    # template bottom must reach the stamp bottom: the rule's rect = ALL bg
    # cells below the template, and a mode-B stamp carries bg cells that would
    # otherwise pollute the rect bbox (caught by self_check at 1/180)
    top_m = max(sr + rng.randint(0, 1), sr + sh - th)
    rect_top = max(sr + sh + 1, top_m + th) + 1      # empty row below stamp cols
    rect_left = rng.randint(0, 2)
    h = rect_top + rect_h + rng.randint(1, 2)
    w = max(mask_c + tw, rect_left + rect_w) + rng.randint(1, 3)
    if h > 30:
        h = rect_top + rect_h
    if w > 30:
        w = max(mask_c + tw, rect_left + rect_w)
    g = full_grid(h, w, 0)
    for r in range(sh):
        for c in range(sw):
            g[sr + r][scol + c] = stamp[r][c]
    for r in range(th):
        for c in range(tw):
            g[top_m + r][mask_c + c] = mask[r // cell][c // cell]
    fill_box(g, rect_top, rect_left, rect_top + rect_h - 1,
             rect_left + rect_w - 1, bg)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 10, 0)
    if name == "no_stamp":
        g[0][4] = 8
        return g
    if name == "no_mask":
        g[0][0] = 2
        g[1][0] = 4
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(10):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Mirror the rule's reads: red-bbox stamp, an 8-template right of it, and
    a solid bg rect below the template whose dims are exact stamp multiples."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    reds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not reds:
        return ["no red stamp markers"]
    sr2 = max(r for r, _ in reds)
    sc2 = max(c for _, c in reds)
    sh_ = sr2 - min(r for r, _ in reds) + 1
    sw_ = sc2 - min(c for _, c in reds) + 1
    # bg = the rule's scan: first non-{0,2,8} cell row-major
    bg = next((v for row in grid for v in row if v not in (0, 2, 8)), None)
    if bg is None:
        return ["no background color anywhere (rule cannot detect bg)"]
    t8 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8 and c > sc2]
    if not t8:
        return ["no 8-template right of the stamp"]
    atr2 = max(r for r, _ in t8)
    rect = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == bg and r > atr2]
    if not rect:
        return ["no bg target rect below the template"]
    errs = []
    rh_ = max(r for r, _ in rect) - min(r for r, _ in rect) + 1
    rw_ = max(c for _, c in rect) - min(c for _, c in rect) + 1
    if len(rect) != rh_ * rw_:
        errs.append("target rect is not a solid rectangle")
    if rh_ % sh_ or rw_ % sw_:
        errs.append(f"rect {rh_}x{rw_} is not a multiple of the stamp {sh_}x{sw_}")
    return errs
