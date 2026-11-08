"""Generator for arc_puzzle_bank_21_set13_bundle:easy_m06.

Rule: singleton seeds expand into hollow pluses: center erased, four
orthogonal neighbors painted with the seed color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_seeds, seeds_at_edge, seeds_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33a736924c92"
VERSION = "1.2.0"  # +self_check
TASK_ID = "33a736924c92"
SUMMARY = "Interior singleton seeds separated enough for hollow plus expansion."

INVARIANTS = [
    "background is 0",
    "all nonzero cells are isolated singleton seeds",
    "seeds are interior cells",
    "expanded pluses do not overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "seeds_at_edge", "seeds_overlap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "interior_singletons",
                       "valid": "interior_singletons"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 seed present, all nonzero cells are isolated (no 4-neighbor)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    h, w = len(grid), len(grid[0])
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        errs.append("no seed cells found")
        return errs
    nz_set = set(nonzero)
    for r, c in nonzero:
        neighbors = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
        if any(nb in nz_set for nb in neighbors):
            errs.append(f"seed at ({r},{c}) has a nonzero 4-neighbor (not isolated)")
            break  # report once
    return errs


def _plus_cells(r, c):
    return {(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        seed_count = ctx.draw_int("seed_count", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        seed_count = ctx.draw_int("seed_count", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        seed_count = ctx.draw_int("seed_count", 2, 4)
    colors = ctx.draw_distinct_colors("colors", n=seed_count, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    occupied_plus = set()
    for color in colors:
        for _ in range(300):
            r = rng.randint(1, h - 2)
            c = rng.randint(1, w - 2)
            plus = _plus_cells(r, c)
            if g[r][c] == 0 and (r, c) not in occupied_plus and not (plus & occupied_plus):
                g[r][c] = color
                occupied_plus |= plus | {(r, c)}
                break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # blank grid → no plus expansion, rule is identity
        return g
    if name == "seeds_at_edge":
        # seeds on the outer border → plus arms extend out of bounds, partial plus painted
        g[0][3] = 4
        g[h - 1][5] = 6
        g[3][0] = 3
        return g
    if name == "seeds_overlap":
        # seeds within 2 cells → plus expansions overlap, conflicting paints
        g[3][3] = 4; g[3][5] = 6   # adjacent seeds, plus arms collide at (3,4)
        g[6][2] = 3; g[6][4] = 8
        return g
    return g
