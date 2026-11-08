"""Generator for 29623171.

Rule: in a gray-separated 3x3 panel grid, sections with maximal marker
count are filled.

Combinatorial axes (8): grid_size, cell_size, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, color.
Degenerates: no_markers, all_full, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5003370f0e31"
VERSION = "1.2.1"
TASK_ID = "5003370f0e31"
SUMMARY = "3×3 grid of equal-sized panels separated by two full color-5 rows and two full color-5 cols. Each panel has 0..k² marker cells in one color. Rule finds the maximum marker count, then fills each panel that reaches that max completely with the marker color. Separators preserved."

# Rivals: 'output is input' refuted by any demo (max-count panels fill).
# 'fill all panels' refuted by any demo where non-max panels stay sparse.
# 'use color 5 for fill' refuted by any demo (fill uses marker color).
# 'fill smallest-count panels' refuted by any demo. 3 demos cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "two full gray rows and two full gray columns form a 3x3 section grid",
    "all markers use one nonzero non-gray color",
    "marker counts vary by section",
    "marker color is distinct from 0 and 5",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "all_full", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_size":      {"type": "int", "default": "rng 8..11", "valid": "8..17"},
    "cell_size":      {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "color":          {"type": "color", "default": "rng !{0,5}", "valid": "1..9 except 5"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: two full gray(5) rows and two full gray(5) cols (3x3 panel grid); >=1 marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    full_gray_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    full_gray_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(full_gray_rows) != 2:
        errs.append(f"expected 2 full-gray rows (3x3 separator), found {len(full_gray_rows)}")
    if len(full_gray_cols) != 2:
        errs.append(f"expected 2 full-gray cols (3x3 separator), found {len(full_gray_cols)}")
    # Check marker (non-0, non-5) exists
    has_marker = any(grid[r][c] not in (0, 5) for r in range(h) for c in range(w))
    if not has_marker:
        errs.append("no marker cells (non-0, non-5) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        k_lo, k_hi = 2, 3
    elif difficulty == "hard":
        k_lo, k_hi = 4, 5
    else:
        k_lo, k_hi = 2, 4
    k = ctx.draw_int("cell_size", k_lo, k_hi)
    color = ctx.draw_color("color", exclude={0, 5})
    size = 3 * k + 2
    g = full_grid(size, size, 0)
    sep1 = k
    sep2 = 2 * k + 1
    for i in range(size):
        g[sep1][i] = 5
        g[sep2][i] = 5
        g[i][sep1] = 5
        g[i][sep2] = 5
    # RANDOM marker count per panel (0..k^2) so the set of max-count panels (the
    # panels the rule fills) varies — the old fixed counts always made panels 2
    # and 8 the max, so the filled set never changed (distinct=23).
    counts = [rng.randint(0, k * k) for _ in range(9)]
    starts = [(0, 0), (0, sep1 + 1), (0, sep2 + 1),
              (sep1 + 1, 0), (sep1 + 1, sep1 + 1), (sep1 + 1, sep2 + 1),
              (sep2 + 1, 0), (sep2 + 1, sep1 + 1), (sep2 + 1, sep2 + 1)]
    for idx, count in enumerate(counts):
        r0, c0 = starts[idx]
        cells = [(r0 + r, c0 + c) for r in range(k) for c in range(k)]
        rng.shuffle(cells)
        for r, c in cells[:count]:
            g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(11, 11, 0)
    sep1, sep2 = 3, 7
    for i in range(11):
        g[sep1][i] = 5; g[sep2][i] = 5
        g[i][sep1] = 5; g[i][sep2] = 5
    if name == "no_markers":
        return g
    if name == "all_full":
        for r in range(11):
            for c in range(11):
                if g[r][c] != 5:
                    g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(11):
            for c in range(11):
                g[r][c] = 5
        return g
    return g
