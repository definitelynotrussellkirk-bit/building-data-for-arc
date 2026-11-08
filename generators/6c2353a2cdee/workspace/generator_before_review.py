"""Generator for 14b:hard_98 — overlay transformed templates to count map.

Rule: 3 5x5 panels at rows 0-4 cols [0..4, 6..10, 12..16] + a code
row at row 6 with per-panel transform codes at the same column blocks.
Output is a per-cell overlap count of the 3 transformed panels,
colored 2/4/8 by count.

Multi-panel family: requires both panel offsets AND code-row offsets
to match exactly.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_panel_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_panels, no_codes, full_panels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c2353a2cdee"
VERSION = "1.2.1"
TASK_ID = "6c2353a2cdee"

SUMMARY = "3 5x5 panels at top + code row at row 6 with 3 transform codes; output 5x5 overlap-count colored 2/4/8."

# Bbox is fixed by the rule (7×17 input, 5×5 output) — diversity lives
# entirely in (a) which cells are set in each panel, (b) which 1..5
# code per panel, (c) colors.
#
# Rivals: 'overlap counts use a different color scheme' refuted by
# ≥2 demos with varied output (always 2/4/8). 'ignore code row'
# refuted by ≥2 demos where same panels with different codes produce
# different outputs. 'output panel union (no transform)' refuted by
# ≥1 demo where transformations are observable.
# 4 demos with varied panel cell patterns + codes cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "grid is 7 rows tall and 17 cols wide",
    "3 panels at rows 0..4 cols [0..4], [6..10], [12..16]; each 4-7 cells",
    "code row at row 6 has exactly one non-bg cell in each col-block [0..4], [6..10], [12..16]",
    "code values are in {1, 2, 3, 4, 5}",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_panels", "no_codes", "full_panels")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7", "valid": "7..7"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_panel_cells":  {"type": "int", "default": "rng 4..7", "valid": "4..7"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "fixed_3panel_with_codes",
                       "valid": "fixed_3panel_with_codes"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is 7x17; code row 6 has >=1 nonzero cell in each of the 3 panel col blocks."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h != 7 or w != 17:
        errs.append(f"expected 7x17 grid; got {h}x{w}")
        return errs
    # Check code row has at least one nonzero cell per block
    blocks = [(0, 4), (6, 10), (12, 16)]
    for (c0, c1) in blocks:
        has_code = any(grid[6][c] != 0 for c in range(c0, c1 + 1))
        if not has_code:
            errs.append(f"code row (row 6) has no nonzero cell in cols {c0}-{c1}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    h = 7; w = 17
    g = full_grid(h, w, 0)
    panel_starts = [0, 6, 12]
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], 3)
    if difficulty == "easy":
        n_lo, n_hi = 3, 5
    elif difficulty == "hard":
        n_lo, n_hi = 7, 12
    else:
        n_lo, n_hi = 5, 9
    for c0, color in zip(panel_starts, palette):
        cells = [(r, c0 + dc) for r in range(5) for dc in range(5)]
        n = min(rng.randint(n_lo, n_hi), 25)
        for r, c in rng.sample(cells, n):
            g[r][c] = color
    # code row at row 6: one distinct code per panel (rule dispatches
    # differently per panel). Sampled without replacement so all 3
    # codes differ — ensures rotation/reflection variety is observable.
    codes = rng.sample([1, 2, 3, 4, 5], 3)
    for c0, code in zip(panel_starts, codes):
        slot = rng.randint(c0, c0 + 4)
        g[6][slot] = code
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 17
    g = full_grid(h, w, 0)
    panel_starts = [0, 6, 12]
    if name == "empty_panels":
        # no panel cells → no templates to overlay, output blank
        for c0 in panel_starts:
            g[6][c0 + 2] = 1
        return g
    if name == "no_codes":
        # panels but no code row → no transform dispatch, undefined
        for c0, color in zip(panel_starts, [4, 6, 8]):
            for r, c in [(0, c0), (1, c0), (1, c0 + 1)]:
                g[r][c] = color
        return g
    if name == "full_panels":
        # all 25 cells filled → max overlap regardless of transforms
        for c0, color in zip(panel_starts, [4, 6, 8]):
            for r in range(5):
                for dc in range(5):
                    g[r][c0 + dc] = color
        for c0 in panel_starts:
            g[6][c0 + 2] = 1
        return g
    return g
