"""Generator for arc_puzzle_bank_21_set9_s:S9_H5.

A color-2 template and a hollow color-4 frame are given. The rule stamps the
template plus its horizontal, vertical, and 180-degree variants into the four
interior corners of the frame.

Combinatorial axes (8): grid_h, grid_w, palette_kind, template_variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_template, no_frame, frame_too_small.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "c039ca80fb59"
VERSION = "1.2.1"
TASK_ID = "c039ca80fb59"
SUMMARY = "Stamp a template and its mirrored/rotated variants into the 4 interior corners of a 4-frame."

# Rivals: 'stamp once into one corner' refuted by ≥1 demo where all
# 4 corners are filled. 'stamp without variant transforms' refuted by
# ≥2 demos where the 4 stamps show observably different orientations
# (asymmetric templates). 'use template's own color in stamps' refuted
# by any demo (stamps preserve the template's color 2). 'erase the
# input template' refuted by any demo where the original template
# survives outside the frame.
# 4 demos with varied templates + varied frame sizes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "there is exactly one hollow rectangular frame of color 4",
    "there is exactly one connected template object of color 2",
    "the frame interior is large enough for all four variants",
    "the input template is outside the frame",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_template", "no_frame", "frame_too_small")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "13", "valid": "13..13"},
    "grid_w":         {"type": "int", "default": "16", "valid": "16..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "template_variant": {"type": "int", "default": "rng 0..2", "valid": "0..2"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "template_plus_frame",
                       "valid": "template_plus_frame"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_template|no_frame|frame_too_small"},
}

_TEMPLATES = [
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 1), (1, 0), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    [(0, 0), (0, 1), (1, 0)],                            # L-tromino
    [(0, 0), (1, 0), (2, 0), (2, 1)],                    # J-tet
    [(0, 0), (0, 1), (0, 2), (1, 1)],                    # T-tet
    [(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)],            # W-pent
]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has color-4 frame cells and color-2 template cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    fours = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 4]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not fours:
        errs.append("no color-4 frame cells found")
    if not twos:
        errs.append("no color-2 template cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION,
        task_id=TASK_ID, difficulty=difficulty, overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 11, 13, 14, 16
        variant_idx = ctx.draw_int("template_variant", 0, min(2, len(_TEMPLATES) - 1))
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 18, 17, 22
        variant_idx = ctx.draw_int("template_variant", 0, len(_TEMPLATES) - 1)
    else:
        h_lo, h_hi, w_lo, w_hi = 12, 15, 15, 19
        variant_idx = ctx.draw_int("template_variant", 0, len(_TEMPLATES) - 1)
    template = _TEMPLATES[variant_idx]
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    g = full_grid(h, w, 0)
    # Template area must accommodate the template + 1-cell margin.
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    # Frame size: enough to hold 4 stamps of the template + center gap.
    # Min interior: (2 * th + 1) × (2 * tw + 1). Pick frame size in that range.
    min_fh = 2 * th + 3  # 2 stamps + 1 gap + 2 borders
    min_fw = 2 * tw + 3
    max_fh = min(h - 1, min_fh + 4)
    # The frame sits to the RIGHT of the template, so left ∈ [tw+3, w-fw];
    # that range is non-empty only when fw ≤ w-tw-3. The old max_fw ignored
    # this, letting a wide fw make `randint(tw+3, w-fw)` empty. Cap it; if the
    # cap drops below min_fw the feasibility check below takes the fallback.
    max_fw = min(w // 2 + 4, min_fw + 6, w - tw - 3)
    if max_fh < min_fh or max_fw < min_fw:
        # Fallback to original fixed layout
        g = full_grid(13, 16, 0)
        _paint(g, 1, 1, template, 2)
        draw_frame(g, 2, 7, 10, 14, 4)
        return g
    fh = rng.randint(min_fh, max_fh)
    fw = rng.randint(min_fw, max_fw)
    # Place template on the left, frame on the right with space between.
    _paint(g, 1 + rng.randint(0, max(0, h - th - 2)), 1 + rng.randint(0, 1), template, 2)
    top = rng.randint(0, h - fh)
    left = rng.randint(tw + 3, w - fw)
    draw_frame(g, top, left, top + fh - 1, left + fw - 1, 4)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 16, 0)
    if name == "no_template":
        # frame without template → no stencil to stamp into corners
        draw_frame(g, 2, 7, 10, 14, 4)
        return g
    if name == "no_frame":
        # template without frame → no stamping target
        _paint(g, 1, 1, _TEMPLATES[0], 2)
        return g
    if name == "frame_too_small":
        # frame interior too small to fit all 4 template variants
        _paint(g, 1, 1, _TEMPLATES[0], 2)
        draw_frame(g, 2, 7, 6, 11, 4)
        return g
    return g
