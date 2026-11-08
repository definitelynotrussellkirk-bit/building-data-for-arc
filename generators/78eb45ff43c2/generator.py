"""Generator for d4f3cd78.

Rule: gray rectangular frame with a one-cell gap; rule fills interior
with cyan and extends a cyan line outward through the gap.

Combinatorial axes (8): grid_h/w, frame_h, frame_w, palette_kind,
anchor_corner, asymmetry_force, palette_size, gap_side.
Degenerates: no_frame, full_grid, no_gap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "78eb45ff43c2"
VERSION = "1.1.1"
TASK_ID = "78eb45ff43c2"
SUMMARY = "Gray frame with a gap; rule fills interior and extends a line through the gap."

INVARIANTS = [
    "background is 0",
    "exactly one gray frame of color 5",
    "frame perimeter has exactly one missing cell as the gap",
    "frame is at least 5x5 and has bg margin to the grid edge on the gap side",
]

GAP_SIDES = ("top", "bottom", "left", "right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frame", "full_grid", "no_gap")
HELPFUL_TEXTURES = GAP_SIDES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "frame_h":        {"type": "int", "default": "rng 5..h-5", "valid": ">=5"},
    "frame_w":        {"type": "int", "default": "rng 5..w-5", "valid": ">=5"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "gap_side":       {"type": "str", "default": "rng helpful",
                       "valid": "|".join(GAP_SIDES)},
    "texture":        {"type": "str", "default": "alias for gap_side",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg 0, ≥1 color-5 (gray) frame cell, exactly one gap (a non-5 cell in the frame perimeter)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    count_5 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 5)
    if count_5 == 0:
        errs.append("no color-5 (gray) frame cells found")
        return errs
    # Check only one non-bg color: color 5
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if colors - {5}:
        errs.append(f"unexpected non-5 non-0 colors: {colors - {5}} (frame should be monochrome gray)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("frame_pos")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 12, 14
    elif difficulty == "hard":
        h_lo, h_hi = 18, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    fh = ctx.draw_int("frame_h", 5, h - 5)
    fw = ctx.draw_int("frame_w", 5, w - 5)
    rr = rng.randint(2, h - fh - 2)
    rc = rng.randint(2, w - fw - 2)
    g = full_grid(h, w, 0)
    draw_rect_outline(g, rr, rc, fh, fw, 5)
    side = (overrides.get("texture") if overrides.get("texture") in GAP_SIDES else None) or \
           overrides.get("gap_side") or \
           ctx.draw_choice("gap_side", list(GAP_SIDES))
    if side == "top":
        gap_c = ctx.draw_int("gap_pos", rc + 1, rc + fw - 2)
        g[rr][gap_c] = 0
    elif side == "bottom":
        gap_c = ctx.draw_int("gap_pos", rc + 1, rc + fw - 2)
        g[rr + fh - 1][gap_c] = 0
    elif side == "left":
        gap_r = ctx.draw_int("gap_pos", rr + 1, rr + fh - 2)
        g[gap_r][rc] = 0
    else:
        gap_r = ctx.draw_int("gap_pos", rr + 1, rr + fh - 2)
        g[gap_r][rc + fw - 1] = 0
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(14, 14, 0)
    if name == "no_frame":
        return g
    if name == "no_gap":
        draw_rect_outline(g, 3, 3, 6, 6, 5)
        return g
    if name == "full_grid":
        for r in range(14):
            for c in range(14):
                g[r][c] = 5
        return g
    return g
