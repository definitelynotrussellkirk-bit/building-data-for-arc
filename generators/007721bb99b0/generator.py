"""Generator for puzzle d10ecb37.

Rule: `(rule! (lambda (g) (build-grid 2 2 (r c) (at g r c))))`. Output
is the top-left 2 × 2 corner of the input.

Combinatorial axes:
  * grid_h / grid_w     — outer canvas size
  * texture             — pattern: noise/sparse/blob/stripes/checker/...
  * tl_corner_kind      — what goes in the top-left 2 × 2 (controls the
                          actual output): mixed_4 / two_colors /
                          one_color / palette_corner
  * bg_color            — background color
  * fill_density        — how covered the rest of the grid is
  * caller-opt-in degenerates: monochrome (output uniform), single_cell,
                               only_corner_fg
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "007721bb99b0"
VERSION = "1.4.1"  # avoid 2x2 identity inputs; keep executable invariants.
TASK_ID = "007721bb99b0"
SUMMARY = "Any colored grid ≥ 2 × 2. Rule outputs the top-left 2 × 2 corner crop verbatim (preserving colors). Everything else is discarded."

# Rivals: 'output is full grid' refuted by any demo (output is small).
# 'output bottom-right 2x2' refuted by ≥1 demo where the corners
# differ. 'output 3x3' refuted by any demo (always 2x2). 'use mode
# color' refuted by any demo where the 2x2 contains rare colors.
# 3 demos with varied corners cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "h ≥ 2 and w ≥ 2",
    "the four top-left cells determine the entire output",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
TL_CORNER_KINDS = ("mixed_4", "two_colors", "one_color", "palette_corner", "with_bg")
DEGENERATE_TEXTURES = ("monochrome", "single_cell", "only_corner_fg")

AXES = {
    "grid_h":         {"type": "int",   "default": "rng 2..14", "valid": "2..15"},
    "grid_w":         {"type": "int",   "default": "rng 2..14", "valid": "2..15"},
    "texture":        {"type": "str",   "default": "rng helpful",
                       "valid": "noise|sparse|blob|stripes|gradient|checkerboard|frame|"
                                "ring|plus|monochrome|single_cell|only_corner_fg"},
    "tl_corner_kind": {"type": "str",   "default": "rng helpful",
                       "valid": "mixed_4|two_colors|one_color|palette_corner|with_bg"},
    "bg_color":       {"type": "color", "default": "rng",       "valid": "0..9"},
    "fill_density":   {"type": "float", "default": "rng 0.4..0.85", "valid": "0..1"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi = 2, 5
    elif difficulty == "hard":
        h_lo, h_hi = 10, 14
    else:
        h_lo, h_hi = 2, 14

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    # A 2x2 canvas makes the top-left crop identical to the input, so the
    # runner rightly rejects it as an identity demo. Keep tiny/easy examples,
    # but require at least one discarded row/column.
    if h == 2 and w == 2:
        w = 3
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    bg = int(overrides.get("bg_color", ctx.draw_color("bg_color")))
    # draw_distinct_colors returns a tuple; normalize to list once —
    # downstream shuffles/concats need a mutable list (was a TypeError
    # crash on ~1 in 6 seeds)
    palette = list(ctx.draw_distinct_colors("palette", n=5))
    if bg in palette:
        palette = [c for c in palette if c != bg] + [c for c in range(10) if c not in palette and c != bg][:1]

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

    # Force the top-left 2 × 2 to a specific kind for output diversity.
    tl_kind = overrides.get(
        "tl_corner_kind",
        ctx.draw_choice("tl_corner_kind", list(TL_CORNER_KINDS)))
    _set_top_left(g, tl_kind, palette, rng)

    if len({v for row in g for v in row}) < 2:
        g[h - 1][w - 1] = palette[0] if palette[0] != g[0][0] else palette[1]
    return g


def _set_top_left(g, kind, palette, rng):
    if not palette:
        palette = [1, 2]
    if kind == "mixed_4":
        # 4 distinct colors in the corner.
        chosen = palette[:4]
        if len(chosen) < 4:
            extras = [c for c in range(10) if c not in chosen]
            chosen = (chosen + extras)[:4]
        rng.shuffle(chosen)
        g[0][0] = chosen[0]
        g[0][1] = chosen[1]
        g[1][0] = chosen[2]
        g[1][1] = chosen[3]
    elif kind == "two_colors":
        a = palette[0]
        b = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
        g[0][0] = a; g[1][1] = a
        g[0][1] = b; g[1][0] = b
    elif kind == "one_color":
        c = palette[0]
        g[0][0] = c; g[0][1] = c; g[1][0] = c; g[1][1] = c
    elif kind == "palette_corner":
        chosen = palette[:4] if len(palette) >= 4 else palette + [palette[0]] * (4 - len(palette))
        g[0][0] = chosen[0]
        g[0][1] = chosen[1]
        g[1][0] = chosen[2]
        g[1][1] = chosen[3]
    elif kind == "with_bg":
        # 1-3 corner cells are background 0 — outputs containing bg are
        # reachable (they weren't before; every kind painted 4 fg cells)
        cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
        rng.shuffle(cells)
        n_bg = rng.randint(1, 3)
        for idx, (r, c) in enumerate(cells):
            g[r][c] = 0 if idx < n_bg else palette[idx % len(palette)]


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the corner-extraction signal is hidden.

    monochrome      — uniform input → uniform 2 × 2 output. Could be
                      confused with "fill with X."
    single_cell     — one fg cell off-corner; the corner is plain bg.
    only_corner_fg  — fg cells only inside the top-left 2 × 2; rest is
                      bg. Output looks "exactly like the visible part."
    """
    bg = 0
    g = full_grid(h, w, bg)
    palette = [c for c in range(1, 10)]
    rng.shuffle(palette)
    if name == "monochrome":
        color = palette[0]
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    if name == "single_cell":
        # h or w can be 2: the off-corner band may not exist — clamp
        rr = rng.randint(min(2, h - 1), h - 1)
        rc = rng.randint(min(2, w - 1), w - 1)
        g[rr][rc] = palette[0]
        return g
    if name == "only_corner_fg":
        for r in range(2):
            for c in range(2):
                g[r][c] = palette[(r * 2 + c) % len(palette)]
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 2 or w < 2:
        errors.append(f"grid is {h}x{w}, expected at least 2x2")
        return errors
    if h == 2 and w == 2:
        errors.append("normal sample is exactly 2x2, so crop output would equal input")
    colors = {v for row in grid for v in row}
    if len(colors) < 2:
        errors.append("normal sample collapsed to a monochrome grid")
    corner = [grid[0][0], grid[0][1], grid[1][0], grid[1][1]]
    if not corner:
        errors.append("missing top-left 2x2 corner")
    return errors
