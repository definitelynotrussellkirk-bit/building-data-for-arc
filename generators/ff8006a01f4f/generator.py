"""Generator for arc_puzzle_bank_21_set8_s:S8_E7.

Rule: each row's leading nonzero prefix is repeated to fill the row width.

Combinatorial axes (8): grid_h/w, palette_kind, prefix_len,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: prefix_full_width, all_zero_grid, single_color_prefixes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff8006a01f4f"
VERSION = "2.1.0"
TASK_ID = "ff8006a01f4f"
SUMMARY = (
    "0-bg grid (h~4-12, w~6-16) where each row starts "
    "with a contiguous non-zero PREFIX of random length 1-6 "
    "and random colors from {1..9} (some rows may be blank), "
    "followed by zeros to the row end. Rule: for "
    "each row, identify the leading non-zero prefix "
    "pattern. TILE that prefix REPEATEDLY across the "
    "full row width (modular index — the prefix pattern "
    "repeats c mod prefix_len). Net: each row becomes a "
    "periodic tiling of its initial prefix."
)

INVARIANTS = [
    "background is 0",
    "each active row starts with a contiguous nonzero prefix",
    "the rest of each active row begins blank",
    "outputs repeat the prefix pattern to the row width",
]

PALETTE_KINDS = ("varied_lengths", "stepped_lengths", "monocolor_prefixes", "rainbow")
DEGENERATE_TEXTURES = ("prefix_full_width", "all_zero_grid", "single_color_prefixes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "3..12"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "prefix_len":     {"type": "int", "default": "rng 1..6", "valid": "0..6"},
    "palette_size":   {"type": "int", "default": "9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "leftmost", "valid": "leftmost"},
    "n_distinct_colors": {"type": "int", "default": "up to 9", "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 6, 10)
        plen_max = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 11, 16)
        plen_max = 6
    else:
        h = ctx.draw_int("grid_h", 5, 10)
        w = ctx.draw_int("grid_w", 8, 14)
        plen_max = 6
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    palette = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    # Each row: a RANDOM-content contiguous prefix (random length, random colors)
    # which the rule tiles to the full width. Random content (vs the old fixed
    # (r+c)%6 diagonal) and the full palette maximize pattern/color diversity;
    # occasional all-zero rows stay blank (rule tiles an empty prefix to zeros),
    # exercising that case. >=1 non-blank row guaranteed.
    forced = rng.randrange(h)
    for r in range(h):
        if r != forced and rng.randint(0, 99) < 15:
            continue                       # leave this row blank
        length = rng.randint(1, min(plen_max, w - 1))
        for c in range(length):
            g[r][c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 10
    g = full_grid(h, w, 0)
    palette = [2, 3, 4, 6, 7, 9]
    if name == "prefix_full_width":
        for r in range(h):
            for c in range(w):
                g[r][c] = palette[(r + c) % len(palette)]
        return g
    if name == "all_zero_grid":
        return g
    if name == "single_color_prefixes":
        for r in range(h):
            for c in range(2):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify each active row has a leading nonzero prefix followed only by zeros."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errors = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w}")
    active = 0
    for r, row in enumerate(grid):
        bad = [v for v in row if not isinstance(v, int) or not (0 <= v <= 9)]
        if bad:
            errors.append(f"row {r} has out-of-palette values: {bad}")
            continue
        if all(v == 0 for v in row):
            continue
        active += 1
        if row[0] == 0:
            errors.append(f"row {r} has a nonzero cell but no leading prefix at column 0")
            continue
        first_zero = next((c for c, v in enumerate(row) if v == 0), w)
        if first_zero == w:
            errors.append(f"row {r} prefix spans full width; default rows need a blank suffix")
        if any(v == 0 for v in row[:first_zero]):
            errors.append(f"row {r} prefix is not contiguous")
        if any(v != 0 for v in row[first_zero:]):
            errors.append(f"row {r} has nonzero cells after the prefix ends")
    if active == 0:
        errors.append("no active prefix rows found")
    return errors
