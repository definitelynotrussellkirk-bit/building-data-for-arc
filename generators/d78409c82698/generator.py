"""Generator for arc_additional_puzzle_bank_volume2:E8.

Rule: red cells with no cardinal red neighbor are recolored green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_singletons,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_singletons, all_singletons, no_components.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d78409c82698"
VERSION = "2.0.3"
RULE_HASH = "f38a8db401a2"
TASK_ID = "d78409c82698"
SUMMARY = (
    "0-bg grid (h~8-13, w~8-13) with: (a) 2-5 "
    "COLOR-2 (red) SINGLETON CELLS placed at "
    "positions with no cardinal red neighbor "
    "(diagonal-neighbor pairs are allowed and "
    "used to pin CARDINAL, not diagonal, "
    "connectivity); (b) ONE FIXED MULTI-CELL "
    "COLOR-2 CLUSTER at bottom-left (a "
    "3-cell L-shape at (h-3, 0), (h-2, 0), "
    "(h-2, 1)) — a non-singleton red blob that "
    "should NOT be recolored. Rule: for EVERY "
    "COLOR-2 (red) CELL, check its 4 cardinal "
    "neighbors. If ALL 4 cardinal neighbors are "
    "NON-RED (any non-2 value), RECOLOR that "
    "cell to COLOR 3 (green). If ≥1 cardinal "
    "neighbor IS red (part of a multi-cell "
    "component), KEEP it as 2. Net: cardinally "
    "isolated red singletons become green; "
    "multi-cell red blobs stay red."
)

# Rivals: 'output is input' refuted by demos with ≥1 isolated 2.
# 'recolor all 2s' refuted by demos with multi-cell components
# staying 2. 'use color 4 instead of 3' refuted by demos. 'include
# diagonal neighbors in connectivity check' refuted by demos with
# diagonally-adjacent 2s that still get recolored. 3 demos with mix
# of singletons and multi-cell components cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "target red cells are cardinally isolated singletons",
    "larger red components are present as non-target distractors",
    "red singletons are separated from all red components",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_singletons", "all_singletons", "no_components")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_singletons":   {"type": "int", "default": "rng 2..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2",
                       "probe": "diagnostic"},
    "position_bias":  {"type": "str", "default": "singletons_plus_component",
                       "valid": "singletons_plus_component", "probe": "diagnostic"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2",
                          "probe": "diagnostic"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse",
                       "probe": "diagnostic"},
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        n_singletons = ctx.draw_int("n_singletons", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 20)
        w = ctx.draw_int("grid_w", 14, 20)
        n_singletons = ctx.draw_int("n_singletons", 6, 12)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 10, 14)
        n_singletons = ctx.draw_int("n_singletons", 3, 6)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    # Fixed non-singleton component.  Place it first so singleton selection can
    # test cardinal isolation against the distractor component too.
    g[h - 2][0] = 2
    g[h - 2][1] = 2
    g[h - 3][0] = 2

    def cardinal_clear(r, c):
        if g[r][c] != 0:
            return False
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w and g[rr][cc] == 2:
                return False
        return True

    # Force a diagonal pair when possible; the old Chebyshev spacing blocked
    # this important anti-rival branch and, on small easy boards, under-placed
    # the promised singleton count.
    candidates = [(r, c) for r in range(h) for c in range(w) if cardinal_clear(r, c)]
    diag_pairs = []
    cset = set(candidates)
    for r, c in candidates:
        for rr, cc in ((r + 1, c + 1), (r + 1, c - 1)):
            if (rr, cc) in cset:
                diag_pairs.append(((r, c), (rr, cc)))
    rng.shuffle(diag_pairs)
    placed: list[tuple[int, int]] = []
    if n_singletons >= 2 and diag_pairs:
        for r, c in diag_pairs[0]:
            g[r][c] = 2
            placed.append((r, c))

    for _try in range(500):
        if len(placed) >= n_singletons:
            break
        candidates = [(r, c) for r in range(h) for c in range(w) if cardinal_clear(r, c)]
        if not candidates:
            break
        r, c = rng.choice(candidates)
        g[r][c] = 2
        placed.append((r, c))
    if len(placed) != n_singletons:
        raise ValueError("could not place requested cardinally isolated singletons")
    return g


def _red_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 2 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] == 2 and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            comps.append(comp)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify isolated red singletons plus a non-singleton red distractor."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    comps = _red_components(grid)
    singleton_count = sum(1 for comp in comps if len(comp) == 1)
    multi_count = sum(1 for comp in comps if len(comp) > 1)
    min_singletons = 6 if difficulty == "hard" else (2 if difficulty == "easy" else 3)
    errs = []
    if singleton_count < min_singletons:
        errs.append(f"expected at least {min_singletons} cardinally isolated red singletons, found {singleton_count}")
    if multi_count < 1:
        errs.append("missing multi-cell red component that should remain color 2")
    # Diagonal-neighbor singleton pairs are a generated-distribution teaching
    # requirement, not a validity condition of the canonical rule.  Original
    # ARC examples without such a pair remain lawful and must pass self_check;
    # focused generator tests pin the stronger distribution property.
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 10
    g = full_grid(h, w, 0)
    if name == "no_singletons":
        # only multi-cell red component → rule fires zero times, output identical
        g[1][1] = 2; g[1][2] = 2; g[2][1] = 2
        return g
    if name == "all_singletons":
        # all red cells are isolated singletons → all recolored green
        g[1][2] = 2; g[3][5] = 2; g[5][7] = 2; g[7][1] = 2
        return g
    if name == "no_components":
        # blank → no red cells, rule has no effect
        return g
    return g


def observe_overrides(grid):
    """Recover exact grid dimensions and the requested singleton count."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    singleton_count = sum(1 for component in _red_components(grid) if len(component) == 1)
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_singletons": singleton_count}
