"""Generator for puzzle 22eb0ac0.

Rule: for each row r, if g[r][0] != 0 AND g[r][0] == g[r][w-1], fill
the entire row with that color; else keep cells.

Combinatorial axes: grid_h/w, palette_size, row_kind_distribution
(uniform/biased_match/biased_mismatch), interior_decoy_density.
Degenerates: all_match, all_mismatch, all_blank.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "58e533041a8e"
VERSION = "2.0.1"
TASK_ID = "58e533041a8e"
SUMMARY = (
    "0-bg grid (h, w ∈ 4-18, by "
    "difficulty) with: each ROW "
    "INDEPENDENTLY assigned a KIND "
    "per ROW_DISTRIBUTION ∈ {uniform, "
    "biased_match, biased_mismatch, "
    "alternating}: (a) 'match' → "
    "g[r][0] = g[r][w-1] = SAME "
    "color drawn from palette; "
    "(b) 'mismatch' → g[r][0] = a, "
    "g[r][w-1] = b (different "
    "colors); (c) 'blank' → both "
    "left and right are 0. Palette "
    "of 2-6 distinct colors drawn "
    "from {1..9}. INTERIOR DECOY "
    "DENSITY ∈ 0-20% sprinkles "
    "random colored cells in "
    "non-edge columns. Generation "
    "guarantees ≥1 matching-row "
    "exists. Rule (FOR EACH ROW r: "
    "IF g[r][0] != 0 AND g[r][0] "
    "== g[r][w-1]: FILL THE ENTIRE "
    "ROW (ALL w COLUMNS) WITH THAT "
    "COLOR; ELSE: KEEP THE ROW "
    "AS-IS): For EACH row r: "
    "READ g[r][0] and g[r][w-1]. "
    "IF both are non-zero AND "
    "equal: PAINT every cell of "
    "that row with that color. "
    "OTHERWISE: row unchanged. "
    "Net: matching-pair rows "
    "fill solidly with their "
    "edge color; mismatch and "
    "blank rows stay."
)

INVARIANTS = [
    "≥1 row with matching non-zero left/right pair",
    "rule expects bg = 0 (compares to 0)",
]

ROW_DISTRIBUTIONS = ("uniform", "biased_match", "biased_mismatch", "alternating")
DEGENERATE_TEXTURES = ("all_match", "all_mismatch", "all_blank")
HELPFUL_TEXTURES = ROW_DISTRIBUTIONS

AXES = {
    "grid_h":          {"type": "int", "default": "rng 4..14", "valid": "4..18"},
    "grid_w":          {"type": "int", "default": "rng 4..14", "valid": "4..18"},
    "palette_size":    {"type": "int", "default": "rng 2..6", "valid": "1..9"},
    "row_distribution": {"type": "str", "default": "rng helpful",
                         "valid": "|".join(ROW_DISTRIBUTIONS)},
    "interior_decoy_density": {"type": "float", "default": "rng 0..0.2", "valid": "0..0.5"},
    "texture":         {"type": "str", "default": "alias for row_distribution",
                        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 4, 7
    elif difficulty == "hard":
        h_lo, h_hi = 11, 14
    else:
        h_lo, h_hi = 4, 14
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_palette = int(overrides.get("palette_size",
                                  ctx.draw_int("palette_size", 2, 6)))
    palette = list(ctx.draw_distinct_colors("palette", n=max(2, n_palette), exclude={0}))
    distribution = (overrides.get("texture") or overrides.get("row_distribution")
                    or ctx.draw_choice("row_distribution", list(ROW_DISTRIBUTIONS)))
    decoy_d = float(overrides.get("interior_decoy_density",
                                  ctx.draw_rng("interior_decoy_density").uniform(0.0, 0.2)))
    g = full_grid(h, w, 0)
    for r in range(h):
        kind = _pick_row_kind(distribution, r, rng)
        if kind == "match":
            col = rng.choice(palette)
            g[r][0] = col
            g[r][w - 1] = col
        elif kind == "mismatch":
            if len(palette) >= 2:
                a, b = rng.sample(palette, 2)
            else:
                a, b = palette[0], palette[0]
            g[r][0] = a
            g[r][w - 1] = b
        if decoy_d > 0:
            for c in range(1, w - 1):
                if rng.random() < decoy_d:
                    g[r][c] = rng.choice(palette)
    if not any(g[r][0] != 0 and g[r][0] == g[r][w - 1] for r in range(h)):
        col = palette[0]
        g[0][0] = col
        g[0][w - 1] = col
    return g


def _pick_row_kind(dist, r, rng):
    if dist == "uniform":
        return rng.choice(["match", "mismatch", "blank"])
    if dist == "biased_match":
        return rng.choices(["match", "mismatch", "blank"], weights=[5, 2, 1])[0]
    if dist == "biased_mismatch":
        return rng.choices(["match", "mismatch", "blank"], weights=[1, 5, 2])[0]
    if dist == "alternating":
        return ["match", "mismatch", "blank"][r % 3]
    return rng.choice(["match", "mismatch", "blank"])


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one row with matching non-zero left/right endpoints."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    match_found = any(
        grid[r][0] != 0 and grid[r][0] == grid[r][w - 1]
        for r in range(h)
    )
    if not match_found:
        errs.append("no row with matching non-zero left/right endpoints found")
    return errs


def _draw_from_degenerate(name, h, w, rng):
    palette = list(range(1, 10))
    rng.shuffle(palette)
    g = full_grid(h, w, 0)
    if name == "all_match":
        for r in range(h):
            col = rng.choice(palette)
            g[r][0] = col
            g[r][w - 1] = col
        return g
    if name == "all_mismatch":
        for r in range(h):
            a, b = rng.sample(palette, 2)
            g[r][0] = a
            g[r][w - 1] = b
        # Force one match so invariant satisfied.
        g[0][0] = palette[0]
        g[0][w - 1] = palette[0]
        return g
    if name == "all_blank":
        # Force one match.
        g[0][0] = palette[0]
        g[0][w - 1] = palette[0]
        return g
    return g
