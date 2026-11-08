"""Generator for arc_puzzle_bank_eleventh21:E72.

Rule: in each row with two same-color endpoints, fill the horizontal
interval between them with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, n_spans, palette_size,
position_bias, n_distinct_colors, gap_density, texture.
Degenerates: no_gap, single_endpoint, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "62b2533ef10f"
VERSION = "1.1.1"
TASK_ID = "62b2533ef10f"
SUMMARY = "Fill horizontal intervals between matching row endpoints."

INVARIANTS = [
    "background is 0",
    "active rows contain exactly two matching endpoints",
    "only zeros lie between the endpoints",
    "colors are unique across generated spans",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_gap", "single_endpoint", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "5..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "spans":          {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "gap_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 9, 11)
    n = min(ctx.draw_int("spans", 3, 5), h, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), n)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
    for r, color in zip(rows, colors):
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = color
        g[r][c2] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 row with exactly 2 same-color endpoints with zero cells between."""
    if not grid or not grid[0]:
        return ["grid is empty"]
    h, w = len(grid), len(grid[0])
    errors = []
    found_span = False
    for r in range(h):
        nonzero = [(c, grid[r][c]) for c in range(w) if grid[r][c] != 0]
        if len(nonzero) == 2:
            (c1, v1), (c2, v2) = nonzero
            if v1 == v2 and c2 > c1 + 1:
                # check zeros between
                if all(grid[r][c] == 0 for c in range(c1+1, c2)):
                    found_span = True
                    break
    if not found_span:
        errors.append("no row with two matching same-color endpoints and zeros between found")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_gap":
        # touching endpoints — interval has zero interior
        g[2][3] = 4
        g[2][4] = 4
        return g
    if name == "single_endpoint":
        # only one cell — no second endpoint
        g[3][5] = 6
        return g
    if name == "no_seeds":
        # empty grid — no spans to fill
        return g
    return g
