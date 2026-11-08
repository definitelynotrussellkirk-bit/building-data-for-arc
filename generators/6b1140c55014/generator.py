"""Generator for 462c09d6.

Rule: find col with 4s. Crop-to-content left half + crop-to-content right
half; vconcat (heights stack, widths must match).

Combinatorial axes (8): grid_h/w, sep_col_position, shape_width_k,
left_height, right_height, palette_kind, position_bias,
shape_density.
Degenerates: no_separator, multiple_separators, empty_halves.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b1140c55014"
VERSION = "2.1.1"  # guard spread sep_col randint at easy w=10 (w-6=4<5 → empty randrange(5,5))
TASK_ID = "6b1140c55014"
SUMMARY = (
    "0-bg grid (h~10-16, w~"
    "12-18) with: (a) ONE "
    "FULL COLOR-4 (yellow) "
    "SEPARATOR COLUMN at "
    "sep_col (position bias: "
    "center/spread/edge); "
    "(b) a LEFT SHAPE of "
    "width k (3-4) × height "
    "left_h (2-4) in some "
    "color from the palette "
    "(non-4), placed in the "
    "left half; (c) a RIGHT "
    "SHAPE of same width k × "
    "height right_h (2-4) in "
    "a distinct color in the "
    "right half. Shape "
    "density 0.5-0.9 — both "
    "shapes have 4 corner "
    "cells set + extra cells "
    "scattered inside. Rule "
    "(VCONCAT CROPPED HALVES): "
    "identify the FULL 4-COL "
    "SEPARATOR. CROP the LEFT "
    "HALF (cols 0..sep_col-1) "
    "to its non-bg CONTENT "
    "BBOX. CROP the RIGHT "
    "HALF (cols sep_col+1..w-1) "
    "to its non-bg CONTENT "
    "BBOX. VCONCAT (stack "
    "vertically) the two "
    "crops (left on top, "
    "right below). Widths "
    "must match (both = k). "
    "Output height = "
    "left_h + right_h, width "
    "= k. Net: 4-separator "
    "drives a vertical stack "
    "of left then right "
    "cropped shapes."
)

INVARIANTS = [
    "exactly one column fully filled with color 4",
    "left half contains a shape of width k",
    "right half contains a shape of width k (same k as left)",
    "no other 4-cells",
]

POSITION_BIAS = ("center", "spread", "edge")
PALETTE_KINDS = ("warm", "cool", "broad")
DEGENERATE_TEXTURES = ("no_separator", "multiple_separators", "empty_halves")
HELPFUL_TEXTURES = POSITION_BIAS

AXES = {
    "grid_h":           {"type": "int", "default": "rng 10..16", "valid": "8..20"},
    "grid_w":           {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "sep_col_position": {"type": "str", "default": "rng helpful",
                         "valid": "center|spread|edge"},
    "shape_width_k":    {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "left_height":      {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "right_height":     {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "palette_kind":     {"type": "str", "default": "rng helpful",
                         "valid": "warm|cool|broad"},
    "shape_density":    {"type": "float", "default": "rng 0.5..0.9",
                         "valid": "0.3..1"},
    "texture":          {"type": "str", "default": "alias for sep_col_position",
                         "valid": "center|spread|edge|no_separator|multiple_separators|empty_halves"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; exactly one full-height color-4 (yellow separator) column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    full_4_cols = [c for c in range(w) if all(grid[r][c] == 4 for r in range(h))]
    if not full_4_cols:
        return errs  # degenerate (no_separator) — allowed
    if len(full_4_cols) != 1:
        errs.append(f"found {len(full_4_cols)} full-height color-4 cols; expected 1")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 8, 11, 10, 13
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 14, 20, 16, 22
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 16, 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    sep_pos = (overrides.get("texture") or
               overrides.get("sep_col_position")
               or ctx.draw_choice("sep_col_position",
                                  list(POSITION_BIAS)))
    if sep_pos == "center":
        sep_col = w // 2
    elif sep_pos == "edge":
        sep_col = rng.choice([5, w - 6])
    else:
        # The 5/6 margins assume w≥11; at easy w=10, w-6=4<5 makes the spread
        # `randint(5, 4)` an empty randrange(5,5). center/edge don't crash and the
        # clamp below already lands them on 5 (the only feasible separator for w=10
        # under these margins), so guard only the randint and let the clamp finish.
        sep_col = rng.randint(5, w - 6) if w - 6 >= 5 else 5
    sep_col = max(5, min(w - 6, sep_col))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    if palette_kind == "warm":
        pool = [3, 4, 6, 9]
    elif palette_kind == "cool":
        pool = [1, 5, 7, 8]
    else:
        pool = [1, 2, 3, 5, 6, 7, 8, 9]
    pool = [c for c in pool if c != 4]
    rng.shuffle(pool)
    palette = pool[:2]
    if len(palette) < 2:
        palette = [1, 2]
    left_color, right_color = palette[0], palette[1]
    k = int(overrides.get("shape_width_k",
                          ctx.draw_int("shape_width_k", 3,
                                       min(4, sep_col, w - sep_col - 1))))
    k = max(2, min(min(sep_col, w - sep_col - 1), k))
    left_h = int(overrides.get("left_height",
                               ctx.draw_int("left_height", 2, 4)))
    right_h = int(overrides.get("right_height",
                                ctx.draw_int("right_height", 2, 4)))
    left_h = max(2, min(h - 2, left_h))
    right_h = max(2, min(h - 2, right_h))
    density = float(overrides.get("shape_density",
                                  ctx.draw_rng("shape_density")
                                  .uniform(0.5, 0.9)))
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][sep_col] = 4
    left_r = rng.randint(0, h - left_h - 1)
    left_c = rng.randint(0, sep_col - k)
    _place_shape(g, left_r, left_c, left_h, k, left_color, density, rng)
    right_r = rng.randint(0, h - right_h - 1)
    right_c = rng.randint(sep_col + 1, w - k)
    _place_shape(g, right_r, right_c, right_h, k, right_color, density, rng)
    return g


def _place_shape(g, r0, c0, h, w, color, density, rng):
    cells = [(r, c) for r in range(r0, r0 + h) for c in range(c0, c0 + w)]
    g[r0][c0] = color
    g[r0][c0 + w - 1] = color
    g[r0 + h - 1][c0] = color
    g[r0 + h - 1][c0 + w - 1] = color
    n = max(4, int(len(cells) * density))
    chosen = rng.sample(cells, min(n, len(cells)))
    for r, c in chosen:
        g[r][c] = color


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    sep_col = w // 2
    if name == "no_separator":
        return g
    if name == "multiple_separators":
        for c in range(0, w, max(1, w // 3)):
            for r in range(h):
                g[r][c] = 4
        return g
    if name == "empty_halves":
        for r in range(h):
            g[r][sep_col] = 4
        return g
    return g
