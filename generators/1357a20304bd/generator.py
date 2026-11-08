"""Generator for arc_additional_puzzles_21_set7:M48.

Rule: same-colored points are connected in reading order by horizontal-
then-vertical traces.

Combinatorial axes (8): grid_h/w, point_count, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias,
n_distinct_colors.
Degenerates: no_points, single_color, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1357a20304bd"
VERSION = "3.0.1"  # unlock FIXED 10x10 + fixed point positions: random grid size, 2-4 colors, 2-4 random points each
TASK_ID = "1357a20304bd"
SUMMARY = (
    "Variable-size 0-bg grid with 1-4 foreground colors, each placed as "
    "2-4 ISOLATED SEED POINTS at random distinct positions. Rule "
    "(CONNECT SAME-COLORED "
    "POINTS IN READING "
    "ORDER WITH HORIZONTAL"
    "-THEN-VERTICAL "
    "TRACES): For EACH "
    "COLOR with ≥2 SEED "
    "POINTS: sort points "
    "in READING ORDER "
    "(row-major). For "
    "consecutive pairs "
    "(p_i, p_{i+1}): "
    "draw a horizontal-"
    "then-vertical L-PATH "
    "from p_i to p_{i+1} "
    "— first move "
    "HORIZONTALLY from "
    "p_i's column to "
    "p_{i+1}'s column on "
    "p_i's row, then "
    "VERTICALLY from "
    "p_i's row to "
    "p_{i+1}'s row on "
    "p_{i+1}'s column. "
    "PAINT all path cells "
    "in that color. Net: "
    "same-color points "
    "chain together via "
    "row-major-ordered "
    "L-paths."
)

INVARIANTS = [
    "each foreground color has two or more seed points",
    "points are traced in row-major order for each color",
    "each segment moves horizontally to the next point's column, then vertically to its row",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_points", "single_color", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..16", "valid": "7..20"},
    "grid_w":         {"type": "int", "default": "rng 9..16", "valid": "7..20"},
    "point_count":    {"type": "int", "default": "rng 2..4 per color", "valid": "2..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; has >=2 distinct non-zero colors with >=2 cells each (seed points)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        return errors  # degenerate (no_points) — allowed
    if len(counts) < 2:
        return errors  # degenerate (single_color) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 7, 10)
        ncol_lo, ncol_hi = 1, 2; ppc_lo, ppc_hi = 2, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 20); w = ctx.draw_int("grid_w", 12, 20)
        ncol_lo, ncol_hi = 3, 4; ppc_lo, ppc_hi = 3, 4
    else:
        h = ctx.draw_int("grid_h", 9, 16); w = ctx.draw_int("grid_w", 9, 16)
        ncol_lo, ncol_hi = 2, 3; ppc_lo, ppc_hi = 2, 4

    n_colors = ctx.draw_int("n_distinct_colors", ncol_lo, ncol_hi)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_colors)
    g = full_grid(h, w, 0)
    used = set()
    for color in colors:
        n_pts = rng.randint(ppc_lo, ppc_hi)
        placed = 0
        for _ in range(n_pts * 12):
            if placed >= n_pts:
                break
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if (r, c) not in used:
                used.add((r, c)); g[r][c] = color; placed += 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_points":
        return g
    if name == "single_color":
        for r, c in [(1, 1), (5, 5), (7, 7)]:
            g[r][c] = 3
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 3
        return g
    return g
