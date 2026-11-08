"""Generator for 14bf50a4.

Rule: color-3 shapes below a 9 separator are recolored when they match
the color-1 template above.

Combinatorial axes (8): motif, match_count, grid_h, grid_w, sep_row,
template_position, palette_kind, anchor_corner.
Degenerates: no_template, all_match, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3db1560cd47e"
VERSION = "2.0.1"
TASK_ID = "3db1560cd47e"
SUMMARY = (
    "0-bg grid (h~13-15, w~14-16) with: (a) ROW 1 area "
    "(above sep) has a color-1 (blue) TEMPLATE shape "
    "(5-cell tetromino-style: L, T, corner, stair); (b) "
    "FULL color-9 (maroon) SEPARATOR row at row sep (~5); "
    "(c) BELOW the separator, 1-4 color-3 (green) "
    "CANDIDATE shapes — some matching the template's "
    "normalized shape and some not (a NON-MATCH "
    "distractor). Rule: detect the color-1 template "
    "shape above the sep row. For each color-3 "
    "candidate below: if its normalized shape matches "
    "the template, recolor every cell from 3 to 2 (red). "
    "Non-matching shapes stay color 3."
)

INVARIANTS = [
    "a color-1 template appears above the separator row",
    "a full color-9 row separates template and candidates",
    "candidate shapes below the separator use color 3",
    "only candidates with the same normalized shape as the template become color 2",
]

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 color-1 cell (template), >=1 full color-9 row (separator), >=1 color-3 cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    threes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not ones:
        errs.append("no color-1 template cells found")
    if not sep_rows:
        errs.append("no full color-9 separator row found")
    if not threes:
        errs.append("no color-3 candidate cells found")
    return errs


MOTIFS_DICT = {
    "l": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
    "t": [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)],
    "corner": [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0)],
    "stair": [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
}
NONMATCH = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)]
TEMPLATE_POSITIONS = ("left", "center", "right", "rng")
DEGENERATE_TEXTURES = ("no_template", "all_match", "full_grid")
HELPFUL_TEXTURES = tuple(MOTIFS_DICT.keys())

AXES = {
    "motif":          {"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES)},
    "match_count":    {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "grid_h":         {"type": "int", "default": "rng 13..15", "valid": "11..18"},
    "grid_w":         {"type": "int", "default": "rng 14..16", "valid": "12..18"},
    "sep_row":        {"type": "int", "default": "5", "valid": "4..7"},
    "template_position":{"type": "str", "default": "rng",
                       "valid": "|".join(TEMPLATE_POSITIONS)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "texture":        {"type": "str", "default": "alias for motif",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint(g, cells, r0, c0, color):
    for dr, dc in cells:
        if 0 <= r0 + dr < len(g) and 0 <= c0 + dc < len(g[0]):
            g[r0 + dr][c0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 11, 13
        mc_lo, mc_hi = 1, 1
    elif difficulty == "hard":
        h_lo, h_hi = 15, 18
        mc_lo, mc_hi = 2, 4
    else:
        h_lo, h_hi = 13, 15
        mc_lo, mc_hi = 1, 3
    motif_name = (overrides.get("texture") or
                  overrides.get("motif")
                  or ctx.draw_choice("motif", list(MOTIFS_DICT.keys())))
    motif = MOTIFS_DICT[motif_name]
    match_count = int(overrides.get("match_count",
                                    ctx.draw_int("match_count", mc_lo, mc_hi)))
    match_count = max(1, min(4, match_count))
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", 12, 16)
    sep = int(overrides.get("sep_row", 5))
    sep = max(4, min(sep, h - 4))
    g = full_grid(h, w, 0)
    template_pos = overrides.get("template_position",
                                 ctx.draw_choice("template_position",
                                                 list(TEMPLATE_POSITIONS)))
    if template_pos == "left":
        tc = 1
    elif template_pos == "center":
        tc = max(1, w // 2 - 1)
    elif template_pos == "right":
        tc = max(1, w - 5)
    else:
        tc = rng.randint(1, max(1, w - 4))
    _paint(g, motif, 1, tc, 1)
    for c in range(w):
        g[sep][c] = 9
    slots = [(sep + 2, 1), (sep + 2, 6), (sep + 7, 2), (sep + 7, 8)]
    slots = [(r, c) for r, c in slots if r + 2 < h and c + 2 < w]
    rng.shuffle(slots)
    for r, c in slots[:match_count]:
        _paint(g, motif, r, c, 3)
    if len(slots) > match_count:
        _paint(g, NONMATCH, slots[match_count][0], slots[match_count][1], 3)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    sep = 5
    if name == "no_template":
        for c in range(w):
            g[sep][c] = 9
        _paint(g, MOTIFS_DICT["l"], sep + 2, 2, 3)
        return g
    if name == "all_match":
        _paint(g, MOTIFS_DICT["l"], 1, 2, 1)
        for c in range(w):
            g[sep][c] = 9
        for slot in [(sep + 2, 1), (sep + 2, 6)]:
            _paint(g, MOTIFS_DICT["l"], slot[0], slot[1], 3)
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 9
        return g
    return g
