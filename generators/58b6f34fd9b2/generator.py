"""Generator for ARC task 6a11f6da.

Rule: input is 15 × w (3 stacked 5-row panels). Output is 5 × w:
priority-OR with 6 > 1 > 8 > 0.

Combinatorial axes (8): grid_w, panel_colors (which of {0, 1, 6, 8}),
panel_density per panel, panel_pattern, priority_overlap_target,
panel_color_distribution, decoy_density, conflict_target.
Degenerates: only_panel_0, only_panel_2, all_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58b6f34fd9b2"
VERSION = "2.0.1"
TASK_ID = "58b6f34fd9b2"
SUMMARY = (
    "15 × w grid (w ~3-14), composed of THREE stacked 5-row "
    "PANELS at rows 0-4, 5-9, 10-14. Each panel uses values "
    "from {0, 1, 6, 8} in some pattern (random/blob/stripes/"
    "checker/border/diagonal/scatter). Rule: output = 5 × w "
    "grid. For each (r, c) in output, look at the 3 stacked "
    "cells g[r][c], g[r+5][c], g[r+10][c]. Compute the cell "
    "by priority OR: if ANY of the 3 is 6 → output 6; else if "
    "ANY is 1 → output 1; else if ANY is 8 → output 8; else → "
    "0. Net effect: 3-way overlay with color precedence 6 > 1 "
    "> 8 > 0."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input height is 15 (3 panels × 5 rows)",
    "panel cells use {0, 1, 6, 8}",
    "≥1 priority conflict (e.g., a 6 in panel A overrides a 1 in panel B)",
    "panels show varied patterns across train pairs",
]

PANEL_PATTERNS = ("random", "blob", "stripes", "checker", "border", "diagonal", "scatter")
DEGENERATE_TEXTURES = ("only_panel_0", "only_panel_2", "all_zero")
HELPFUL_TEXTURES = PANEL_PATTERNS

AXES = {
    "grid_w":             {"type": "int", "default": "rng 3..14", "valid": "1..30"},
    "panel0_density":     {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel1_density":     {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel2_density":     {"type": "float", "default": "rng 0.3..0.6", "valid": "0..1"},
    "panel_pattern":      {"type": "str", "default": "rng helpful",
                           "valid": "|".join(PANEL_PATTERNS)},
    "priority_overlap":   {"type": "float", "default": "rng 0..0.4", "valid": "0..1"},
    "color_distribution": {"type": "str", "default": "rng 6_dominant|1_dominant|8_dominant|uniform",
                           "valid": "6_dominant|1_dominant|8_dominant|uniform"},
    "conflict_target":    {"type": "int", "default": "rng 1..5", "valid": "1..15"},
    "texture":            {"type": "str", "default": "alias for panel_pattern",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        w_lo, w_hi = 3, 5
    elif difficulty == "hard":
        w_lo, w_hi = 11, 14
    else:
        w_lo, w_hi = 3, 14
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("panels")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], w, rng)
    densities = []
    for k in ("panel0_density", "panel1_density", "panel2_density"):
        d = float(overrides.get(k, ctx.draw_rng(k).uniform(0.3, 0.6)))
        densities.append(d)
    pattern = (overrides.get("texture") or overrides.get("panel_pattern")
               or ctx.draw_choice("panel_pattern", list(PANEL_PATTERNS)))
    color_dist = overrides.get("color_distribution",
                               ctx.draw_choice("color_distribution",
                                               ["6_dominant", "1_dominant", "8_dominant", "uniform"]))
    weights = {"6_dominant": [1, 1, 5, 2], "1_dominant": [1, 5, 1, 2],
               "8_dominant": [1, 2, 1, 5], "uniform": [1, 1, 1, 1]}[color_dist]
    panel_colors = [0, 1, 6, 8]
    g = full_grid(15, w, 0)
    for pi in range(3):
        r0 = pi * 5
        _fill_panel(g, r0, r0 + 5, w, pattern, densities[pi], panel_colors, weights, rng)
    # Force ≥1 conflict (e.g., paint panel0 cells overlapping with panel1).
    target = int(overrides.get("conflict_target",
                               ctx.draw_int("conflict_target", 1,
                                            max(1, 5 * w // 5))))
    _ensure_conflicts(g, w, target, rng)
    return g


def _fill_panel(g, r0, r1, w, pattern, density, colors, weights, rng):
    if pattern == "random":
        for r in range(r0, r1):
            for c in range(w):
                if rng.random() < density:
                    g[r][c] = rng.choices(colors, weights=weights)[0]
    elif pattern == "blob":
        bh = max(1, int((r1 - r0) * density)); bw = max(1, int(w * density))
        rr = rng.randint(r0, r1 - bh); cc = rng.randint(0, w - bw)
        color = rng.choices(colors, weights=weights)[0]
        for r in range(rr, rr + bh):
            for c in range(cc, cc + bw):
                g[r][c] = color
    elif pattern == "stripes":
        for r in range(r0, r1):
            if (r - r0) % 2 == 0:
                color = rng.choices(colors, weights=weights)[0]
                for c in range(w):
                    g[r][c] = color
    elif pattern == "checker":
        for r in range(r0, r1):
            for c in range(w):
                if (r + c) % 2 == 0:
                    g[r][c] = rng.choices(colors, weights=weights)[0]
    elif pattern == "border":
        c0 = rng.choices(colors, weights=weights)[0]
        for c in range(w):
            g[r0][c] = c0; g[r1 - 1][c] = c0
        for r in range(r0, r1):
            g[r][0] = c0; g[r][w - 1] = c0
    elif pattern == "diagonal":
        for k in range(min(r1 - r0, w)):
            g[r0 + k][k] = rng.choices(colors, weights=weights)[0]
    elif pattern == "scatter":
        for r in range(r0, r1):
            for c in range(w):
                if rng.random() < density * 0.5:
                    g[r][c] = rng.choices(colors, weights=weights)[0]


def _ensure_conflicts(g, w, target, rng):
    """Add ≥target cells where multiple panels disagree."""
    have = sum(1 for r in range(5) for c in range(w)
               if len({g[r][c], g[5 + r][c], g[10 + r][c]}) > 1)
    if have >= target:
        return
    cells = [(r, c) for r in range(5) for c in range(w)]
    rng.shuffle(cells)
    for (r, c) in cells:
        if have >= target: break
        # Force a conflict: assign different colors at panel positions.
        g[r][c] = 6
        g[5 + r][c] = 1
        g[10 + r][c] = 8
        have += 1


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 15 rows (3 panels × 5), uses only {0, 1, 6, 8}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != 15:
        errs.append(f"expected 15 rows (3 × 5 panels), got {h}")
    allowed = {0, 1, 6, 8}
    bad = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] not in allowed}
    if bad:
        errs.append(f"unexpected cell values (expected {{0,1,6,8}}): {sorted(bad)}")
    return errs


def _draw_from_degenerate(name, w, rng):
    g = full_grid(15, w, 0)
    if name == "only_panel_0":
        for r in range(5):
            for c in range(w):
                if rng.random() < 0.5:
                    g[r][c] = rng.choice([1, 6, 8])
        return g
    if name == "only_panel_2":
        for r in range(10, 15):
            for c in range(w):
                if rng.random() < 0.5:
                    g[r][c] = rng.choice([1, 6, 8])
        return g
    if name == "all_zero":
        # Need ≥1 fg.
        g[0][0] = 6
        return g
    return g
