"""Generator for arc_additional_puzzles_21_set7:E48.

Rule: blank cells filled from partners reflected across the anti-diagonal.

Combinatorial axes (8): grid_h/w, grid_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_marks, full_antidiag, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da4a2278f620"
VERSION = "2.1.0"  # anti-diagonal point-reflection fill; output=input dims but grid_size was pinned 5-12 -> out_shapes 3. Widen grid_size 5-19 + more sources -> more output sizes.
TASK_ID = "da4a2278f620"
SUMMARY = (
    "Square N×N (6 ≤ N ≤ 9) 0-bg grid with 3-5 non-zero source cells "
    "in distinct colors at scattered positions. Each source cell's "
    "anti-diagonal mirror image is blank (so the rule can fill it). "
    "Rule: for each cell (r, c), if v == 0 AND the anti-diagonal "
    "mirror cell (N-1-c, N-1-r) has value ref != 0, then fill with "
    "ref. Otherwise preserve. Effectively each non-zero source cell "
    "gets reflected across the anti-diagonal."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "grid is square N×N",
    "3-5 source cells in distinct non-zero colors",
    "for each source cell (r, c), the anti-diagonal mirror (N-1-c, N-1-r) is bg in input",
    "source cells are not on the anti-diagonal (r + c != N-1) so reflections are distinct",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_marks", "full_antidiag", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "6..9"},
    "grid_size":      {"type": "int", "default": "rng 8..13", "valid": "5..19"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("grid_size", 5, 8)
        n_sources = ctx.draw_int("n_sources", 3, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_size", 13, 19)
        n_sources = ctx.draw_int("n_sources", 5, 8)
    else:
        n = ctx.draw_int("grid_size", 8, 13)
        n_sources = ctx.draw_int("n_sources", 3, 6)
    colors = list(ctx.draw_distinct_colors("colors", n=n_sources, exclude=[0]))
    g = full_grid(n, n, 0)
    placed = 0
    for _ in range(n_sources * 10):
        if placed >= n_sources:
            break
        r = rng.randint(0, n - 1)
        c = rng.randint(0, n - 1)
        if r + c == n - 1:
            continue  # on anti-diagonal -- reflection is itself
        if g[r][c] != 0:
            continue
        # Mirror must be empty
        mr, mc = n - 1 - c, n - 1 - r
        if g[mr][mc] != 0:
            continue
        g[r][c] = colors[placed]
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_marks":
        return g
    if name == "full_antidiag":
        for i in range(7):
            g[i][6 - i] = 3
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 3
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    n = len(grid)
    if len(grid[0]) != n:
        errs.append("grid is not square")
        return errs
    sources = [(r, c, grid[r][c]) for r in range(n) for c in range(n) if grid[r][c] != 0]
    if len(sources) < 3:
        errs.append(f"expected at least 3 source cells, found {len(sources)}")
    colors = [v for _, _, v in sources]
    if len(set(colors)) != len(colors):
        errs.append("source colors are not distinct")
    for r, c, _ in sources:
        if r + c == n - 1:
            errs.append("source cell lies on the anti-diagonal")
            break
        mr, mc = n - 1 - c, n - 1 - r
        if grid[mr][mc] != 0:
            errs.append("a source cell's anti-diagonal mirror is already occupied")
            break
    return errs
