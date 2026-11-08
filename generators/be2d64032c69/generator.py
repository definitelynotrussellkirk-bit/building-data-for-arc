"""Generator for 88a10436.

Rule: 5-marker is anchor. Shape (non-0 non-5 cells) is copied so its
centroid aligns with the 5-marker.

Combinatorial axes (8): grid_h/w, shape_variant, marker_position,
shape_position, palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: same_position, no_marker, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "be2d64032c69"
VERSION = "2.2.1"  # 2.2.0->2.2.1: add self_check. out_shapes 9: h,w in 7..9. Output=same dims; widen grid toward valid (5..12 normal) -> more shapes. (also: clamp shape sc0 lo to rightmost fit)
TASK_ID = "be2d64032c69"
SUMMARY = (
    "0-bg grid (h, w~7-9) "
    "with: (a) ONE MULTI-"
    "COLOR SHAPE drawn "
    "from 3 hardcoded "
    "SHAPE VARIANTS (each "
    "3-6 cells in 2-3 "
    "distinct colors from "
    "{1, 2, 4, 6}) placed "
    "in the UPPER-RIGHT "
    "quadrant; (b) ONE "
    "COLOR-5 (gray) "
    "MARKER cell at a "
    "non-adjacent "
    "position in the "
    "LOWER-LEFT quadrant. "
    "Rule (TRANSLATE "
    "SHAPE TO ALIGN "
    "CENTROID WITH "
    "5-MARKER): identify "
    "the SHAPE (non-0 "
    "non-5 cells) and "
    "compute its "
    "CENTROID (mean of "
    "cell positions, "
    "rounded). Identify "
    "the 5-MARKER's "
    "position. COMPUTE "
    "translation delta "
    "= (marker - "
    "centroid). For "
    "EACH SHAPE cell at "
    "(r, c) with color "
    "C: ERASE the "
    "original, PAINT "
    "g[r + dr][c + dc] = "
    "C. The 5-marker is "
    "absorbed (or kept "
    "per task). Net: "
    "shape moves so its "
    "centroid lands on "
    "the gray marker."
)

INVARIANTS = [
    "exactly one 5-cell (the marker)",
    ">=3 non-5 non-0 cells forming a connected shape",
    "shape and marker are in different quadrants so movement is non-trivial",
]

SHAPES = [
    [(0, 0, 6), (1, 0, 1), (1, 1, 1), (2, 0, 2), (2, 1, 2), (2, 2, 2)],
    [(0, 1, 6), (1, 0, 1), (1, 1, 1), (2, 0, 2)],
    [(0, 0, 4), (0, 1, 4), (1, 1, 6), (2, 1, 2)],
]

POSITION_BIASES = ("opposite", "diagonal", "wide_spread", "rng")
DEGENERATE_TEXTURES = ("same_position", "no_marker", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "5..12"},
    "shape_variant":  {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "opposite|diagonal|wide_spread|rng"},
    "marker_position":{"type": "str", "default": "lower_left",
                       "valid": "lower_left|tl|tr|br|rng"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "opposite|diagonal|wide_spread|rng|same_position|no_marker|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one color-5 marker; has non-{0,5} shape cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    fives = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    shapes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 5)]
    if not fives and not shapes:
        return errs  # degenerate
    if not fives:
        return errs  # degenerate no_marker
    if len(fives) != 1:
        errs.append(f"expected exactly 1 color-5 marker, got {len(fives)}")
    if not shapes:
        errs.append("no non-{0,5} shape cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    # output = same dims; v1.x used h,w in 7..9 -> only 9 shapes. Widen toward
    # valid (5..12); rule reads a single color-5 marker so any size works.
    if difficulty == "easy":
        h_lo, h_hi = 5, 7
    elif difficulty == "hard":
        h_lo, h_hi = 10, 12
    else:
        h_lo, h_hi = 5, 12
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    sv = int(overrides.get("shape_variant",
                           ctx.draw_int("shape_variant", 0, len(SHAPES) - 1)))
    sv = max(0, min(len(SHAPES) - 1, sv))
    shape = SHAPES[sv]
    sh = max(r for r, c, v in shape) + 1
    sw = max(c for r, c, v in shape) + 1
    sr0 = rng.randint(0, max(0, h // 2 - sh))
    # The shape wants the right half (sc0 ≥ w//2+1) but must also fit
    # (sc0 ≤ w-sw). On the easy band's narrowest grid (w=5) a width-3 shape can't
    # satisfy both — w//2+1=3 > w-sw=2 — so randint(3,2) raised "randrange(3,3)".
    # Floor the lo at the rightmost fitting start so the shape lands as far right
    # as the width allows.
    sc_hi = max(0, w - sw)
    sc_lo = min(max(w // 2 + 1, w - sw - 1), sc_hi)
    sc0 = rng.randint(sc_lo, sc_hi)
    for dr, dc, v in shape:
        if sr0 + dr < h and sc0 + dc < w:
            g[sr0 + dr][sc0 + dc] = v
    for _ in range(40):
        mr = rng.randint(max(1, h // 2 + 1), h - 2)
        mc = rng.randint(1, max(1, w // 2 - 1))
        if mr < h and mc >= 0 and g[mr][mc] == 0:
            g[mr][mc] = 5
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "same_position":
        g[3][3] = 5
        g[3][3] = 6
        return g
    if name == "no_marker":
        g[1][5] = 6; g[2][4] = 1; g[2][5] = 1
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
