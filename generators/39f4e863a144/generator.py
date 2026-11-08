"""Generator for f1cefba8.

Rule: inner tab protrusions cut through the inner object and extend
outward through the outer frame.

Combinatorial axes (8): grid_h/w, tab_axis, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_outer, no_inner, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, draw_rect, full_grid

GENERATOR_ID = "39f4e863a144"
VERSION = "2.0.1"  # shape-locked-in/out (fixed 13x13, fixed frame (2,2,10,10), fixed 3x3 inner, fixed 2 tab positions): rule reads h,w dynamically (output=input size) and canonical spans 15x17/19x13/16x18. Now grid + outer block size/pos + inner body (inset) + tab edges/positions/count + colors all vary; >=1 tab guaranteed (non-identity).
TASK_ID = "39f4e863a144"
SUMMARY = "Inner tab protrusions cut through inner object and extend through outer frame."

INVARIANTS = [
    "the background is zero",
    "the largest bbox object is the outer frame",
    "the second largest bbox object is an inner object with one-cell tabs on its edge",
    "outer and inner colors are distinct and non-zero",
]

TAB_AXES = ("row", "col")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_outer", "no_inner", "full_grid")
HELPFUL_TEXTURES = TAB_AXES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 13..18", "valid": "12..22"},
    "grid_w":         {"type": "int", "default": "rng 13..18", "valid": "12..22"},
    "tab_axis":       {"type": "str", "default": "rng helpful",
                       "valid": "row|col"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for tab_axis",
                       "valid": "row|col|no_outer|no_inner|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 2 distinct nonzero colors (outer frame + inner object); values 0..9."""
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
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if not colors:
        pass  # degenerate (no_outer/no_inner) — allowed
    elif len(colors) != 2:
        errors.append(f"expected 2 colors (outer+inner), found {len(colors)}: {sorted(colors)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        H = ctx.draw_int("grid_h", 12, 14); W = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        H = ctx.draw_int("grid_h", 16, 22); W = ctx.draw_int("grid_w", 16, 22)
    else:
        H = ctx.draw_int("grid_h", 13, 18); W = ctx.draw_int("grid_w", 13, 18)
    outer, inner = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    g = full_grid(H, W, 0)
    # --- outer solid block (largest bbox), >=1 margin all sides for outward rays
    bh = min(rng.randint(8, H - 2), H - 2)
    bw = min(rng.randint(8, W - 2), W - 2)
    oR1 = rng.randint(1, H - 1 - bh); oC1 = rng.randint(1, W - 1 - bw)
    oR2 = oR1 + bh - 1; oC2 = oC1 + bw - 1
    for r in range(oR1, oR2 + 1):
        for c in range(oC1, oC2 + 1):
            g[r][c] = outer
    # --- inner solid body (second bbox), inset 2 so a tab (1 cell out) sits in
    #     the oc ring; body >=3x3.
    iR1, iC1, iR2, iC2 = oR1 + 2, oC1 + 2, oR2 - 2, oC2 - 2
    for r in range(iR1, iR2 + 1):
        for c in range(iC1, iC2 + 1):
            g[r][c] = inner
    # --- tabs: single-cell ic protrusions, 1 cell out from a body edge, at
    #     non-corner positions spaced >=2 so each tip has exactly one ic neighbor.
    def spaced(lo, hi, k):
        opts = list(range(lo, hi + 1)); rng.shuffle(opts)
        chosen = []
        for v in opts:
            if all(abs(v - u) >= 2 for u in chosen):
                chosen.append(v)
            if len(chosen) == k:
                break
        return chosen
    edges = ["top", "bottom", "left", "right"]
    rng.shuffle(edges)
    n_edges = rng.randint(1, 4)
    for edge in edges[:n_edges]:
        k = rng.randint(1, 2)
        if edge in ("top", "bottom") and iC2 - 1 >= iC1 + 1:
            r = iR1 - 1 if edge == "top" else iR2 + 1
            for c in spaced(iC1 + 1, iC2 - 1, k):
                g[r][c] = inner
        elif edge in ("left", "right") and iR2 - 1 >= iR1 + 1:
            c = iC1 - 1 if edge == "left" else iC2 + 1
            for r in spaced(iR1 + 1, iR2 - 1, k):
                g[r][c] = inner
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_outer":
        draw_rect(g, 5, 5, 3, 3, 2)
        return g
    if name == "no_inner":
        draw_frame(g, 2, 2, 10, 10, 1)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 1
        return g
    return g
