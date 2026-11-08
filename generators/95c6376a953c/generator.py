"""Generator for arc_additional_puzzle_bank_volume15:H101.

Rule: singleton control 1-3 selects which color-6 nested-frame band
becomes cyan.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_control, no_frames, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "95c6376a953c"
VERSION = "2.0.1"
TASK_ID = "95c6376a953c"
SUMMARY = (
    "0-bg grid (h, w~15-18)"
    " with: (a) THREE "
    "NESTED RECTANGULAR "
    "FRAMES of COLOR 6 — "
    "drawn at offsets (0, "
    "2, 4) from a centered "
    "anchor (frame 0 "
    "outermost at margin 2, "
    "frame 1 nested 2 "
    "cells inward, frame 2 "
    "innermost 4 cells "
    "inward), all in color "
    "6; (b) ONE CONTROL "
    "CELL in COLOR ∈ {1, "
    "2, 3} placed at one "
    "of the 4 GRID CORNERS"
    ". The control encodes "
    "a band index k. Rule "
    "(FILL THE k-TH BAND "
    "WITH CYAN, FROM OUTER "
    "INWARD): identify "
    "the SINGLE CONTROL "
    "CELL — its color k ∈ "
    "{1, 2, 3}. The "
    "nested-frame "
    "structure has 3 "
    "BANDS: BAND-1 = ring "
    "between frame 0 and "
    "frame 1; BAND-2 = "
    "ring between frame 1 "
    "and frame 2; BAND-3 "
    "= interior inside "
    "frame 2. SELECT the "
    "k-th band (outer-in)"
    ". PAINT every BG-0 "
    "cell in that band "
    "with COLOR 8 (cyan). "
    "Frame cells (6) stay. "
    "Control cell stays. "
    "Net: the control "
    "color picks one "
    "nested ring and fills "
    "it cyan."
)

# Rivals: 'fill all bands' refuted by ≥2 demos where only one band
# changes. 'use control color for fill' refuted by any demo (fill is
# 8). 'fill interior of innermost frame' refuted by ≥1 demo where
# control=1 or 2 (outer band fills, not innermost). 'replace frame
# color' refuted by any demo (frames stay 6). 3 demos with control
# 1/2/3 cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "three color-6 rectangular frames are nested",
    "exactly one of colors 1, 2, 3 appears as the control",
    "the selected band has empty cells",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_control", "no_frames", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 15..18", "valid": "15..24"},
    "grid_w":         {"type": "int", "default": "rng 15..18", "valid": "15..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "centered", "valid": "centered"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("placement")
    if difficulty == "easy":
        # Need h,w >= 15 for the offset-4 inner frame to exist.
        h = ctx.draw_int("grid_h", 15, 16)
        w = ctx.draw_int("grid_w", 15, 16)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 18, 24)
        w = ctx.draw_int("grid_w", 18, 24)
    else:
        h = ctx.draw_int("grid_h", 15, 18)
        w = ctx.draw_int("grid_w", 15, 18)
    g = full_grid(h, w, 0)
    # Control color can land in any of 4 corners
    corner = rng.choice([(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)])
    g[corner[0]][corner[1]] = rng.randint(1, 3)
    # Frames: outermost at margin 2, inner with step 2
    for offset in (0, 2, 4):
        r1 = 2 + offset
        c1 = 2 + offset
        r2 = h - 3 - offset
        c2 = w - 3 - offset
        if r2 - r1 < 2 or c2 - c1 < 2:
            break
        draw_frame(g, r1, c1, r2, c2, 6)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 15, 0)
    if name == "no_control":
        for offset in (0, 2, 4):
            draw_frame(g, 2 + offset, 2 + offset, 12 - offset, 12 - offset, 6)
        return g
    if name == "no_frames":
        g[0][0] = 1
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(15):
                g[r][c] = 6
        return g
    return g


def _frame_cells(r1, c1, r2, c2):
    cells = set()
    for c in range(c1, c2 + 1):
        cells.add((r1, c)); cells.add((r2, c))
    for r in range(r1, r2 + 1):
        cells.add((r, c1)); cells.add((r, c2))
    return cells


def _band_cells(h, w, band_index):
    """Return the bg cells belonging to band 1, 2, or 3 in the input frame layout."""
    outer = (2, 2, h - 3, w - 3)
    middle = (4, 4, h - 5, w - 5)
    inner = (6, 6, h - 7, w - 7)
    if band_index == 1:
        r1, c1, r2, c2 = outer
        mr1, mc1, mr2, mc2 = middle
        return {(r, c) for r in range(r1 + 1, r2)
                for c in range(c1 + 1, c2)
                if not (mr1 <= r <= mr2 and mc1 <= c <= mc2)}
    if band_index == 2:
        r1, c1, r2, c2 = middle
        ir1, ic1, ir2, ic2 = inner
        return {(r, c) for r in range(r1 + 1, r2)
                for c in range(c1 + 1, c2)
                if not (ir1 <= r <= ir2 and ic1 <= c <= ic2)}
    r1, c1, r2, c2 = inner
    return {(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)}


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the nested-frame control task."""
    errs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    h, w = len(grid), len(grid[0])
    if h < 15 or w < 15:
        errs.append("grid must be at least 15x15 so all three nested frames exist")
        return errs

    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    controls = [(r, c, grid[r][c]) for (r, c) in corners if grid[r][c] in (1, 2, 3)]
    if len(controls) != 1:
        errs.append("expected exactly one corner control cell with color 1, 2, or 3")
    control_pos = {(r, c) for r, c, _ in controls}

    expected_frame_cells = set()
    for offset in (0, 2, 4):
        r1 = 2 + offset
        c1 = 2 + offset
        r2 = h - 3 - offset
        c2 = w - 3 - offset
        if r2 - r1 < 2 or c2 - c1 < 2:
            errs.append(f"frame at offset {offset} is too small or missing")
            continue
        expected_frame_cells |= _frame_cells(r1, c1, r2, c2)
    bad_frame = [(r, c) for (r, c) in expected_frame_cells if grid[r][c] != 6]
    if bad_frame:
        errs.append("all three expected nested-frame borders must be color 6")

    allowed_nonzero = expected_frame_cells | control_pos
    extras = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
              if v != 0 and (r, c) not in allowed_nonzero]
    if extras:
        errs.append("non-zero cells must be only the three frames plus the corner control")

    if controls:
        band = controls[0][2]
        bg_cells = [(r, c) for (r, c) in _band_cells(h, w, band) if grid[r][c] == 0]
        if not bg_cells:
            errs.append("selected band must contain at least one background cell to fill")
    return errs
