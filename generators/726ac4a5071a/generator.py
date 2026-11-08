"""Generator for arc_puzzle_bank_21_set8_s:S8_M7 — infer row period.

Rule: each row has a periodic prefix (1-3 cycle period). Extend the
prefix to fill the entire row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, period_len,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_prefix, full_row_already, single_cell_prefix.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "726ac4a5071a"
VERSION = "2.0.0"
TASK_ID = "726ac4a5071a"
SUMMARY = (
    "0-bg grid (h~3-5, w~"
    "10-14) where EACH "
    "ROW r contains a "
    "PERIODIC PREFIX: a "
    "cycle of length P_r "
    "∈ {1, 2, 3} repeated "
    "K_r ≥ 2 times "
    "starting at col 0, "
    "followed by TRAILING "
    "0-CELLS to col w-1. "
    "The prefix length "
    "K_r * P_r < w (so "
    "trailing 0s exist). "
    "Each row's period "
    "uses a random "
    "selection of colors "
    "from {1..9}. Rule "
    "(INFER ROW PERIOD, "
    "EXTEND PREFIX TO "
    "FILL ENTIRE ROW): "
    "For EACH ROW r: "
    "DETECT the PERIODIC "
    "CYCLE by finding "
    "the smallest period "
    "length P that makes "
    "the prefix self-"
    "repeating. EXTEND "
    "the cycle by "
    "repeating the "
    "period FROM CELL 0 "
    "all the way TO COL "
    "w-1. Trailing 0s "
    "get filled with "
    "cycle continuation. "
    "Net: each row's "
    "periodic prefix "
    "extends to fill "
    "the full row width."
)

INVARIANTS = [
    "background is 0 (only after the prefix)",
    "each row's prefix is at least one full period AND has trailing 0s",
    "period length is 1-3",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_prefix", "full_row_already", "single_cell_prefix")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..5", "valid": "2..6"},
    "grid_w":         {"type": "int", "default": "rng 10..14", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "period_len":     {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "row_periodic_prefix",
                       "valid": "row_periodic_prefix"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 3, 4)
        w = ctx.draw_int("grid_w", 10, 11)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 4, 5)
        w = ctx.draw_int("grid_w", 13, 14)
    else:
        h = ctx.draw_int("grid_h", 3, 5)
        w = ctx.draw_int("grid_w", 10, 14)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for r in range(h):
        period_len = rng.randint(1, 3)
        period = [rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9]) for _ in range(period_len)]
        repeats = rng.randint(2, max(2, (w - 2) // period_len))
        prefix_len = repeats * period_len
        if prefix_len >= w:
            prefix_len = period_len * (w // period_len - 1)
        for i in range(prefix_len):
            g[r][i] = period[i % period_len]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 4, 12
    g = full_grid(h, w, 0)
    if name == "no_prefix":
        # blank rows → no period to extend
        return g
    if name == "full_row_already":
        # row already filled to width → rule is identity (no trailing 0 to fill)
        for c in range(w): g[0][c] = (3 if c % 2 == 0 else 6)
        for c in range(w): g[1][c] = 4
        return g
    if name == "single_cell_prefix":
        # only one cell of color → period unrecoverable (no full period to detect)
        g[0][0] = 4
        g[2][0] = 6
        return g
    return g

def _row_prefix(row):
    i = 0
    while i < len(row) and row[i] != 0:
        i += 1
    return row[:i], row[i:]


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    for ri, row in enumerate(grid):
        prefix, suffix = _row_prefix(row)
        if not prefix:
            errors.append("row has no periodic prefix")
            continue
        if not suffix or any(v != 0 for v in suffix):
            errors.append("row must have a nonzero prefix followed by trailing zeros")
        ok = False
        for p in (1, 2, 3):
            if len(prefix) >= 2 * p and all(prefix[i] == prefix[i % p] for i in range(len(prefix))):
                ok = True
                break
        if not ok:
            errors.append("row prefix is not a recoverable 1..3-period repeated at least twice")
    return errors
