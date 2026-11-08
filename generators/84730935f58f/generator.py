"""Generator for ARC task 84730935f58f (corner selector chooses plus or X).

The cell at ``(0, 0)`` is a selector, not a seed.  Selector ``1`` chooses
cardinal plus growth; selectors ``2..7`` choose diagonal-X growth.  Every
other nonzero cell is a seed and the canonical rule paints the union of the
selected five-cell stencils cyan on a fresh zero grid.

The ordinary generator deliberately alternates selector modes by sample index,
so every consecutive four-example lesson contains both branches.  Layout and
colour decisions remain keyed and deterministic.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "84730935f58f"
VERSION = "2.1.0"
TASK_ID = GENERATOR_ID
SUMMARY = (
    "A zero-background grid has a selector in the top-left corner and at least "
    "two coloured seeds elsewhere. Selector 1 chooses the five-cell plus "
    "stencil; selectors 2..7 choose the five-cell diagonal X. The output is a "
    "fresh zero grid containing the in-bounds union of those stencils in cyan "
    "(8); the selector itself is not copied to the output."
)

EXAMPLES_NEEDED = 4

INVARIANTS = [
    "cell (0,0) is the stencil selector",
    "selector 1 means plus growth; selectors 2..7 mean X growth",
    "remaining nonzero cells are seeds and input never contains output colour 8",
    "the three-cell halo touching the selector is empty",
]

PALETTE_KINDS = ("default", "many_seeds", "spread_seeds", "tight_seeds")
DEGENERATE_TEXTURES = ("no_selector", "no_seeds", "ambiguous_selector")
HELPFUL_TEXTURES = PALETTE_KINDS
SEED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
SELECTOR_HALO = {(0, 1), (1, 0), (1, 1)}
PLUS_OFFSETS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
X_OFFSETS = ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))

AXES = {
    "height": {"type": "int", "default": "difficulty-aware", "valid": "5..14"},
    "width": {"type": "int", "default": "difficulty-aware", "valid": "5..14"},
    "palette_kind": {"type": "str", "default": "keyed helpful profile",
                     "valid": "|".join(PALETTE_KINDS)},
    "mode": {"type": "choice", "default": "alternates by sample_index",
             "valid": "plus|x"},
    "num_seeds": {"type": "int", "default": "difficulty-aware", "valid": "2..8"},
    "n_distinct_colors": {"type": "int", "default": "difficulty-aware",
                          "valid": "1..min(6,num_seeds)"},
    "texture": {"type": "str", "default": "optional alias/negative fixture",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_ALLOWED_OVERRIDES = set(AXES)


def _validate_grid(grid) -> list[str]:
    if type(grid) is not list or not grid:
        return ["empty or non-list grid"]
    if type(grid[0]) is not list or not grid[0]:
        return ["empty first row"]
    width = len(grid[0])
    errors = []
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        errors.append("grid dimensions must be in 3..30")
    if any(type(row) is not list or len(row) != width for row in grid):
        errors.append("ragged grid")
        return errors
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        errors.append("cells must be exact integer ARC colours 0..9")
    return errors


def seed_cells(grid) -> list[tuple[int, int]]:
    """Return seed coordinates in row-major order, excluding the selector."""
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if (r, c) != (0, 0) and value != 0
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed selectors, unsafe halo cells, and weak seed scenes."""
    errors = _validate_grid(grid)
    if errors:
        return errors
    selector = grid[0][0]
    if selector not in range(1, 8):
        errors.append("selector at (0,0) must be an exact colour in 1..7")
    for r, c in SELECTOR_HALO:
        if r < len(grid) and c < len(grid[0]) and grid[r][c] != 0:
            errors.append(f"selector halo cell {(r, c)} must be zero")
    seeds = seed_cells(grid)
    if len(seeds) < 2:
        errors.append(f"expected at least 2 seeds; found {len(seeds)}")
    for r, c in seeds:
        if grid[r][c] not in SEED_COLORS:
            errors.append(f"seed {(r, c)} uses forbidden colour {grid[r][c]}")
    return errors


def _strict_int_override(overrides: dict, label: str) -> None:
    value = overrides.get(label)
    if value is not None and type(value) is not int:
        raise TypeError(f"{label} override must be an integer (not bool)")


def _mode(overrides: dict, sample_index: int) -> str:
    value = overrides.get("mode")
    if value is None:
        return "plus" if sample_index % 2 == 0 else "x"
    if type(value) is not str or value not in ("plus", "x"):
        raise ValueError("mode must be 'plus' or 'x'")
    return value


def _normalise_palette_kind(overrides: dict, ctx) -> str:
    texture = overrides.get("texture")
    palette = overrides.get("palette_kind")
    if texture is not None and type(texture) is not str:
        raise TypeError("texture must be a string")
    if palette is not None and type(palette) is not str:
        raise TypeError("palette_kind must be a string")
    if texture in HELPFUL_TEXTURES:
        if palette is not None and palette != texture:
            raise ValueError("texture and palette_kind conflict")
        return texture
    if texture is not None and texture not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown texture {texture!r}")
    if palette is not None:
        if palette not in PALETTE_KINDS:
            raise ValueError(f"unknown palette_kind {palette!r}")
        return palette
    return ctx.draw_choice("palette_kind", PALETTE_KINDS)


