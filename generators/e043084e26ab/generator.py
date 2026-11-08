"""Generator for arc_additional_puzzle_bank_volume15:M103.

Rule: dr/dc = (3-marker − 2-marker) + (6-marker − 4-marker). For each
1-cell, paint 8 at (r + dr, c + dc) when that cell is 0.

Combinatorial axes (9): grid_h/w, palette_kind, marker_layout,
template_size, palette_size, position_bias, n_distinct_colors,
decoration_color, texture.
Degenerates: missing_marker, zero_combined_delta, no_template.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e043084e26ab"
VERSION = "2.0.1"
TASK_ID = "e043084e26ab"
SUMMARY = (
    "0-bg grid (h ∈ 9-11, w ∈ 11-13) with four singleton marker "
    "cells in colors 2, 3, 4, and 6 at randomized non-overlapping "
    "positions, plus one connected color-1 template (line or L triomino) "
    "and one non-cyan decoration in color 7 or 9. Rule: compute "
    "v = (pos(3)-pos(2)) + (pos(6)-pos(4)); for each color-1 template "
    "cell, paint color 8 at the translated cell when it is in-bounds and "
    "background. Normal generation guarantees the translated template cells "
    "are in-bounds/background so the cyan copy is fully visible."
)

INVARIANTS = [
    "exactly one 1-blob, one each of markers 2,3,4,6",
    "combined delta keeps translated cells in-bounds",
    "decoration is non-{1..6} cell",
]

PALETTE_KINDS = ("default", "tight_template", "wide_grid", "spread_markers")
DEGENERATE_TEXTURES = ("missing_marker", "zero_combined_delta", "no_template")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker_layout":  {"type": "str", "default": "random_nonoverlap", "valid": "random_nonoverlap"},
    "template_size":  {"type": "int", "default": "3", "valid": "3"},
    "decoration_color": {"type": "int", "default": "rng 7|9", "valid": "7|9"},
    "palette_size":   {"type": "int", "default": "6", "valid": "6"},
    "position_bias":  {"type": "str", "default": "random_nonoverlap_visible_copy",
                       "valid": "random_nonoverlap_visible_copy"},
    "n_distinct_colors": {"type": "int", "default": "6", "valid": "6"},
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
        h = ctx.draw_int("grid_h", 9, 9)
        w = ctx.draw_int("grid_w", 11, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    rng = ctx.draw_rng("layout")
    templates = [
        [(0, 0), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0)],
        [(0, 0), (0, 1), (1, 1)],
        [(0, 1), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (2, 0)],
        [(0, 0), (0, 1), (0, 2)],
    ]
    for _ in range(240):
        g = full_grid(h, w, 0)
        # Random template placement
        tpl = rng.choice(templates)
        th = max(r for r, _ in tpl) + 1
        tw = max(c for _, c in tpl) + 1
        tr = rng.randint(0, h - th)
        tc = rng.randint(0, w - tw)
        for dr, dc in tpl:
            g[tr + dr][tc + dc] = 1
        # Random 4 markers (2, 3, 4, 6) at non-overlapping positions
        positions = {}
        ok = True
        for color in [2, 3, 4, 6]:
            placed = False
            for _ in range(60):
                r = rng.randint(0, h - 1)
                c = rng.randint(0, w - 1)
                if g[r][c] != 0:
                    continue
                positions[color] = (r, c)
                g[r][c] = color
                placed = True
                break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        vr, vc = _combined_delta(positions)
        if (vr, vc) == (0, 0):
            continue
        # Check translated template cells in-bounds AND still background.  The
        # old generator checked only bounds, so many examples hid part/all of the
        # cyan copy behind markers, the template itself, or a decoration.
        targets = []
        bad = False
        for dr, dc in tpl:
            tr_t = tr + dr + vr
            tc_t = tc + dc + vc
            if not (0 <= tr_t < h and 0 <= tc_t < w) or g[tr_t][tc_t] != 0:
                bad = True
                break
            targets.append((tr_t, tc_t))
        if bad:
            continue
        # Decoration should not use output color 8; otherwise the input already
        # contains a cyan distractor indistinguishable from the copied template.
        dec_color = rng.choice([7, 9])
        for _ in range(20):
            dr_p = rng.randint(0, h - 1)
            dc_p = rng.randint(0, w - 1)
            if g[dr_p][dc_p] == 0 and (dr_p, dc_p) not in targets:
                g[dr_p][dc_p] = dec_color
                break
        return g
    raise ValueError("could not realize non-overlapping vector-copy board")


def _positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]


def _combined_delta(pos):
    return ((pos[3][0] - pos[2][0]) + (pos[6][0] - pos[4][0]),
            (pos[3][1] - pos[2][1]) + (pos[6][1] - pos[4][1]))


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    pos = {color: _positions(grid, color) for color in [1, 2, 3, 4, 6]}
    for color in [2, 3, 4, 6]:
        if len(pos[color]) != 1:
            msgs.append(f"expected exactly one marker color {color}; got {len(pos[color])}")
    if not pos[1]:
        msgs.append("expected at least one color-1 template cell")
    if any(len(pos[color]) != 1 for color in [2, 3, 4, 6]) or not pos[1]:
        return msgs
    marker_pos = {color: pos[color][0] for color in [2, 3, 4, 6]}
    vr, vc = _combined_delta(marker_pos)
    if (vr, vc) == (0, 0):
        msgs.append("combined marker delta should be nonzero")
    h, w = len(grid), len(grid[0])
    for r, c in pos[1]:
        rr, cc = r + vr, c + vc
        if not (0 <= rr < h and 0 <= cc < w):
            msgs.append("translated template cell goes out of bounds")
            break
        if grid[rr][cc] != 0:
            msgs.append("translated template target should be background in the input")
            break
    if any(v == 8 for row in grid for v in row):
        msgs.append("normal input should not already contain output color 8")
    return msgs

def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "missing_marker":
        # only 3 of the 4 markers — combined delta undefined
        g[0][8] = 2
        g[1][9] = 3
        g[7][8] = 4
        g[1][1] = 1; g[2][1] = 1; g[2][2] = 1
        g[h - 1][0] = 5
        return g
    if name == "zero_combined_delta":
        # delta vectors cancel — net translation is (0, 0)
        g[0][8] = 2
        g[1][9] = 3
        g[8][9] = 4
        g[7][8] = 6
        g[1][1] = 1; g[2][1] = 1; g[2][2] = 1
        g[h - 1][0] = 5
        return g
    if name == "no_template":
        # markers but no 1-blob to translate
        g[0][8] = 2
        g[1][9] = 3
        g[7][8] = 4
        g[7][9] = 6
        g[h - 1][0] = 5
        return g
    return g
