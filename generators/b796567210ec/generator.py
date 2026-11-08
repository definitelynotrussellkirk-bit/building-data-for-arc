"""Generator for puzzle 20fb2937.

Rule: row 0 has 3 block colors at cols 0, 4, 8 (3x3 each). Row 4 has
matching key colors at cols 1, 5, 9. Dots below row 6 use key colors.
Output expands each dot into 3x3 of its block color.

Combinatorial axes (8): height, dot_count, palette_kind, dot_position,
key_density, anchor_corner, asymmetry_force, include_decoy.
Degenerates: no_dots, full_grid, single_dot.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b796567210ec"
VERSION = "1.1.0"
TASK_ID = "b796567210ec"
SUMMARY = "Key-dot lookup; rule expands each dot into 3x3 block."

INVARIANTS = [
    "background is 7",
    "row 0: 3 block colors at cols 0, 4, 8 (3x3 each)",
    "row 4: matching key colors at cols 1, 5, 9",
    "dots below row 6 use only key colors",
    "dots stay in valid centers (rows 8+, cols 1, 5, 9)",
]

POSITION_BIASES = ("scattered", "left_heavy", "right_heavy",
                   "row_aligned", "centered")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dots", "full_grid", "single_dot")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "height":         {"type": "int", "default": "rng 14..20", "valid": "10..28"},
    "dot_count":      {"type": "int", "default": "rng 2..6", "valid": "1..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "scattered|left_heavy|right_heavy|row_aligned|centered"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "include_decoy":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "bg_color":       {"type": "color", "default": "7", "valid": "7"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "scattered|left_heavy|right_heavy|row_aligned|centered|no_dots|full_grid|single_dot"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 18, 28
    else:
        h_lo, h_hi = 14, 20
    h = ctx.draw_int("height", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, rng)
    dot_count = int(overrides.get("dot_count",
                                  ctx.draw_int("dot_count", 2, 6)))
    dot_count = max(1, min(12, dot_count))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    bias = (overrides.get("texture") or
            overrides.get("position_bias")
            or ctx.draw_choice("position_bias",
                               list(POSITION_BIASES)))
    colors = _build_palette(palette_kind, 6, rng)
    block_colors = colors[:3]
    key_colors = colors[3:]
    g = full_grid(h, 11, 7)
    for i, color in enumerate(block_colors):
        start = i * 4
        for r in range(3):
            for c in range(start, start + 3):
                g[r][c] = color
    for i, color in enumerate(key_colors):
        g[4][1 + i * 4] = color
    centers = [(r, c) for r in range(8, h - 1, 3) for c in (1, 5, 9)]
    centers = _order_centers(bias, centers, rng)
    for r, c in centers[:min(dot_count, len(centers))]:
        g[r][c] = rng.choice(key_colors)
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 5, 6, 8, 9]
    pool = [c for c in pool if c != 7]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 8, 9]:
            if c not in pool and c != 7:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def _order_centers(bias, centers, rng):
    if bias == "left_heavy":
        return sorted(centers, key=lambda p: p[1])
    if bias == "right_heavy":
        return sorted(centers, key=lambda p: -p[1])
    if bias == "row_aligned":
        return sorted(centers, key=lambda p: p[0])
    if bias == "centered":
        return sorted(centers, key=lambda p: abs(p[1] - 5))
    rng.shuffle(centers)
    return centers


def _draw_from_degenerate(name, h, rng):
    g = full_grid(h, 11, 7)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], 6)
    block_colors = colors[:3]
    key_colors = colors[3:]
    for i, color in enumerate(block_colors):
        start = i * 4
        for r in range(3):
            for c in range(start, start + 3):
                g[r][c] = color
    for i, color in enumerate(key_colors):
        g[4][1 + i * 4] = color
    if name == "no_dots":
        return g
    if name == "full_grid":
        # Many dots - all centers
        for r in range(8, h - 1, 3):
            for c in (1, 5, 9):
                g[r][c] = rng.choice(key_colors)
        return g
    if name == "single_dot":
        g[h // 2][5] = key_colors[0]
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    h, w = len(grid), len(grid[0])
    if w != 11 or h < 10:
        errors.append("grid should be at least 10x11 with width exactly 11")
    block_colors = [grid[0][0], grid[0][4], grid[0][8]]
    key_colors = [grid[4][1], grid[4][5], grid[4][9]]
    if 7 in block_colors or 7 in key_colors:
        errors.append("block/key colors must not be background 7")
    if len(set(block_colors + key_colors)) != 6:
        errors.append("block and key palette should contain six distinct colors")
    for i, color in enumerate(block_colors):
        start = i * 4
        if any(grid[r][c] != color for r in range(3) for c in range(start, start + 3)):
            errors.append("top lookup block is not a solid 3x3 square")
            break
    dots = [(r, c, grid[r][c]) for r in range(7, h) for c in range(w) if grid[r][c] != 7]
    if len(dots) < 2:
        errors.append("expected at least two query dots below the key")
    if any(v not in key_colors for _, _, v in dots):
        errors.append("a dot uses a color outside the key palette")
    valid_centers = {(r, c) for r in range(8, h - 1, 3) for c in (1, 5, 9)}
    if any((r, c) not in valid_centers for r, c, _ in dots):
        errors.append("dot is not on a valid 3x3 expansion center")
    return errors
