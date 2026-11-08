"""Generator for 95755ff2.

Rule: exterior colored pixels shoot straight rays into a color-2 diamond
interior.

Combinatorial axes (8): grid_h/w, ray_layout, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_diamond, no_rays, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5b35376e1fc9"
RULE_HASH = "df67b1ec5fb3"  # canonical rule this generator was written against
# 3.2.0: defect-lint identity_demo — a border pixel aligned with the diamond's
# TIP row/col (a single-2 line with no range) gave the ray no interior to paint
# (output == input). Pixels now target strictly interior diamond lines.
# (3.1.0: varied grid N + radius + aligned border pixels.)
VERSION = "3.2.0"
TASK_ID = "5b35376e1fc9"
SUMMARY = (
    "Fixed 13×13 0-bg grid containing: (a) a "
    "CENTERED COLOR-2 (red) DIAMOND OUTLINE of "
    "radius 4 centered at (6, 6) — diamond "
    "boundary cells trace the manhattan-radius "
    "shape; (b) 2-4 EXTERIOR COLORED PIXELS on "
    "the GRID BORDER aligned with the diamond's "
    "horizontal/vertical AXIS (col 6 and row 6) "
    "in 4 distinct non-{0, 2} colors. Layout "
    "varies (cross / vertical / horizontal). "
    "Rule: for EACH exterior border PIXEL, cast "
    "a STRAIGHT RAY INWARD toward the grid "
    "center in its color. The ray travels "
    "through 0 cells until it reaches the "
    "diamond's OPPOSITE BOUNDARY (red color-2 "
    "cell) — at which point it stops. The "
    "exterior pixel and the diamond outline "
    "stay. Net: input is a red diamond outline "
    "+ exterior border pixels; output adds "
    "colored rays from those pixels inward "
    "until they hit the diamond."
)

INVARIANTS = [
    "the background is zero",
    "color 2 forms a centered diamond outline",
    "exterior colored pixels align with valid diamond rows or columns",
    "rays paint inward until they reach the opposite diamond boundary or an interior obstacle",
]

LAYOUTS = ("cross", "vertical", "horizontal")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_diamond", "no_rays", "full_grid")
HELPFUL_TEXTURES = LAYOUTS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..21", "valid": "11..21"},
    "grid_w":         {"type": "int", "default": "rng 11..21", "valid": "11..21"},
    "ray_layout":     {"type": "str", "default": "rng helpful",
                       "valid": "|".join(LAYOUTS)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "4", "valid": "4"},
    "texture":        {"type": "str", "default": "alias for ray_layout",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_diamond(g, cr, cc, radius):
    for r in range(cr - radius, cr + radius + 1):
        d = radius - abs(r - cr)
        g[r][cc - d] = 2
        g[r][cc + d] = 2


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    layout = (overrides.get("texture") if overrides.get("texture") in LAYOUTS else None) or \
             overrides.get("ray_layout") or \
             ctx.draw_choice("ray_layout", list(LAYOUTS))
    colors = ctx.draw_distinct_colors("ray_colors", n=4, exclude={0, 2})
    # rule is size-generic (reads the color-2 diamond's row/col ranges + shoots
    # rays from border pixels). Vary grid size + diamond radius + the (diamond-
    # aligned) border-pixel positions so rays still strike the diamond.
    if difficulty == "easy":
        N = ctx.draw_int("grid_n", 11, 13)
    elif difficulty == "hard":
        N = ctx.draw_int("grid_n", 15, 21)
    else:
        N = ctx.draw_int("grid_n", 11, 17)
    if N % 2 == 0:
        N += 1
    center = N // 2
    r = rng.randint(3, center - 1)
    g = full_grid(N, N, 0)
    _draw_diamond(g, center, center, r)
    # Strictly interior diamond lines: the TIP row/col holds a single 2 (no
    # range), so a ray aligned with it has no interior to paint (identity).
    lo, hi = center - r + 1, center + r - 1
    if layout in {"cross", "vertical"}:
        g[0][rng.randint(lo, hi)] = colors[0]
        g[N - 1][rng.randint(lo, hi)] = colors[1]
    if layout in {"cross", "horizontal"}:
        g[rng.randint(lo, hi)][0] = colors[2]
        g[rng.randint(lo, hi)][N - 1] = colors[3]
    # Corner legend decorations like the canonical demos — kept strictly
    # OUTSIDE the diamond's column span so their columns carry no 2-range
    # (rule-inert, exactly like the canonical legends); covers ~8 colors.
    deco = [c for c in range(1, 10) if c not in (0, 2)]
    rng.shuffle(deco)
    run = min(rng.randint(2, 4), max(1, center - r))
    for i in range(run):
        if g[0][i] == 0:
            g[0][i] = deco[i % len(deco)]
    run2 = min(rng.randint(2, 4), max(1, N - 1 - (center + r)))
    for i in range(run2):
        if g[N - 1][N - 1 - i] == 0:
            g[N - 1][N - 1 - i] = deco[(i + run) % len(deco)]
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(13, 13, 0)
    if name == "no_diamond":
        g[0][6] = 3
        return g
    if name == "no_rays":
        _draw_diamond(g, 6, 6, 4)
        return g
    if name == "full_grid":
        for r in range(13):
            for c in range(13):
                g[r][c] = 2
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    n = len(grid)
    errors = []
    if any(len(row) != n for row in grid) or n % 2 == 0:
        errors.append("grid should be odd square")
        return errors
    center = n // 2
    twos = {(r, c) for r in range(n) for c in range(n) if grid[r][c] == 2}
    if not twos:
        errors.append("missing color-2 diamond")
    else:
        dists = {abs(r - center) + abs(c - center) for r, c in twos}
        if len(dists) != 1:
            errors.append(f"color-2 cells should form one manhattan-radius outline, got radii {sorted(dists)}")
    border = []
    for c in range(n):
        if grid[0][c] not in (0, 2): border.append((0, c))
        if grid[n - 1][c] not in (0, 2): border.append((n - 1, c))
    for r in range(1, n - 1):
        if grid[r][0] not in (0, 2): border.append((r, 0))
        if grid[r][n - 1] not in (0, 2): border.append((r, n - 1))
    if len(border) < 2:
        errors.append("need at least two exterior ray source pixels")
    return sorted(set(errors))
