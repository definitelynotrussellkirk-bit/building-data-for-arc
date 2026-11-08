"""Generator for arc_puzzle_bank_twentieth21:E139 — keep most-frequent color.

Rule: only the most-frequent non-zero color is kept; all other non-zeros
become 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: tied_majority, single_color, all_minority.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "832677479459"
VERSION = "1.2.0"
TASK_ID = "832677479459"
SUMMARY = "Several non-zero cells in 2-4 colors; one color is strictly most frequent. Rule keeps only that color; all other non-zeros become 0. Background stays."

# Rivals: 'output is input' refuted by any demo (minority colors are
# erased). 'keep one specific color (eg blue)' refuted by ≥2 demos
# with different majority colors. 'keep the rarest color' refuted by
# any demo (rule keeps majority). 'recolor majority to a fixed color'
# refuted by any demo (majority keeps own color). 3 demos with
# varied majority colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "2-3 non-zero colors used; one strictly outnumbers the others",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("tied_majority", "single_color", "all_minority")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..5", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 5..6", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "rng 2..3", "valid": "2..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_majority",
                       "valid": "scattered_majority"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "density":        {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6)
        w = ctx.draw_int("grid_w", 4, 6)
        n_major_lo, n_major_hi = 3, 5
        n_minor_lo, n_minor_hi = 1, 2
        n_colors_lo, n_colors_hi = 2, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 10, 16)
        n_major_lo, n_major_hi = 10, 18
        n_minor_lo, n_minor_hi = 2, 5
        n_colors_lo, n_colors_hi = 3, 4
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 10)
        n_major_lo, n_major_hi = 5, 9
        n_minor_lo, n_minor_hi = 1, 3
        n_colors_lo, n_colors_hi = 2, 3

    for outer in range(40):
        g = full_grid(h, w, 0)
        n_colors = rng.randint(n_colors_lo, n_colors_hi)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
        major = colors[0]
        n_major = rng.randint(n_major_lo, n_major_hi)
        n_minor = rng.randint(n_minor_lo, n_minor_hi)
        positions = []
        for _ in range(n_major):
            for _t in range(40):
                r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                if g[r][c] != 0: continue
                g[r][c] = major
                positions.append((r, c))
                break
        for color in colors[1:]:
            for _ in range(n_minor):
                for _t in range(40):
                    r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
                    if g[r][c] != 0: continue
                    g[r][c] = color
                    break
        from collections import Counter
        cnts = Counter(v for row in g for v in row if v != 0)
        if cnts[major] > max((c for k, c in cnts.items() if k != major), default=0):
            return g
    return g


def _draw_from_degenerate(name, rng):
    h, w = 5, 6
    g = full_grid(h, w, 0)
    if name == "tied_majority":
        # two colors tied for max → "most-frequent" is ambiguous
        for (r, c) in [(0, 0), (1, 1), (2, 2)]: g[r][c] = 4   # 3 cells
        for (r, c) in [(3, 0), (3, 2), (3, 4)]: g[r][c] = 6   # 3 cells, also max
        return g
    if name == "single_color":
        # only one color → trivially most-frequent, rule is identity
        for (r, c) in [(0, 0), (1, 2), (2, 4), (3, 1)]: g[r][c] = 4
        return g
    if name == "all_minority":
        # all colors equally rare (each has 1 cell) → no strict majority
        g[0][0] = 4; g[1][2] = 6; g[2][4] = 3; g[3][1] = 8
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    from collections import Counter
    counts = Counter(v for row in grid for v in row if v != 0)
    if not counts:
        errors.append("expected nonzero colors")
        return errors
    n = len(counts)
    lo, hi = (2, 2) if difficulty == "easy" else ((3, 4) if difficulty == "hard" else (2, 3))
    if not (lo <= n <= hi):
        errors.append(f"expected {lo}..{hi} nonzero colors, got {n}")
    ordered = counts.most_common()
    if len(ordered) < 2 or ordered[0][1] <= ordered[1][1]:
        errors.append(f"expected a strict majority color, got counts {dict(counts)}")
    return errors
