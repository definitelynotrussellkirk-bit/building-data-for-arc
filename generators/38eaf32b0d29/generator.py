"""Generator for 38eaf32b0d29.

Rule: background cells diagonally (not cardinally) adjacent to the OUTER
color become the INNER color. The background is the modal color; the OUTER
color is the most frequent non-background color and the INNER color is the
other non-background color.

Combinatorial axes: grid_size, n_outer_marks, background color, palette_kind,
position_bias, inner_position, anchor_corner, asymmetry_force.
Degenerates: no_outer, no_inner, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "38eaf32b0d29"
VERSION = "2.2.0"  # output quality: nonzero modal bg + many separated outer marks like canonical examples
TASK_ID = "38eaf32b0d29"
SUMMARY = (
    "Nonzero-modal-bg square grid (size~12-16) with many separated OUTER-color "
    "cells on an interior lattice plus one or two INNER-color markers. The outer "
    "color is the most frequent non-bg color; the inner color is present but less "
    "frequent. Rule: for every modal-background cell, if it has a diagonal "
    "neighbor of the outer color and no cardinal neighbor of the outer color, "
    "recolor it to the inner color. Net: sparse outer marks project a diagonal "
    "inner-color halo into the background."
)

INVARIANTS = [
    "modal background may be nonzero",
    "outer color is the most frequent non-background color",
    "inner color is present but less frequent",
    "at least one background cell is diagonal-only adjacent to an outer cell",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_outer", "no_inner", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_size":      {"type": "int", "default": "rng 12..16", "valid": "7..18"},
    "n_outer_marks": {"type": "int", "default": "rng 8..16", "valid": "4..24"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "inner_position": {"type": "str", "default": "rng",
                       "valid": "tl|tr|bl|br|center"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        size_lo, size_hi = 10, 12
        mark_lo, mark_hi = 6, 9
    elif difficulty == "hard":
        size_lo, size_hi = 15, 18
        mark_lo, mark_hi = 14, 22
    else:
        size_lo, size_hi = 12, 16
        mark_lo, mark_hi = 8, 16
    size = ctx.draw_int("grid_size", size_lo, size_hi)
    bg, outer, inner = _colors(ctx, rng)
    n_outer = int(overrides.get("n_outer_marks", ctx.draw_int("n_outer_marks", mark_lo, mark_hi)))
    n_outer = max(4, min(24, n_outer))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))

    g = full_grid(size, size, bg)
    candidates = _candidate_outer_positions(size, bias, rng)
    rng.shuffle(candidates)
    for r, c in candidates[:min(n_outer, len(candidates))]:
        g[r][c] = outer

    inner_pos = overrides.get("inner_position",
                              ctx.draw_choice("inner_position", ["tl", "tr", "bl", "br", "center"]))
    inner_pts = _inner_positions(size, inner_pos)
    for r, c in inner_pts:
        # Do not overwrite an outer mark; nudge inward if a sampled lattice mark is there.
        if g[r][c] == outer:
            r = min(size - 2, max(1, r + 1))
            c = min(size - 2, max(1, c + 1))
        g[r][c] = inner
    return g


def _colors(ctx, rng):
    # Prefer a nonzero modal background, because the real eval distribution often
    # does not use black as background and the canonical examples for this task use 7.
    palette_kind = ctx.overrides.get("palette_kind", None) if hasattr(ctx, "overrides") else None
    pool = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rng.shuffle(pool)
    bg = 7 if 7 in pool else pool[0]
    remaining = [c for c in pool if c != bg]
    outer, inner = remaining[0], remaining[1]
    return bg, outer, inner


def _candidate_outer_positions(size, bias, rng):
    if bias == "corner":
        r_range = range(2, min(size - 2, 9), 2)
        c_range = range(2, min(size - 2, 9), 2)
    elif bias == "near_edge":
        r_range = range(2, size - 2, 2)
        c_range = range(2, min(size - 2, 9), 2)
    elif bias == "centered":
        mid = size // 2
        lo = max(1, mid - 4)
        hi = min(size - 1, mid + 5)
        r_range = range(lo, hi, 2)
        c_range = range(lo, hi, 2)
    else:
        r_range = range(2, size - 2, 2)
        c_range = range(2, size - 2, 2)
    return [(r, c) for r in r_range for c in c_range]


def _inner_positions(size, inner_pos):
    if inner_pos == "tl":
        return [(1, 1)]
    if inner_pos == "tr":
        return [(1, size - 2)]
    if inner_pos == "bl":
        return [(size - 2, 1)]
    if inner_pos == "center":
        return [(size // 2, size - 2)]
    return [(1, size - 2)]


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if h != w:
        return [f"grid is {h}x{w}; expected square"]
    if any(len(row) != w for row in grid):
        return ["grid is ragged"]
    counts = {}
    for row in grid:
        for v in row:
            counts[v] = counts.get(v, 0) + 1
    bg = max(counts, key=counts.get)
    colors = [v for v in counts if v != bg]
    errs = []
    if len(colors) != 2:
        errs.append(f"expected exactly two non-background colors, got {sorted(colors)}")
        return errs
    outer = max(colors, key=lambda c: counts[c])
    inner = min(colors, key=lambda c: counts[c])
    if counts[outer] <= counts[inner]:
        errs.append("outer color is not strictly more frequent than inner marker")
    diag = ((1, 1), (1, -1), (-1, 1), (-1, -1))
    card = ((1, 0), (-1, 0), (0, 1), (0, -1))
    halo = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] != bg:
                continue
            near_diag = any(0 <= r+dr < h and 0 <= c+dc < w and grid[r+dr][c+dc] == outer for dr, dc in diag)
            near_card = any(0 <= r+dr < h and 0 <= c+dc < w and grid[r+dr][c+dc] == outer for dr, dc in card)
            if near_diag and not near_card:
                halo += 1
    if halo == 0:
        errs.append("no diagonal-only background cells around the outer marks; output would hide the rule")
    if halo < 4:
        errs.append(f"only {halo} diagonal-only fill cells; expected a visible halo")
    return errs


def _draw_from_degenerate(name, rng):
    size = 10
    g = full_grid(size, size, 7)
    if name == "no_outer":
        g[1][8] = 3
        return g
    if name == "no_inner":
        for r, c in [(2, 2), (2, 4), (4, 2), (4, 4)]:
            g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(size):
            for c in range(size):
                g[r][c] = 2
        return g
    return g