def _safe_cells(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) != (0, 0) and (r, c) not in SELECTOR_HALO
    ]


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _spread_positions(cells: list[tuple[int, int]], count: int, rng) -> list[tuple[int, int]]:
    pool = cells[:]
    rng.shuffle(pool)
    chosen = [pool.pop()]
    while len(chosen) < count:
        best_distance = max(min(_manhattan(cell, old) for old in chosen) for cell in pool)
        best = [cell for cell in pool if min(_manhattan(cell, old) for old in chosen) == best_distance]
        cell = rng.choice(best)
        pool.remove(cell)
        chosen.append(cell)
    return chosen


def _tight_positions(cells: list[tuple[int, int]], count: int, rng) -> list[tuple[int, int]]:
    anchor = rng.choice(cells)
    jitter = {cell: rng.random() for cell in cells}
    ranked = sorted(cells, key=lambda cell: (_manhattan(cell, anchor), jitter[cell], cell))
    return ranked[:count]


def _positions(cells: list[tuple[int, int]], count: int, kind: str, rng) -> list[tuple[int, int]]:
    if kind == "spread_seeds":
        return _spread_positions(cells, count, rng)
    if kind == "tight_seeds":
        return _tight_positions(cells, count, rng)
    return rng.sample(cells, count)


def _seed_colours(count: int, distinct: int, rng) -> list[int]:
    palette = rng.sample(list(SEED_COLORS), distinct)
    colours = [palette[index % distinct] for index in range(count)]
    rng.shuffle(colours)
    return colours


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard") and not isinstance(difficulty, (int, float)):
        raise ValueError("difficulty must be None, easy, medium, hard, or numeric")
    for label in ("height", "width", "num_seeds", "n_distinct_colors"):
        _strict_int_override(overrides, label)

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        height = ctx.draw_int_diff("height", 5, 14)
        width = ctx.draw_int_diff("width", 5, 14)
        return _draw_from_degenerate(texture, height, width)

    height = ctx.draw_int_diff("height", 5, 14)
    width = ctx.draw_int_diff("width", 5, 14)
    kind = _normalise_palette_kind(overrides, ctx)
    mode = _mode(overrides, sample_index)
    cells = _safe_cells(height, width)
    max_seeds = min(8, len(cells))
    num_seeds = ctx.draw_int_diff("num_seeds", 2, max_seeds)
    if overrides.get("num_seeds") is None and kind == "many_seeds":
        num_seeds = max(min(5, max_seeds), num_seeds)
    max_distinct = min(6, num_seeds, len(SEED_COLORS))
    n_distinct = ctx.draw_int_diff("n_distinct_colors", 1, max_distinct)
    if n_distinct > num_seeds:
        raise ValueError("n_distinct_colors cannot exceed num_seeds")

    grid = full_grid(height, width, 0)
    if mode == "plus":
        grid[0][0] = 1
    else:
        grid[0][0] = ctx.draw_rng("selector_color").choice([2, 3, 4, 5, 6, 7])
    chosen = _positions(cells, num_seeds, kind, ctx.draw_rng("seed_positions"))
    colours = _seed_colours(num_seeds, n_distinct, ctx.draw_rng("seed_colors"))
    for (r, c), colour in zip(chosen, colours):
        grid[r][c] = colour
    return grid


def _draw_from_degenerate(name: str, height: int, width: int):
    grid = full_grid(height, width, 0)
    if name == "no_selector":
        grid[min(2, height - 1)][min(3, width - 1)] = 5
        grid[min(4, height - 1)][min(2, width - 1)] = 6
    elif name == "no_seeds":
        grid[0][0] = 1
    elif name == "ambiguous_selector":
        grid[0][0] = 1
        grid[0][1] = 2
        grid[min(3, height - 1)][min(3, width - 1)] = 5
    return grid


def profile_signature(grid) -> dict:
    errors = _validate_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    selector = grid[0][0]
    seeds = seed_cells(grid)
    distances = [_manhattan(a, b) for a, b in combinations(seeds, 2)]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "selector": selector,
        "mode": "plus" if selector == 1 else "x",
        "num_seeds": len(seeds),
        "n_distinct_colors": len({grid[r][c] for r, c in seeds}),
        "minimum_seed_distance": min(distances) if distances else 0,
        "seed_cells": [list(cell) for cell in seeds],
    }


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the exact canonical Racket semantics."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid canonical input: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    offsets = PLUS_OFFSETS if grid[0][0] == 1 else X_OFFSETS
    output = full_grid(height, width, 0)
    for r, c in seed_cells(grid):
        for dr, dc in offsets:
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width:
                output[rr][cc] = 8
    return output
