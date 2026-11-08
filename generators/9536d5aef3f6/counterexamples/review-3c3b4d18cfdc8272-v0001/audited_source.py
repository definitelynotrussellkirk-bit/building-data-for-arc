"""Generator for easy_77_mirror_across_main_diagonal.

Rule: cells above the main diagonal are mirrored to their transposed
positions below the diagonal.

Combinatorial axes (8): grid_size, palette_kind, num_markers,
palette_size, position_bias, n_distinct_colors, marker_density, texture.
Degenerates: already_symmetric, on_diagonal, no_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9536d5aef3f6"
VERSION = "1.1.1"  # add self_check
TASK_ID = "9536d5aef3f6"
SUMMARY = "Place colored cells above the main diagonal of a square grid to mirror below."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "source cells are above the main diagonal",
    "no source cell already has its mirrored counterpart",
]

PALETTE_KINDS = ("default", "sparse", "dense", "rainbow")
DEGENERATE_TEXTURES = ("already_symmetric", "on_diagonal", "no_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "size":           {"type": "int", "default": "rng 6..9", "valid": "3..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "markers":        {"type": "int", "default": "rng 3..6", "valid": "1..20"},
    "marker_density": {"type": "str", "default": "medium",
                       "valid": "sparse|medium|dense"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "above_diagonal",
                       "valid": "above_diagonal"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6",
                          "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: square grid; ≥1 non-zero cell strictly above main diagonal (r < c); below diagonal is all 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    errs = []
    if h != w:
        errs.append(f"expected square grid; got {h}×{w}")
    else:
        above = sum(1 for r in range(h) for c in range(r + 1, w) if grid[r][c] != 0)
        below = sum(1 for r in range(h) for c in range(0, r) if grid[r][c] != 0)
        if above < 1:
            errs.append("no source cells above main diagonal (r < c)")
        if below > 0:
            errs.append(f"{below} non-zero cells below main diagonal — should be 0 in input")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("size", 6, 7)
        target_max = 4
    elif difficulty == "hard":
        n = ctx.draw_int("size", 8, 9)
        target_max = 6
    else:
        n = ctx.draw_int("size", 6, 9)
        target_max = 6
    target = min(ctx.draw_int("markers", 3, target_max), n * (n - 1) // 2)
    rng = ctx.draw_rng("layout")
    g = full_grid(n, n, 0)
    positions = [(r, c) for r in range(n) for c in range(r + 1, n)]
    for r, c in rng.sample(positions, target):
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    n = 7
    g = full_grid(n, n, 0)
    if name == "already_symmetric":
        # input already mirrored — rule output identical to input
        for r, c in [(0, 2), (1, 4), (3, 5)]:
            g[r][c] = 5
            g[c][r] = 5
        return g
    if name == "on_diagonal":
        # markers ON main diagonal — mirror to themselves
        for i in [1, 3, 5]:
            g[i][i] = 4
        return g
    if name == "no_markers":
        return g
    return g
