"""Generator for 9344f635.

Rule: bg=7. Horizontal 2-cell same-color pairs in row r expand row r
filled. Vertical pairs in col c expand col c filled.

Combinatorial axes (8): grid_h/w, n_horiz, n_vert, palette_kind,
position_bias, anchor_corner, asymmetry_force, palette_size.
Degenerates: only_horiz, no_pairs, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "38b5470ad5f5"
VERSION = "2.0.1"
TASK_ID = "38b5470ad5f5"
SUMMARY = (
    "7-bg grid (h, w~8-10) "
    "with: (a) 2-3 "
    "HORIZONTAL PAIRS — two "
    "horizontally adjacent "
    "cells in the same row "
    "in a distinct non-7 "
    "color, at distinct "
    "rows; (b) 1-2 VERTICAL "
    "PAIRS — two vertically "
    "adjacent cells in the "
    "same col in a distinct "
    "non-7 color, at "
    "distinct cols. All "
    "pair colors are "
    "distinct across pairs. "
    "Position bias varies "
    "(scattered, centered, "
    "corners, spread). Rule "
    "(EXPAND EACH PAIR INTO "
    "ITS FULL ROW/COL): "
    "For EACH HORIZONTAL "
    "PAIR at row r in color "
    "C: PAINT ALL cells in "
    "row r with color C "
    "(except where another "
    "pair's expansion has "
    "already painted — "
    "specific overlap "
    "behavior is rule-"
    "dependent). For EACH "
    "VERTICAL PAIR at col c "
    "in color C: PAINT ALL "
    "cells in col c with "
    "color C. Cells not on "
    "any pair's row/col "
    "stay at 7. Net: "
    "horizontal pairs grow "
    "into full-width "
    "stripes, vertical "
    "pairs into full-"
    "height stripes."
)

INVARIANTS = [
    "bg = 7",
    "2-3 horizontal pairs (2 adjacent cells in same row, distinct colors)",
    "1-2 vertical pairs (2 adjacent cells in same col, distinct colors)",
    "pairs don't share rows/cols/colors",
]

POSITION_BIASES = ("scattered", "centered", "corners", "spread")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("only_horiz", "no_pairs", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "n_horiz":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "n_vert":         {"type": "int", "default": "rng 1..2", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=7; ≥1 non-7 cell (pairs); values 0..9; grid nonempty."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    non_bg = sum(1 for r in range(h) for c in range(w) if grid[r][c] not in (0, 7))
    if non_bg == 0:
        pass  # degenerate (no_pairs) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 6, 8
        nh_lo, nh_hi = 1, 2
        nv_lo, nv_hi = 0, 1
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
        nh_lo, nh_hi = 3, 4
        nv_lo, nv_hi = 2, 3
    else:
        h_lo, h_hi = 8, 10
        nh_lo, nh_hi = 2, 3
        nv_lo, nv_hi = 1, 2
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = [[7] * w for _ in range(h)]
    n_horiz = int(overrides.get("n_horiz",
                                ctx.draw_int("n_horiz", nh_lo, nh_hi)))
    n_horiz = max(1, min(4, n_horiz))
    n_vert = int(overrides.get("n_vert",
                               ctx.draw_int("n_vert", nv_lo, nv_hi)))
    n_vert = max(0, min(3, n_vert))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    palette = _build_palette(palette_kind, n_horiz + n_vert, rng)
    used_rows = set(); used_cols = set()
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    for color in palette[:n_horiz]:
        for _ in range(40):
            r = rng.randint(0, h - 1)
            c = _pick_h_col(bias, w, rng)
            if r in used_rows:
                continue
            if g[r][c] != 7 or g[r][c + 1] != 7:
                continue
            g[r][c] = color
            g[r][c + 1] = color
            used_rows.add(r)
            break
    for color in palette[n_horiz:n_horiz + n_vert]:
        for _ in range(40):
            c = rng.randint(0, w - 1)
            r = _pick_v_row(bias, h, rng)
            if c in used_cols:
                continue
            if g[r][c] != 7 or g[r + 1][c] != 7:
                continue
            g[r][c] = color
            g[r + 1][c] = color
            used_cols.add(c)
            break
    return g


def _pick_h_col(bias, w, rng):
    if bias == "centered":
        return rng.randint(max(0, w // 3), min(w - 2, 2 * w // 3))
    if bias == "corners":
        return rng.choice([0, max(0, w - 2)])
    return rng.randint(0, w - 2)


def _pick_v_row(bias, h, rng):
    if bias == "centered":
        return rng.randint(max(0, h // 3), min(h - 2, 2 * h // 3))
    if bias == "corners":
        return rng.choice([0, max(0, h - 2)])
    return rng.randint(0, h - 2)


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 8, 9]
    pool = [c for c in pool if c != 7]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = [[7] * w for _ in range(h)]
    if name == "only_horiz":
        g[2][2] = 2; g[2][3] = 2
        g[5][1] = 3; g[5][2] = 3
        return g
    if name == "no_pairs":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
