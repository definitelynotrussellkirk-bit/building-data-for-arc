"""Generator for arc_additional_puzzles_21_set17_bundle:M115 — fill compartments with majority marker color.

Rule: 8-walls divide the grid into compartments. Each compartment's
0-cells get repainted with the majority non-0/non-8 color present in
that compartment.

Combinatorial axes (8): n_markers_per_compartment, palette_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_walls, no_markers, all_compartments_same.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box

GENERATOR_ID = "6ce8f4377282"
VERSION = "3.1.0"  # shape-locked in/out: fixed 9x11 with a 2x2 color-8 compartment grid. Rule fills each compartment region with its MAJORITY non-{0,8} colour (size-generic). Now vary compartment-grid dims + sizes, and place a clear majority colour (+ optional minority) so the majority branch is exercised.
TASK_ID = "6ce8f4377282"
SUMMARY = (
    "Fixed 9×11 grid with "
    "COLOR-8 (cyan) WALLS "
    "forming a 2×2 "
    "COMPARTMENT LAYOUT: "
    "rows 0, 4, 8 are fully "
    "8; cols 0, 5, 10 are "
    "fully 8. This creates "
    "4 INTERIOR "
    "COMPARTMENTS at "
    "(1..3, 1..4), (1..3, "
    "6..9), (5..7, 1..4), "
    "(5..7, 6..9). EACH "
    "COMPARTMENT contains "
    "1-2 SAME-COLOR MARKER "
    "cells in a DISTINCT "
    "color from {1, 2, 3, "
    "4, 5, 6, 7, 9} "
    "(different across "
    "compartments). Rule "
    "(FILL EACH COMPARTMENT "
    "WITH ITS MARKER "
    "COLOR): For EACH "
    "COMPARTMENT (4-conn "
    "non-8 region "
    "bounded by 8-walls): "
    "identify the MAJORITY "
    "non-0, non-8 COLOR "
    "(the marker color). "
    "REPAINT all 0-cells "
    "in that compartment "
    "with the marker "
    "color. The 8-walls "
    "stay. Net: each "
    "compartment fills "
    "with its marker's "
    "color."
)

INVARIANTS = [
    "background is 0",
    "the 8-walls form a 2x2 compartment layout (rows 0,4,8 + cols 0,5,10 are 8)",
    "each compartment contains 1-2 markers, all of the same non-0/non-8 color",
    "different compartments may use different marker colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_walls", "no_markers", "all_compartments_same")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_markers_per_compartment": {"type": "int", "default": "rng 1..2", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "4", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "2x2_compartments_8walls",
                       "valid": "2x2_compartments_8walls"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_walls|no_markers|all_compartments_same"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        tr, tc = 2, 2; ch = ctx.draw_int("ch", 2, 3); cw = ctx.draw_int("cw", 3, 4)
    elif difficulty == "hard":
        tr = ctx.draw_int("tr", 2, 3); tc = ctx.draw_int("tc", 2, 3)
        ch = ctx.draw_int("ch", 3, 4); cw = ctx.draw_int("cw", 3, 5)
    else:
        tr = ctx.draw_int("tr", 2, 3); tc = ctx.draw_int("tc", 2, 3)
        ch = ctx.draw_int("ch", 2, 4); cw = ctx.draw_int("cw", 3, 5)
    h = tr * (ch + 1) + 1
    w = tc * (cw + 1) + 1
    g = full_grid(h, w, 0)
    # color-8 walls: every (ch+1)-th row and (cw+1)-th col (border + dividers)
    for r in range(h):
        for c in range(w):
            if r % (ch + 1) == 0 or c % (cw + 1) == 0:
                g[r][c] = 8
    # each compartment gets a clear MAJORITY colour (+ optional minority)
    for ti in range(tr):
        for tj in range(tc):
            r0 = ti * (ch + 1) + 1
            c0 = tj * (cw + 1) + 1
            cells = [(r, c) for r in range(r0, r0 + ch) for c in range(c0, c0 + cw)]
            rng.shuffle(cells)
            primary = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
            secondary = rng.choice([c for c in (1, 2, 3, 4, 5, 6, 7, 9) if c != primary])
            max_primary = max(2, len(cells) - 1)
            p = rng.randint(2, max_primary)                 # leave at least one zero to fill
            remaining = len(cells) - p
            s = rng.randint(0, min(p - 1, max(0, remaining - 1)))  # minority < majority and still leave zero
            idx = 0
            for _ in range(p):
                r, c = cells[idx]; g[r][c] = primary; idx += 1
            for _ in range(s):
                r, c = cells[idx]; g[r][c] = secondary; idx += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "no_walls":
        # Markers but no 8-walls — compartment boundaries undefined.
        g[2][2] = 4; g[2][7] = 6; g[6][2] = 7; g[6][7] = 1
        return g
    if name == "no_markers":
        # Walls present but every compartment is empty — rule has
        # no marker color to paint with.
        fill_box(g, 0, 0, 0, w - 1, 8)
        fill_box(g, 4, 0, 4, w - 1, 8)
        fill_box(g, h - 1, 0, h - 1, w - 1, 8)
        fill_box(g, 0, 0, h - 1, 0, 8)
        fill_box(g, 0, 5, h - 1, 5, 8)
        fill_box(g, 0, w - 1, h - 1, w - 1, 8)
        return g
    if name == "all_compartments_same":
        # All compartments share the same marker color — rule's per-
        # compartment differentiation collapses to a single fill color.
        fill_box(g, 0, 0, 0, w - 1, 8)
        fill_box(g, 4, 0, 4, w - 1, 8)
        fill_box(g, h - 1, 0, h - 1, w - 1, 8)
        fill_box(g, 0, 0, h - 1, 0, 8)
        fill_box(g, 0, 5, h - 1, 5, 8)
        fill_box(g, 0, w - 1, h - 1, w - 1, 8)
        for r, c in [(2, 2), (2, 7), (6, 2), (6, 7)]:
            g[r][c] = 4
        return g
    return g

def _compartments(grid):
    h = len(grid); w = len(grid[0]) if h else 0
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 8 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] != 8:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    comps = _compartments(grid)
    if not (4 <= len(comps) <= 9):
        errs.append(f"expected 4..9 compartments, got {len(comps)}")
    for i, cells in enumerate(comps):
        vals = [grid[r][c] for r, c in cells]
        if 0 not in vals:
            errs.append(f"compartment {i} has no zero cells left for the rule to fill")
        counts = {}
        for v in vals:
            if v not in (0, 8):
                counts[v] = counts.get(v, 0) + 1
        if not counts:
            errs.append(f"compartment {i} has no marker color")
            continue
        top = sorted(counts.values(), reverse=True)
        if len(top) > 1 and top[0] <= top[1]:
            errs.append(f"compartment {i} has no strict majority marker: {counts}")
    return errs
