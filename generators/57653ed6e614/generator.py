"""Generator for ARC task 29c11459.

Rule: for each row, lv = g[r][0], rv = g[r][w-1]. If both non-zero:
  c < mid → lv; c == mid → 5; c > mid → rv.
Else keep cell as-is. (mid = w/2 with integer division.)

Combinatorial axes: grid_h, grid_w (odd ≥ 3), left_color, right_color,
n_active_rows (rows with both edges non-zero), edge_distribution.
Degenerates: no_active_rows (rule no-op), all_rows_active,
single_color_edges (lv == rv).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57653ed6e614"
VERSION = "2.1.0"
TASK_ID = "57653ed6e614"
SUMMARY = (
    "0-bg grid with h ∈ {3..14} and ODD "
    "WIDTH w ∈ {5, 7, 9, 11, 13, 15} so "
    "the middle column mid = w//2 is "
    "well-defined: (a) ACTIVE ROWS — "
    "selected by one of 4 distributions "
    "(all_active / half_active / "
    "few_active / alternating_inactive). "
    "For each active row r: set "
    "g[r][0] = LEFT_COLOR and "
    "g[r][w-1] = RIGHT_COLOR (LEFT ≠ "
    "RIGHT, both non-{0, 5}); (b) "
    "OPTIONAL DECOY CELLS scattered in "
    "interior columns (1..w-2) at "
    "density 0..0.2 with random "
    "colors. If no rows are active, "
    "force row 0 active. Rule (FOR "
    "EACH ROW WITH NON-ZERO LEFT+RIGHT "
    "EDGES, CREATE LEFT/RIGHT BANDS "
    "SPLIT BY COLOR 5 AT THE MIDDLE "
    "COLUMN): for EACH ROW r where "
    "g[r][0] = lv ≠ 0 AND g[r][w-1] "
    "= rv ≠ 0: REPLACE the row: for "
    "c < mid: cell = lv; for c == "
    "mid: cell = 5; for c > mid: "
    "cell = rv. Non-active rows are "
    "unchanged (interior decoys "
    "stay). Net: each active row "
    "becomes a 3-zone band — left "
    "color, gray center, right "
    "color — replacing any "
    "interior decoys in that row."
)

INVARIANTS = [
    "grid width is odd ≥ 3 (so middle col is well-defined)",
    "≥1 row has both edges non-zero (rule has visible effect)",
    "left and right edge colors are distinct (else output looks like a fill)",
]

EDGE_DISTRIBUTIONS = ("single_active", "all_active", "half_active", "few_active",
                     "alternating_inactive")
DEGENERATE_TEXTURES = ("no_active_rows", "single_color_edges", "single_active_row")
HELPFUL_TEXTURES = EDGE_DISTRIBUTIONS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 3..14", "valid": "1..18"},
    "grid_w":             {"type": "choice", "default": "rng odd 5..15", "valid": "5|7|9|11|13|15"},
    "left_color":         {"type": "color", "default": "rng (≠0,5)", "valid": "1..9 (≠5)"},
    "right_color":        {"type": "color", "default": "rng (≠0,5,left)", "valid": "1..9"},
    "edge_distribution":  {"type": "str", "default": "rng helpful",
                           "valid": "|".join(EDGE_DISTRIBUTIONS)},
    "interior_decoy_density": {"type": "float", "default": "rng 0..0.2", "valid": "0..0.5"},
    "texture":            {"type": "str", "default": "alias for edge_distribution",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, w_choices = 3, 6, [5, 7]
    elif difficulty == "hard":
        h_lo, h_hi, w_choices = 11, 14, [11, 13, 15]
    else:
        h_lo, h_hi, w_choices = 3, 14, [5, 7, 9, 11, 13, 15]
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_choice("grid_w", w_choices)
    rng = ctx.draw_rng("rows")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    left = int(overrides.get("left_color", ctx.draw_color("left_color", exclude={0, 5})))
    right = int(overrides.get("right_color", ctx.draw_color("right_color", exclude={0, 5, left})))
    distribution = (overrides.get("texture") or overrides.get("edge_distribution")
                    or "single_active")
    # The real task's demos contain a single active edge row and otherwise blank
    # background.  Keep decoys opt-in; the previous default 0..0.2 decoy density
    # made the generator structurally drift to many-object inputs.
    decoy_d = float(overrides.get("interior_decoy_density", 0.0))
    g = full_grid(h, w, 0)
    if distribution == "single_active":
        active_rows = {rng.randrange(h)}
    else:
        active_rows = {r for r in range(h) if _is_active(distribution, r, h, rng)}
        if not active_rows:
            active_rows = {rng.randrange(h)}
    for r in range(h):
        if r in active_rows:
            g[r][0] = left
            g[r][w - 1] = right
        if decoy_d > 0:
            for c in range(1, w - 1):
                if rng.random() < decoy_d:
                    g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _is_active(dist, r, h, rng):
    if dist == "single_active":
        return r == 0
    if dist == "all_active":
        return True
    if dist == "half_active":
        return r < h // 2
    if dist == "few_active":
        return rng.random() < 0.4
    if dist == "alternating_inactive":
        return r % 2 == 0
    return rng.random() < 0.6


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_active_rows":
        # No row has both edges non-zero — rule is identity.
        for r in range(h):
            for c in range(w):
                if rng.random() < 0.3:
                    g[r][c] = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
        return g
    if name == "single_color_edges":
        c0 = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
        for r in range(h):
            g[r][0] = c0
            g[r][w - 1] = c0
        return g
    if name == "single_active_row":
        left = 1; right = 2
        g[0][0] = left
        g[0][w - 1] = right
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Width is odd ≥3; ≥1 row has both edge cells non-zero (rule has visible effect)."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if w < 3 or w % 2 == 0:
        errs.append(f"width {w} must be odd ≥3")
    active_rows = [r for r in range(h) if grid[r][0] != 0 and grid[r][w - 1] != 0]
    if not active_rows:
        errs.append("no row with both edge cells non-zero — rule would be a no-op")
    for r in active_rows:
        if grid[r][0] == grid[r][w - 1]:
            errs.append("active row has identical left/right colors")
            break
    return errs
