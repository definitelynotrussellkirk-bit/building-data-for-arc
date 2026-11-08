"""Generator for arc_puzzle_bank_21_set15:S15_M1.

Rule: a multicolor template is copied to the single blue marker anchor.

Combinatorial axes (8): grid_h, grid_w, palette_kind, variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_marker, no_template, multiple_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b24eadbaf79d"
VERSION = "1.2.1"
TASK_ID = "b24eadbaf79d"
SUMMARY = (
    "0-bg grid with: (a) a multicolor template — connected colored "
    "cells using palette {2, 3, 4, ...} (no 0, no 1); (b) exactly one "
    "color-1 marker cell elsewhere. Rule: normalize the template's "
    "cells to top-left = (0, 0), then stamp the template at the "
    "marker position on a FRESH 0-grid (preserving each cell's color). "
    "The marker and original template do NOT appear in the output."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one color-1 marker",
    "multicolor template uses colors {2..9} (no 0, no 1)",
    "marker anchor has room for the whole template footprint",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_marker", "no_template", "multiple_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

_TEMPLATE_BANK = [
    [(0, 0, 2), (0, 1, 3), (1, 0, 4), (2, 1, 3)],
    [(0, 1, 2), (1, 0, 4), (1, 1, 3), (1, 2, 4), (2, 0, 2)],
    [(0, 0, 5), (0, 1, 6), (1, 0, 7), (1, 1, 8)],
    [(0, 0, 3), (0, 1, 4), (0, 2, 5), (1, 1, 6)],
    [(0, 0, 2), (1, 0, 3), (2, 0, 4), (2, 1, 5)],
    [(0, 0, 6), (0, 1, 7), (1, 1, 8), (2, 1, 9)],
]
# Backward-compat
TEMPLATE_A = _TEMPLATE_BANK[0]
TEMPLATE_B = _TEMPLATE_BANK[1]

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "variant":        {"type": "enum", "default": "rng a|b", "valid": "a|b"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "template_top_marker_bottom",
                       "valid": "template_top_marker_bottom"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly 1 cell of color 1 (the marker); ≥2 cells of colors 2-9 (the template)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    one_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    template_count = sum(1 for r in range(h) for c in range(w) if grid[r][c] >= 2)
    if one_count != 1:
        errs.append(f"expected exactly 1 color-1 marker; found {one_count}")
    if template_count < 2:
        errs.append(f"expected ≥2 template cells (colors 2-9); found {template_count}")
    return errs


def _paint_entries(g, r0, c0, entries):
    for dr, dc, color in entries:
        g[r0 + dr][c0 + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 11, 12)
        w = ctx.draw_int("width", 13, 14)
        variant = ctx.draw_choice("variant", ["a"])
    elif difficulty == "hard":
        h = ctx.draw_int("height", 13, 14)
        w = ctx.draw_int("width", 15, 16)
        variant = ctx.draw_choice("variant", ["b"])
    else:
        h = ctx.draw_int("height", 11, 14)
        w = ctx.draw_int("width", 13, 16)
        variant = ctx.draw_choice("variant", ["a", "b"])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    entries = rng.choice(_TEMPLATE_BANK)
    # Random template position (top half)
    tmpl_h = max(r for r, _, _ in entries) + 1
    tmpl_w = max(c for _, c, _ in entries) + 1
    t_top = rng.randint(0, max(0, h // 2 - tmpl_h))
    t_left = rng.randint(0, max(0, w // 2 - tmpl_w))
    _paint_entries(g, t_top, t_left, entries)
    # Random marker in bottom half, with room for template
    for _ in range(40):
        mr = rng.randint(h // 2, h - tmpl_h - 1)
        mc = rng.randint(0, w - tmpl_w - 1)
        if g[mr][mc] == 0:
            g[mr][mc] = 1
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    if name == "no_marker":
        # template without color-1 marker → no anchor to copy to
        _paint_entries(g, 1, 1, TEMPLATE_A)
        return g
    if name == "no_template":
        # marker without template → nothing to copy
        g[h - 5][w - 5] = 1
        return g
    if name == "multiple_markers":
        # 2 color-1 markers → which to copy to is ambiguous
        _paint_entries(g, 1, 1, TEMPLATE_A)
        g[h - 5][w - 5] = 1
        g[h - 5][w - 9] = 1
        return g
    return g
