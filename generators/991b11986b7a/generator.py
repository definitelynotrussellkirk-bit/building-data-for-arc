"""Generator for a644e277.

Rule: first two broken near-full separator rows and columns bound the
cropped subgrid.

Combinatorial axes (8): height, width, sep_position_r, sep_position_c,
palette_kind, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_separator, full_separator, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "991b11986b7a"
VERSION = "1.1.1"
TASK_ID = "991b11986b7a"
SUMMARY = "First two broken near-full separator rows/cols bound the cropped subgrid."

INVARIANTS = [
    "one separator color forms exactly two broken near-full rows and two broken near-full columns",
    "separator rows are missing the two separator-column intersections",
    "separator columns are missing the two separator-row intersections",
    "non-separator cells use a checker of other colors",
]

POSITION_BIASES = ("centered", "wide_spread", "tight", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_separator", "full_separator", "full_grid")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {'height': {'type': 'int', 'default': 'rng 10..12', 'valid': '6..30'},
 'width': {'type': 'int', 'default': 'rng 10..12', 'valid': '6..30'},
 'sep_position_r': {'type': 'str',
                    'default': 'rng helpful',
                    'valid': 'centered|wide_spread|tight|rng'},
 'sep_position_c': {'type': 'str',
                    'default': 'rng helpful',
                    'valid': 'centered|wide_spread|tight|rng'},
 'palette_kind': {'type': 'str', 'default': 'rng', 'valid': 'warm|cool|broad|primary'},
 'anchor_corner': {'type': 'bool', 'default': 'false', 'valid': 'true|false'},
 'asymmetry_force': {'type': 'bool', 'default': 'false', 'valid': 'true|false'},
 'palette_size': {'type': 'int', 'default': '3', 'valid': '3'},
 'texture': {'type': 'str',
             'default': 'alias for sep_position_r',
             'valid': 'centered|wide_spread|tight|rng|no_separator|full_separator|full_grid'}}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least 2 distinct non-bg colors present (checker + separator)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    colors = {v for row in grid for v in row if v != 0}
    if len(colors) < 2:
        return [f"expected >=2 distinct non-bg colors (separator + checker); found {len(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 6, 9, 6, 9
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 13, 18, 13, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 10, 12, 10, 12
    h = ctx.draw_int("height", h_lo, h_hi)
    w = ctx.draw_int("width", w_lo, w_hi)
    sep, a, b = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    g = full_grid(h, w, a)
    for r in range(h):
        for c in range(w):
            g[r][c] = a if (r + c + sample_index) % 2 == 0 else b
    bias_r = (overrides.get("texture") or
              overrides.get("sep_position_r")
              or ctx.draw_choice("sep_position_r", list(POSITION_BIASES)))
    bias_c = overrides.get("sep_position_c",
                           ctx.draw_choice("sep_position_c",
                                           list(POSITION_BIASES)))
    r1, r2 = _pick_sep(bias_r, h, rng)
    c1, c2 = _pick_sep(bias_c, w, rng)
    for c in range(w):
        if c not in (c1, c2):
            g[r1][c] = sep
            g[r2][c] = sep
    for r in range(h):
        if r not in (r1, r2):
            g[r][c1] = sep
            g[r][c2] = sep
    return g


def _pick_sep(bias, n, rng):
    if bias == "centered":
        i1 = max(2, n // 3)
        i2 = max(i1 + 2, 2 * n // 3)
    elif bias == "wide_spread":
        i1 = 1
        i2 = n - 2
    elif bias == "tight":
        i1 = max(1, n // 2 - 1)
        i2 = i1 + 2
    else:
        i1 = rng.randint(1, max(1, n // 3))
        i2 = rng.randint(min(n - 2, max(i1 + 2, 2 * n // 3)), n - 2)
    i1 = max(1, min(i1, n - 4))
    i2 = max(i1 + 2, min(i2, n - 2))
    return i1, i2


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    if name == "no_separator":
        g = full_grid(h, w, 0)
        for r in range(h):
            for c in range(w):
                g[r][c] = 1 if (r + c) % 2 == 0 else 2
        return g
    if name == "full_separator":
        g = full_grid(h, w, 5)
        return g
    if name == "full_grid":
        return full_grid(h, w, 5)
    return full_grid(h, w, 0)
