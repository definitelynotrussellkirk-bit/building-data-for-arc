"""Generator for f18ec8cc.

Rule: vertical color regions are reversed when their widths are
unique, otherwise left-rotated by one region.

Combinatorial axes (8): grid_h, region_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias, widths.
Degenerates: no_regions, single_region, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fc8ce6bdc6ea"
VERSION = "3.0.0"  # vary region count (2-6) + randomized widths exercising BOTH branches (unique->reverse / repeat->rotate); wider grids
TASK_ID = "fc8ce6bdc6ea"
SUMMARY = (
    "0-bg grid divided into 2-6 ADJACENT VERTICAL COLOR "
    "REGIONS (left to right), each a distinct color (adjacent "
    "regions differ so boundaries are detectable) with a "
    "small per-region decoration cell. Region widths are "
    "randomized: SOMETIMES all distinct, sometimes with a "
    "repeat. Rule: detect the regions by per-column modal "
    "color; if ALL region widths are unique, REVERSE the "
    "region order; otherwise ROTATE the regions LEFT by one. "
    "Columns (including decorations) are copied wholesale. "
    "Net: regions flip or cyclically shift depending on "
    "whether their widths are all unique."
)

INVARIANTS = [
    "2-6 adjacent vertical regions; each column's modal color is its region color",
    "adjacent regions have different colors (so the boundary is detected)",
    "widths sometimes all-unique (-> reverse branch), sometimes repeated (-> rotate branch)",
    "full columns (incl. decorations) are copied into the new region order",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_regions", "single_region", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "6-9 easy / 7-12 med / 9-16 hard", "valid": "5..18"},
    "region_count":   {"type": "int", "default": "2-3 easy / 3-4 med / 4-6 hard", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "widths_mode":    {"type": "str", "default": "rng all_unique|has_repeat",
                       "valid": "all_unique|has_repeat"},
    "palette_size":   {"type": "int", "default": "= region_count", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "vertical_regions", "valid": "vertical_regions"},
    "n_distinct_colors": {"type": "int", "default": "= region_count", "valid": "2..6"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _modal(row):
    counts = {}
    for v in row:
        counts[v] = counts.get(v, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify adjacent vertical color regions with detectable width branch."""
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    if h < 5 or w < 4:
        return ["grid too small for region task"]
    col_modes = []
    for c in range(w):
        col = [grid[r][c] for r in range(h)]
        mode = _modal(col)
        if mode == 0:
            return ["column modal color is background"]
        if col.count(mode) <= h // 2:
            return ["column has no clear modal region color"]
        col_modes.append(mode)
    runs = []
    start = 0
    for c in range(1, w + 1):
        if c == w or col_modes[c] != col_modes[start]:
            runs.append((col_modes[start], c - start))
            start = c
    errs = []
    if not (2 <= len(runs) <= 6):
        errs.append(f"expected 2..6 vertical regions, found {len(runs)}")
    if any(width < 2 for _, width in runs):
        errs.append("region width below 2")
    if any(runs[i][0] == runs[i + 1][0] for i in range(len(runs) - 1)):
        errs.append("adjacent regions share the same modal color")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 9)
        n = ctx.draw_int("region_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 16)
        n = ctx.draw_int("region_count", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        n = ctx.draw_int("region_count", 3, 4)
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0}))

    # Widths: half the time ALL-UNIQUE (rule REVERSES the regions), else with a REPEAT
    # (rule ROTATES left). Widths fit the 30-col canvas.
    if rng.random() < 0.5:
        widths = rng.sample(range(2, 2 + n), n)             # n distinct values -> unique
    else:
        widths = [rng.randint(2, 5) for _ in range(n)]
        if len(set(widths)) == n:                           # ensure at least one repeat
            widths[1] = widths[0]

    g = full_grid(h, sum(widths), 0)
    c0 = 0
    for idx, width in enumerate(widths):
        for r in range(h):
            for c in range(c0, c0 + width):
                g[r][c] = colors[idx]
        if width > 2:                                       # per-region decoration cell
            g[1][c0 + width - 1] = colors[(idx + 1) % n]
        c0 += width
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 9, 0)
    if name == "no_regions":
        return g
    if name == "single_region":
        for r in range(6):
            for c in range(9):
                g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(9):
                g[r][c] = 2
        return g
    return g
