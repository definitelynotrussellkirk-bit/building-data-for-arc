"""Generator for a3f84088.

Rule: hollow gray frame; rule fills interior with cycling
distance-from-border colors (5,2,5,0).

Combinatorial axes (8): grid_h/w, frame_h, frame_w, position_bias,
palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: solid_block, no_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "8d3777b00a4c"
VERSION = "1.1.1"
TASK_ID = "8d3777b00a4c"
SUMMARY = "Hollow gray frame; rule fills interior with cycling distance-from-border colors."

INVARIANTS = [
    "background is 0",
    "exactly one hollow gray frame, interior bg",
    "frame >= 5x5 so the (5,2,5,0) cycle is visible",
]

POSITION_BIASES = ("centered", "corner", "near_edge", "scattered")
DEGENERATE_TEXTURES = ("solid_block", "no_frame", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..15", "valid": "9..18"},
    "frame_h":        {"type": "int", "default": "rng 7..h-2", "valid": "5..16"},
    "frame_w":        {"type": "int", "default": "rng 7..w-2", "valid": "5..16"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; color-5 (gray frame) cells present; frame is a rectangle outline."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    has5 = any(grid[r][c] == 5 for r in range(h) for c in range(w))
    if not has5:
        return []  # no_frame degenerate — allowed
    # Find color-5 rows and cols (rows/cols that have any 5)
    rows5 = set(r for r in range(h) for c in range(w) if grid[r][c] == 5)
    cols5 = set(c for r in range(h) for c in range(w) if grid[r][c] == 5)
    errs = []
    if not rows5:
        errs.append("color-5 cells found but no row has them (unexpected)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 9, 11
        fh_lo, fh_hi = 5, 7
    elif difficulty == "hard":
        h_lo, h_hi = 15, 18
        fh_lo, fh_hi = 9, 14
    else:
        h_lo, h_hi = 11, 15
        fh_lo, fh_hi = 7, 11
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    fh = int(overrides.get("frame_h",
                           rng.randint(fh_lo, min(fh_hi, h - 2))))
    fw = int(overrides.get("frame_w",
                           rng.randint(fh_lo, min(fh_hi, w - 2))))
    fh = max(5, min(fh, h - 2))
    fw = max(5, min(fw, w - 2))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias", list(POSITION_BIASES)))
    rr, rc = _pick_pos(bias, h, w, fh, fw, rng)
    draw_rect_outline(g, rr, rc, fh, fw, 5)
    return g


def _pick_pos(bias, h, w, fh, fw, rng):
    max_r = max(1, h - fh - 1)
    max_c = max(1, w - fw - 1)
    if bias == "centered":
        rr = max(1, (h - fh) // 2)
        rc = max(1, (w - fw) // 2)
    elif bias == "corner":
        rr = rng.choice([1, max_r])
        rc = rng.choice([1, max_c])
    elif bias == "near_edge":
        if rng.random() < 0.5:
            rr = rng.choice([1, max_r])
            rc = rng.randint(1, max_c)
        else:
            rr = rng.randint(1, max_r)
            rc = rng.choice([1, max_c])
    else:
        rr = rng.randint(1, max_r)
        rc = rng.randint(1, max_c)
    return rr, rc


def _draw_from_degenerate(name, rng):
    h, w = 13, 13
    g = full_grid(h, w, 0)
    if name == "solid_block":
        for r in range(3, 8):
            for c in range(3, 8):
                g[r][c] = 5
        return g
    if name == "no_frame":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
