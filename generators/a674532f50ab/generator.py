"""Generator for puzzle 5bd6f4ac.

Rule: `(rule! (lambda (g) (build-grid 3 3 (r c) (at g r (+ c (- (cols g) 3))))))`.
Output is the top-right 3 × 3 corner of the input.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * texture             — pattern: noise/sparse/blob/stripes/checker/...
  * tr_corner_kind      — what the top-right 3 × 3 looks like:
                          mixed_9 / two_colors / one_color / palette_corner
  * bg_color            — background color
  * fill_density        — coverage of non-corner area
  * caller-opt-in degenerates: monochrome, only_corner_fg, single_cell_in_corner
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "a674532f50ab"
VERSION = "2.1.0"  # fix all_background (one_color corner -> solid 3x3 output) + identity (3x3 input -> crop == whole input): draw the corner from a MULTI-colour subset and never emit a 3x3 input.
TASK_ID = "a674532f50ab"
SUMMARY = (
    "Any colored grid of size at least 3×3 "
    "(typical h, w ~3-14). The grid is filled "
    "with a TEXTURE (noise / sparse / blob / "
    "stripes / gradient / checkerboard / frame "
    "/ ring / plus) using a 5-color palette + "
    "a chosen background color. The TOP-RIGHT "
    "3×3 CORNER is overlaid with a specific "
    "pattern (mixed_9, two_colors, one_color, "
    "or palette_corner). Rule: EXTRACT the "
    "TOP-RIGHT 3×3 CORNER of the input grid "
    "(rows 0, 1, 2 × cols w-3, w-2, w-1) and "
    "RETURN it as the entire output. The rest "
    "of the input is discarded. Output is a "
    "3×3 grid. Net: rule is just 'crop to "
    "top-right 3×3 corner' regardless of input "
    "size or content."
)

INVARIANTS = [
    "h ≥ 3 and w ≥ 3",
    "the top-right 3 × 3 cells determine the entire output",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
TR_CORNER_KINDS = ("mixed_9", "two_colors", "one_color", "palette_corner")
# Corner kinds that GUARANTEE >=2 colours (so the cropped output is not a
# solid board). one_color is kept valid only via explicit override.
HELPFUL_CORNER_KINDS = ("mixed_9", "two_colors", "palette_corner")
DEGENERATE_TEXTURES = ("monochrome", "only_corner_fg", "single_cell_in_corner")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 3..14", "valid": "3..15"},
    "grid_w":         {"type": "int",   "default": "rng 3..14", "valid": "3..15"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "tr_corner_kind": {"type": "str",   "default": "rng helpful",
                       "valid": "|".join(TR_CORNER_KINDS)},
    "bg_color":       {"type": "color", "default": "rng",       "valid": "0..9"},
    "fill_density":   {"type": "float", "default": "rng 0.4..0.85", "valid": "0..1"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi = 3, 5
    elif difficulty == "hard":
        h_lo, h_hi = 10, 14
    else:
        h_lo, h_hi = 3, 14

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    # A 3x3 input makes the top-right-3x3 crop equal the whole grid (identity);
    # widen so the crop is always a proper sub-grid.
    if h == 3 and w == 3:
        w = 4
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bg = int(overrides.get("bg_color", ctx.draw_color("bg_color")))
    palette = list(ctx.draw_distinct_colors("palette", n=5))
    if bg in palette:
        palette = [c for c in palette if c != bg] + \
                  [c for c in range(10) if c not in palette and c != bg][:1]

    texture = overrides.get(
        "texture",
        ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    full_palette = [bg, *palette]
    g = fill_texture(texture, h, w, full_palette, rng)

    bg_d = float(overrides.get(
        "fill_density",
        ctx.draw_rng("fill_density").uniform(0.4, 0.85)))
    if bg_d < 1.0:
        g = apply_bg_density(g, full_palette, rng, 1.0 - bg_d)
    no = float(overrides.get(
        "noise_overlay",
        ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, full_palette, rng, no)

    tr_kind = overrides.get(
        "tr_corner_kind",
        ctx.draw_choice("tr_corner_kind", list(HELPFUL_CORNER_KINDS)))
    _set_top_right(g, tr_kind, palette, rng)

    if len({v for row in g for v in row}) < 2:
        g[h - 1][0] = palette[0] if palette[0] != g[0][0] else palette[1]
    return g


def _set_top_right(g, kind, palette, rng):
    h = len(g); w = len(g[0])
    if not palette:
        palette = [1, 2]
    rs = list(range(0, 3))
    cs = list(range(w - 3, w))
    if kind == "mixed_9":
        chosen = list(palette[:9])
        if len(chosen) < 9:
            extras = [c for c in range(10) if c not in chosen]
            chosen = (chosen + extras)[:9]
        rng.shuffle(chosen)
        idx = 0
        for r in rs:
            for c in cs:
                g[r][c] = chosen[idx]
                idx += 1
    elif kind == "two_colors":
        a = palette[0]
        b = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
        for r in rs:
            for c in cs:
                g[r][c] = a if (r + c) % 2 == 0 else b
    elif kind == "one_color":
        c0 = palette[0]
        for r in rs:
            for c in cs:
                g[r][c] = c0
    elif kind == "palette_corner":
        chosen = palette[:9] if len(palette) >= 9 else \
                 palette + [palette[0]] * (9 - len(palette))
        idx = 0
        for r in rs:
            for c in cs:
                g[r][c] = chosen[idx % len(chosen)]
                idx += 1


def self_check(grid, *, difficulty=None, meta=None):
    """The top-right 3x3 corner (the entire output) must have >=2 colours,
    and the input must be larger than 3x3 (else the crop equals the input)."""
    h, w = len(grid), len(grid[0])
    issues = []
    if h < 3 or w < 3:
        return ["grid smaller than 3x3"]
    if h == 3 and w == 3:
        issues.append("input is exactly 3x3 -> crop equals input (identity)")
    corner = {grid[r][c] for r in range(3) for c in range(w - 3, w)}
    if len(corner) < 2:
        issues.append("top-right 3x3 corner is a single colour -> solid output")
    return issues


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the top-right-3x3 extraction is hidden.

    monochrome             — uniform input → uniform 3 × 3 output;
                              ambiguous with "fill 3 × 3."
    only_corner_fg         — only the top-right 3 × 3 has fg cells;
                              rest is bg → output looks "exactly like"
                              the visible non-bg area.
    single_cell_in_corner  — one fg cell inside the corner; output is
                              minimal.
    """
    bg = 0
    g = full_grid(h, w, bg)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if name == "monochrome":
        c = palette[0]
        for r in range(h):
            for cc in range(w):
                g[r][cc] = c
        return g
    if name == "only_corner_fg":
        for r in range(3):
            for c in range(w - 3, w):
                g[r][c] = palette[(r + c) % len(palette)]
        return g
    if name == "single_cell_in_corner":
        r = rng.randint(0, 2)
        c = rng.randint(w - 3, w - 1)
        g[r][c] = palette[0]
        return g
    return g
