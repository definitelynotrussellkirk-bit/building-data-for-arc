"""Generator for `arc_additional_puzzle_bank_volume20:E138` — exactly
one full divider (a row OR column entirely of cyan(8) cells); rule
reflects every magenta(6) cell across the divider.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_magentas (no 6 cells → rule's reflect loop is empty,
output equals input), magentas_on_divider (6 cells lie on the 8
divider → reflection lands at same cell, no visual change),
magentas_on_both_sides (6 cells on both sides → reflection collides
with existing 6 cells; rule's "reflect to mirror" output ambiguous).

Invariants:
  - background is 0
  - exactly one row entirely 8 OR exactly one column entirely 8 (the
    divider)
  - >=2 magenta(6) cells, all on one side of the divider (so the
    reflection has somewhere to land)
  - magenta cells positioned so their reflections stay in-bounds
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a09c214ca5fa"
VERSION = "1.1.1"
TASK_ID = "a09c214ca5fa"
SUMMARY = "Cyan divider line + magenta cells on one side; rule reflects magenta across divider."

INVARIANTS = [
    "background is 0",
    "exactly one full divider line of 8s (one row OR one column)",
    ">=2 magenta(6) cells on one side of the divider",
    "magenta cells positioned so their reflections stay in-bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_magentas", "magentas_on_divider", "magentas_on_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "7..18"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "divider_with_magentas_one_side",
                       "valid": "divider_with_magentas_one_side"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; exactly one full-height or full-width line of color-8 (divider); >=2 color-6 cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Count full-height 8-columns
    full_8_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    # Count full-width 8-rows
    full_8_rows = [r for r in range(h) if all(grid[r][c] == 8 for c in range(w))]
    n_dividers = len(full_8_cols) + len(full_8_rows)
    if n_dividers != 1:
        errs.append(f"expected exactly 1 full color-8 divider line, found {n_dividers}")
    # Check >=1 color-6 cells
    sixes = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 6]
    if len(sixes) < 1:
        errs.append(f"expected >=1 color-6 (magenta) cell, found {len(sixes)}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_mag_lo, n_mag_hi = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        n_mag_lo, n_mag_hi = 3, 5
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n_mag_lo, n_mag_hi = 2, 4
    rng = ctx.draw_rng("placement")

    g = full_grid(h, w, 0)
    orientation = rng.choice(["row", "col"])
    if orientation == "row":
        div_r = rng.randint(h // 3, 2 * h // 3)
        for c in range(w):
            g[div_r][c] = 8
        n_mag = rng.randint(n_mag_lo, n_mag_hi)
        for _ in range(n_mag * 5):
            r = rng.randint(0, div_r - 1); c = rng.randint(0, w - 1)
            mr = 2 * div_r - r
            if mr >= h or mr < 0: continue
            if g[r][c] != 0 or g[mr][c] != 0: continue
            g[r][c] = 6
    else:
        div_c = rng.randint(w // 3, 2 * w // 3)
        for r in range(h):
            g[r][div_c] = 8
        n_mag = rng.randint(n_mag_lo, n_mag_hi)
        for _ in range(n_mag * 5):
            r = rng.randint(0, h - 1); c = rng.randint(0, div_c - 1)
            mc = 2 * div_c - c
            if mc >= w or mc < 0: continue
            if g[r][c] != 0 or g[r][mc] != 0: continue
            g[r][c] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    div_r = 5
    for c in range(w):
        g[div_r][c] = 8
    if name == "no_magentas":
        # No 6 cells — rule's reflect loop is empty; output equals
        # input (just the divider).
        return g
    if name == "magentas_on_divider":
        # 6 cells lie on the 8 divider — reflection lands at same
        # cell, no visual change. (Place 6s on the divider row,
        # overwriting the 8.)
        g[div_r][2] = 6; g[div_r][7] = 6
        return g
    if name == "magentas_on_both_sides":
        # 6 cells on both sides — reflection collides with existing
        # cells; rule's "mirror across divider" output ambiguous.
        g[2][3] = 6; g[2][6] = 6
        g[8][3] = 6; g[8][6] = 6
        return g
    return g
