"""Generator for arc_additional_puzzles_21_set13_bundle:E89.

Rule: count cells by color; sort colors ascending; emit one cell per
occurrence in that order. Output is a 1×N row.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_colors,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, single_color_only, equal_counts.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "efa312ece14e"
VERSION = "2.0.1"  # add executable tally/count self_check.
TASK_ID = "efa312ece14e"
SUMMARY = (
    "0-bg grid with scattered single-cell markers in several distinct colors, "
    "each color appearing 1-3 times. Rule: tally non-bg cells, sort colors "
    "ascending, emit each color repeated by its count -> a 1xN row. Color set, "
    "per-color counts (so the tally varies), palette and grid size all vary. "
    "(Adjacency is irrelevant to the rule; cells just need distinct positions.)"
)

INVARIANTS = [
    "background is 0",
    ">=3 distinct non-bg colors",
    "1..3 cells per color at distinct positions",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "single_color_only", "equal_counts")
HELPFUL_TEXTURES = PALETTE_KINDS

_PALETTE_POOLS = {
    "default": [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "varied":  [1, 2, 3, 4, 5, 6, 7, 8, 9],
    "warm":    [2, 3, 4, 6, 9],
    "cool":    [1, 5, 7, 8],
}

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_colors":       {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..5"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "3..5"},
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
        h = ctx.draw_int("grid_h", 5, 7); w = ctx.draw_int("grid_w", 6, 8)
        nlo, nhi, cmax = 3, 3, 2
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 8, 12)
        nlo, nhi, cmax = 4, 5, 3
    else:
        h = ctx.draw_int("grid_h", 6, 9); w = ctx.draw_int("grid_w", 7, 10)
        nlo, nhi, cmax = 3, 4, 3
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_colors = max(3, min(9, int(overrides.get("n_colors", ctx.draw_int("n_colors", nlo, nhi)))))
    pk = (overrides.get("palette_kind")
          or ctx.draw_choice("palette_kind", list(PALETTE_KINDS)))
    pool = list(_PALETTE_POOLS.get(pk, _PALETTE_POOLS["default"]))
    if len(set(pool)) < n_colors:
        pool = list(_PALETTE_POOLS["default"])
    palette = rng.sample(pool, n_colors)
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    idx = 0
    for color in palette:
        cnt = rng.randint(1, cmax)
        for _ in range(cnt):
            if idx >= len(cells):
                break
            r, c = cells[idx]; idx += 1
            g[r][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Default instances: 0-bg scattered markers, 3-5 colors, 1-3 cells per color."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    counts = {}
    for row in grid:
        for v in row:
            if not isinstance(v, int) or not (0 <= v <= 9):
                errs.append(f"grid contains non-digit color {v!r}")
                continue
            if v != 0:
                counts[v] = counts.get(v, 0) + 1
    if not (3 <= len(counts) <= 5):
        errs.append(f"expected 3..5 distinct non-bg colors, got {len(counts)}")
    for color, cnt in sorted(counts.items()):
        if not (1 <= cnt <= 3):
            errs.append(f"color {color} should appear 1..3 times, got {cnt}")
    if not any(v == 0 for row in grid for v in row):
        errs.append("background color 0 is absent")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 6, 7
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no cells → tally is empty, output 1×0 row
        return g
    if name == "single_color_only":
        # only one color present → output is a uniform 1×N row
        for r, c in [(1, 2), (3, 4), (5, 1)]:
            g[r][c] = 6
        return g
    if name == "equal_counts":
        # every color has the same count → row is regular run pattern, no rank signal
        for r, c, v in [(0, 1, 3), (1, 4, 3),
                        (2, 1, 5), (3, 4, 5),
                        (4, 1, 7), (5, 4, 7)]:
            g[r][c] = v
        return g
    return g
