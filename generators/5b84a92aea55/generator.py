"""Generator for ARC task 8618d23e.

Rule: input is even-height. Output is (h+1) × (w+1):
  - Top half (rows 0..h/2-1): rows 0..h/2-1 from input, plus a 9 in
    the appended right column.
  - Separator row at r = h/2: all 9s.
  - Bottom half (rows h/2+1..h): a 9 in the prepended left column,
    plus rows h/2..h-1 from input shifted right by 1, in REVERSED
    bottom-half row order.

Combinatorial axes (8):
  * grid_h (even) / grid_w
  * palette_size, texture
  * top_pattern (random/striped/blob/diag)
  * bot_pattern (independent of top)
  * top_bot_relation (independent / mirror_pair / same)
  * fill_density
  * caller-opt-in degenerates: monochrome, top_all_zero, bot_all_zero
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "5b84a92aea55"
VERSION = "2.0.1"
TASK_ID = "5b84a92aea55"
SUMMARY = (
    "0-bg EVEN-HEIGHT compact grid (h ∈ {2,4,6}, "
    "w ∈ {1,2,3}) filled by one of 9 "
    "TEXTURES (noise / sparse / blob / "
    "stripes / gradient / checkerboard / "
    "frame / ring / plus) using a palette "
    "of 1-8 distinct non-9 colors. Optional "
    "bg_density and noise_overlay layers. "
    "Optionally TOP_BOT_RELATION ties the "
    "two halves (independent / mirror_pair "
    "/ same / complementary). Colors "
    "exclude 9 (reserved for separator). "
    "Rule (PRODUCE (h+1) × (w+1) OUTPUT: "
    "TOP HALF KEPT, SEPARATOR ROW/COL "
    "ADDED, BOTTOM HALF REVERSED AND "
    "SHIFTED): the OUTPUT has dimensions "
    "(h+1) × (w+1). TOP HALF rows 0..h/2-"
    "1: copy rows 0..h/2-1 from input "
    "into output's rows 0..h/2-1, with "
    "a 9 appended in the new right column "
    "(c=w). SEPARATOR ROW at output row "
    "r = h/2: all cells = 9. BOTTOM HALF "
    "rows h/2+1..h: a 9 in the prepended "
    "LEFT column (c=0), plus rows "
    "h/2..h-1 from the input shifted "
    "RIGHT by 1 and in REVERSED ROW "
    "ORDER (input row h/2 → output row "
    "h, input row h-1 → output row h/2+1). "
    "Net: top half preserved, bottom half "
    "flipped vertically and inset by a "
    "row/column of 9-separator, output "
    "grows by 1 row × 1 col."
)

# Rivals: 'output equals input' refuted by any demo (output is larger,
# has 9-separator). 'use a different separator color' refuted by any
# demo (always 9). 'keep bottom row order' refuted by ≥2 demos where
# bottom-half reversal is observable.
# 4 demos with varied heights + textures + relations cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "input height is even (so h/2 is the split point)",
    "input colors exclude 9 (rule's separator color)",
    "≥2 distinct fg colors so the output is informative",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
TOP_BOT_RELATIONS = ("independent", "mirror_pair", "same", "complementary")
DEGENERATE_TEXTURES = ("monochrome", "top_all_zero", "bot_all_zero")

AXES = {
    "grid_h":           {"type": "choice", "default": "rng even 2..6",
                         "valid": "2|4|6"},
    "grid_w":           {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_size":     {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "texture":          {"type": "str", "default": "rng helpful",
                         "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "top_bot_relation": {"type": "str", "default": "rng helpful",
                         "valid": "|".join(TOP_BOT_RELATIONS)},
    "bg_density":       {"type": "float", "default": "rng 0..0.4", "valid": "0..0.95"},
    "noise_overlay":    {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
    "include_zero":     {"type": "bool", "default": "rng", "valid": "true|false"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_choices, w_lo, w_hi = [2, 4], 1, 2
    elif difficulty == "hard":
        h_choices, w_lo, w_hi = [4, 6], 2, 4
    else:
        # Canonical examples are tiny (2x1, 4x2, 6x3).  The previous 10..18 x
        # 10..18 hard band taught a different size regime and tripped the drift
        # linter without adding a new semantic axis.
        h_choices, w_lo, w_hi = [2, 4, 6], 1, 3
    h = ctx.draw_choice("grid_h", h_choices)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    n_colors = ctx.draw_int("palette_size", 2, 5)
    palette = ctx.draw_distinct_colors("palette", n=n_colors, exclude={9})
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    relation = overrides.get("top_bot_relation",
                             ctx.draw_choice("top_bot_relation", list(TOP_BOT_RELATIONS)))
    g = fill_texture(texture, h, w, palette, rng)
    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.4)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)
    bh = h // 2
    if relation == "mirror_pair":
        for r in range(bh):
            for c in range(w):
                g[h - 1 - r][c] = g[r][c]
    elif relation == "same":
        for r in range(bh):
            for c in range(w):
                g[bh + r][c] = g[r][c]
    elif relation == "complementary":
        for r in range(bh):
            for c in range(w):
                if len(palette) > 1 and g[r][c] != palette[0]:
                    g[bh + r][c] = palette[0]
                elif len(palette) > 1:
                    g[bh + r][c] = palette[1]
    if len({v for row in g for v in row}) < 2:
        g[0][0] = palette[0]
        g[-1][-1] = palette[1] if len(palette) > 1 else (palette[0] + 1) % 10
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify top/bottom halves with separator invariants for 5b84a92aea55."""
    errs = []
    h, w = len(grid), len(grid[0])
    if h % 2 != 0:
        errs.append(f"input height {h} is odd (need even for h/2 split)")
    if h not in {2, 4, 6} or not (1 <= w <= 4):
        errs.append(f"expected compact canonical-sized input, got {h}x{w}")
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    if 9 in flat:
        errs.append("color 9 present in input (reserved as separator color for output)")
    colors = {v for v in flat}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct color(s) — need >=2 for visible mirror")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    g = full_grid(h, w, palette[0])
    if name == "monochrome":
        c0 = rng.choice(palette)
        for r in range(h):
            for c in range(w):
                g[r][c] = c0
        return g
    if name == "top_all_zero":
        # Top half is all 0; bottom is colorful.
        bh = h // 2
        for r in range(bh, h):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        return g
    if name == "bot_all_zero":
        bh = h // 2
        for r in range(bh):
            for c in range(w):
                g[r][c] = rng.choice(palette)
        for r in range(bh, h):
            for c in range(w):
                g[r][c] = 0
        return g
    return g
