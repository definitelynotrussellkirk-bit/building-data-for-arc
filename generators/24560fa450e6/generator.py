"""Generator for 24560fa450e6 — element-wise min of two panels' onion-depth maps.

Rule (verified from canonical Racket): split on full color-9 columns into two
panels. For each, compute its onion-layer depth map (each filled cell's distance
from the shape boundary) and crop to content. Pad both to a common size and
output the cell-wise MIN of the two depth maps.

The previous body was the generic "6 panels, find the matching pair" template,
whose sparse 1-3 cell motifs had onion depth ~1 everywhere, so the min was
near-constant (rule_smoke distinct_out=4 -- degenerate). This 2.2.0 rewrite
CONSTRUCTS valid inputs: each panel holds a SOLID filled region (rectangle or
blob) of varying size, so the depth maps have real structure and their min
varies.

Axes: panel size, region sizes/shapes/positions.
Degenerates: tiny_regions, big_regions, offset.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "24560fa450e6"
VERSION = "2.2.1"  # REWRITE: min of two onion-depth maps (was find-pair template; degenerate distinct=4)
TASK_ID = "24560fa450e6"

SUMMARY = (
    "Two panels (color-9 column between), each holding a solid filled region of "
    "varying size. Rule: take each panel's onion-layer depth map, crop, pad to a "
    "common size and output the cell-wise minimum. Panel and region sizes vary."
)

INVARIANTS = [
    "a full color-9 column separates the two panels",
    "each panel holds one solid filled region (so its onion-depth map has structure)",
    "region sizes/shapes vary between samples",
]

DEGENERATE_TEXTURES = ("tiny_regions", "big_regions", "offset")
HELPFUL_TEXTURES = ("varied", "wide", "tall")

AXES = {
    "panel_h":  {"type": "int", "default": "rng 7..12", "valid": "5..16"},
    "panel_w":  {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "texture":  {"type": "str", "default": "rng helpful",
                 "valid": "varied|wide|tall|tiny_regions|big_regions|offset"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid has exactly one full-height column of color-9 (the separator)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if not sep_cols:
        return errors  # degenerate — allowed
    if len(sep_cols) != 1:
        errors.append(f"expected exactly 1 full-height color-9 column; found {len(sep_cols)}")
    return errors


def _fill_region(g, base, ph, pw, rng, color):
    rh = rng.randint(3, ph)
    rw = rng.randint(3, pw)
    tr = rng.randint(0, ph - rh)
    tc = rng.randint(0, pw - rw)
    for r in range(tr, tr + rh):
        for c in range(tc, tc + rw):
            g[r][base + c] = color


def _build(rng, ph, pw):
    W = pw + 1 + pw
    g = full_grid(ph, W, 0)
    for r in range(ph):
        g[r][pw] = 9
    cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 2)
    _fill_region(g, 0, ph, pw, rng, cols[0])
    _fill_region(g, pw + 1, ph, pw, rng, cols[1])
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 8, 5, 7
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 10, 16, 8, 14
    else:
        h_lo, h_hi, w_lo, w_hi = 7, 12, 6, 10

    ph = ctx.draw_int("panel_h", h_lo, h_hi)
    pw = ctx.draw_int("panel_w", w_lo, w_hi)
    return _build(rng, ph, pw)


def _draw_from_degenerate(name, rng):
    if name == "tiny_regions":
        return _build(rng, 7, 6)
    if name == "big_regions":
        return _build(rng, 14, 12)
    return _build(rng, 10, 8)                     # offset / varied
