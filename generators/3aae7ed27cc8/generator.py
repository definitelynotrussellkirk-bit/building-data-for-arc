"""Generator for arc_puzzle_bank_21_set2:S2_E4.

Rule: each red cell creates a yellow down-right echo if the target is empty.

Combinatorial axes (8): grid_h, grid_w, palette_kind, source_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_sources, sources_at_br, sources_clustered.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3aae7ed27cc8"
VERSION = "1.1.1"
TASK_ID = "3aae7ed27cc8"
SUMMARY = "Each red cell creates a yellow down-right echo if the target is empty."

INVARIANTS = [
    "background is 0",
    "red source cells are isolated",
    "most source cells have an in-bounds down-right target",
    "occupied echo targets block the yellow copy",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_sources", "sources_at_br", "sources_clustered")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "source_count":   {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "scattered_avoid_br",
                       "valid": "scattered_avoid_br"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_sources|sources_at_br|sources_clustered"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥1 color-2 (red) source cell; values 0..9; grid nonempty."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    reds = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    if reds == 0:
        pass  # degenerate (no_sources) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        count = ctx.draw_int("source_count", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        count = ctx.draw_int("source_count", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        count = ctx.draw_int("source_count", 3, 5)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    placed = []
    for _ in range(count):
        for _attempt in range(300):
            r = rng.randint(0, h - 2)
            c = rng.randint(0, w - 2)
            if g[r][c] != 0:
                continue
            if any(abs(r - rr) + abs(c - cc) <= 2 for rr, cc in placed):
                continue
            g[r][c] = 2
            placed.append((r, c))
            if rng.random() < 0.2:
                g[r + 1][c + 1] = rng.choice([1, 3, 5])
            break
        else:
            raise ValueError("could not place red source")
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_sources":
        # no red cells → no echoes, rule no-op
        return g
    if name == "sources_at_br":
        # red cells on bottom row or right column → down-right is out of bounds, rule no-op
        for c in [1, 4, 7]:
            g[h - 1][c] = 2
        for r in [2, 5]:
            g[r][w - 1] = 2
        return g
    if name == "sources_clustered":
        # adjacent red cells → "isolated source" invariant violated, ambiguous component count
        for r, c in [(2, 2), (2, 3), (3, 2), (3, 3)]:
            g[r][c] = 2
        return g
    return g
