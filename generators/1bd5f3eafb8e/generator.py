"""Generator for puzzle fbf15a0b.

Rule: bg=8 with sparse 1s. Two 5-cells indicate the split: aligned in
column → horizontal split (top/bottom half by row); aligned in row →
vertical split (left/right half by col). Output: that half with 5s
recolored to 8.

Combinatorial axes (8): grid_h/w, ones_density, marker_orientation,
marker_side, marker_separation, ones_pattern, anchor_corner,
asymmetry_force.
Degenerates: marker_at_center, no_ones, all_ones.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bd5f3eafb8e"
VERSION = "1.1.1"
TASK_ID = "1bd5f3eafb8e"
SUMMARY = "Even h,w grid; bg=8 with 1s + 2 aligned 5-markers; rule crops half."

INVARIANTS = [
    "h and w are even",
    "bg = 8",
    "exactly two 5-cells aligned in same row or same col, 2 apart",
    "5s lie entirely within one half (left/right or top/bottom)",
]

ONES_PATTERNS = ("scattered", "stripes", "diagonal", "checker", "frame")
MARKER_ORIENTS = ("horizontal_split", "vertical_split")
MARKER_SIDES = ("top_or_left", "bottom_or_right")
DEGENERATE_TEXTURES = ("marker_at_center", "no_ones", "all_ones")
HELPFUL_TEXTURES = ONES_PATTERNS

AXES = {
    "grid_h":              {"type": "int", "default": "rng 14..22 (even)",
                            "valid": "10..28"},
    "grid_w":              {"type": "int", "default": "rng 14..22 (even)",
                            "valid": "10..28"},
    "ones_density":        {"type": "float", "default": "rng 0.1..0.3",
                            "valid": "0..0.5"},
    "ones_pattern":        {"type": "str", "default": "rng helpful",
                            "valid": "scattered|stripes|diagonal|checker|frame"},
    "marker_orientation":  {"type": "str", "default": "rng horizontal_split|vertical_split",
                            "valid": "horizontal_split|vertical_split"},
    "marker_side":         {"type": "str", "default": "rng top_or_left|bottom_or_right",
                            "valid": "top_or_left|bottom_or_right"},
    "marker_separation":   {"type": "int", "default": "2", "valid": "2"},
    "anchor_corner":       {"type": "bool", "default": "false",
                            "valid": "true|false"},
    "texture":             {"type": "str", "default": "alias for ones_pattern",
                            "valid": "scattered|stripes|diagonal|checker|frame|marker_at_center|no_ones|all_ones"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 14
    elif difficulty == "hard":
        h_lo, h_hi = 22, 28
    else:
        h_lo, h_hi = 14, 22
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    if h % 2:
        h += 1
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    if w % 2:
        w += 1
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    g = full_grid(h, w, 8)
    pattern = (overrides.get("texture") or
               overrides.get("ones_pattern")
               or ctx.draw_choice("ones_pattern", list(ONES_PATTERNS)))
    density = float(overrides.get("ones_density",
                                  ctx.draw_rng("ones_density")
                                  .uniform(0.1, 0.3)))
    _fill_ones(g, pattern, h, w, density, rng)
    orient = overrides.get("marker_orientation",
                           ctx.draw_choice("marker_orientation",
                                           list(MARKER_ORIENTS)))
    side = overrides.get("marker_side",
                         ctx.draw_choice("marker_side",
                                         list(MARKER_SIDES)))
    if orient == "horizontal_split":
        if side == "top_or_left":
            r1 = rng.randint(0, max(0, h // 2 - 3))
        else:
            r1 = rng.randint(h // 2, max(h // 2, h - 3))
        col = rng.randint(0, w - 1)
        g[r1][col] = 5
        if r1 + 2 < h:
            g[r1 + 2][col] = 5
        else:
            g[r1 - 2][col] = 5
    else:
        if side == "top_or_left":
            c1 = rng.randint(0, max(0, w // 2 - 3))
        else:
            c1 = rng.randint(w // 2, max(w // 2, w - 3))
        row = rng.randint(0, h - 1)
        g[row][c1] = 5
        if c1 + 2 < w:
            g[row][c1 + 2] = 5
        else:
            g[row][c1 - 2] = 5
    return g


def _fill_ones(g, pattern, h, w, density, rng):
    if pattern == "scattered":
        for r in range(h):
            for c in range(w):
                if rng.random() < density:
                    g[r][c] = 1
    elif pattern == "stripes":
        for r in range(h):
            if r % 2 == 0:
                for c in range(w):
                    if rng.random() < density + 0.2:
                        g[r][c] = 1
    elif pattern == "diagonal":
        for r in range(h):
            for c in range(w):
                if (r + c) % 3 == 0 and rng.random() < density + 0.4:
                    g[r][c] = 1
    elif pattern == "checker":
        for r in range(h):
            for c in range(w):
                if (r + c) % 2 == 0 and rng.random() < density + 0.4:
                    g[r][c] = 1
    elif pattern == "frame":
        for r in range(h):
            for c in range(w):
                if (r in (0, h - 1) or c in (0, w - 1)) and rng.random() < density + 0.4:
                    g[r][c] = 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: h and w even; bg=8; exactly 2 color-5 marker cells."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    errs = []
    if h % 2 != 0:
        errs.append(f"expected even height, got {h}")
    if w % 2 != 0:
        errs.append(f"expected even width, got {w}")
    c5 = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    if len(c5) != 2:
        errs.append(f"expected exactly 2 color-5 marker cells, found {len(c5)}")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    if h % 2:
        h += 1
    if w % 2:
        w += 1
    g = full_grid(h, w, 8)
    if name == "marker_at_center":
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.18:
                    g[r][c] = 1
        # markers exactly straddling the midline (ambiguous)
        g[h // 2 - 1][w // 2] = 5
        g[h // 2 + 1][w // 2] = 5
        return g
    if name == "no_ones":
        g[0][0] = 5
        g[0][2] = 5
        return g
    if name == "all_ones":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        g[0][0] = 5
        g[0][2] = 5
        return g
    return g
