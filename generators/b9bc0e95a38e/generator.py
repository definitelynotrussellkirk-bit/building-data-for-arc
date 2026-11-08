"""Generator for d06dbe63.

Rule: cyan seed emits a clipped gray stair pattern up-right and
down-left.

Combinatorial axes (8): grid_h/w, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, seed_kind, n_seeds.
Degenerates: no_seed, full_grid, single_pixel.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b9bc0e95a38e"
VERSION = "2.1.0"  # 2.0.0->2.1.0: jitter the corner-bias seed positions (were
# fixed at (3,3)/(3,w-4)/... -> duplicate outputs at same grid size). Now every
# bias picks within a region so the marker position varies fully. uniq_out up.
TASK_ID = "b9bc0e95a38e"
SUMMARY = (
    "0-bg grid (h, w ∈ 9-16, by "
    "difficulty) with: ONE COLOR-8 "
    "(CYAN) SEED PIXEL placed at a "
    "position per POSITION_BIAS ∈ "
    "{center (rng), top_left (3, 3), "
    "top_right (3, w-4), bottom_left "
    "(h-4, 3), bottom_right (h-4, "
    "w-4)} with ≥3-cell margin from "
    "all edges. Rule (FROM THE CYAN "
    "SEED, EMIT A CLIPPED GRAY (5) "
    "STAIR PATTERN: ONE ARM GOES "
    "UP-RIGHT IN STAIR STEPS, ONE "
    "ARM GOES DOWN-LEFT IN STAIR "
    "STEPS; THE STAIRS ALTERNATE "
    "ONE-CELL HORIZONTAL AND ONE-"
    "CELL VERTICAL MOVES, PAINTED "
    "IN COLOR 5; SEED CELL "
    "PRESERVED AS COLOR 8): FIND "
    "the COLOR-8 seed at (sr, sc). "
    "EMIT UP-RIGHT ARM: walk "
    "alternating up-1, right-1, "
    "up-1, right-1 ... until "
    "hitting the grid edge, "
    "painting each cell COLOR 5. "
    "EMIT DOWN-LEFT ARM: walk "
    "alternating down-1, left-1, "
    "... until edge, painting "
    "color 5. Seed stays cyan. "
    "Net: cyan dot grows a 2-arm "
    "gray stair pattern."
)

INVARIANTS = [
    "background is color 0",
    "there is exactly one color-8 seed pixel",
    "the rule preserves the seed and paints color-5 stair segments from it",
    "the seed leaves room for both upward-right and downward-left stair arms",
]

POSITION_BIASES = ("center", "top_left", "top_right", "bottom_left", "bottom_right")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seed", "full_grid", "single_pixel")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "height":         {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "width":          {"type": "int", "default": "rng 9..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "fixed", "valid": "fixed"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "seed_kind":      {"type": "str", "default": "single", "valid": "single"},
    "n_seeds":        {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for position_bias",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 9, 10
    elif difficulty == "hard":
        h_lo, h_hi = 13, 16
    else:
        h_lo, h_hi = 9, 13
    h = ctx.draw_int("height", h_lo, h_hi)
    w = ctx.draw_int("width", h_lo, h_hi)
    pos = (overrides.get("texture") if overrides.get("texture") in POSITION_BIASES else None) or \
          overrides.get("position_bias") or \
          ctx.draw_choice("position_bias", list(POSITION_BIASES))
    g = full_grid(h, w, 0)
    rlo, rhi = 3, h - 4
    clo, chi = 3, w - 4
    rmid = (rlo + rhi) // 2
    cmid = (clo + chi) // 2
    if pos == "top_left":
        r = rng.randint(rlo, max(rlo, rmid)); c = rng.randint(clo, max(clo, cmid))
    elif pos == "top_right":
        r = rng.randint(rlo, max(rlo, rmid)); c = rng.randint(min(cmid, chi), chi)
    elif pos == "bottom_left":
        r = rng.randint(min(rmid, rhi), rhi); c = rng.randint(clo, max(clo, cmid))
    elif pos == "bottom_right":
        r = rng.randint(min(rmid, rhi), rhi); c = rng.randint(min(cmid, chi), chi)
    else:
        r = rng.randint(rlo, rhi)
        c = rng.randint(clo, chi)
    g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 10, 0)
    if name == "no_seed":
        return g
    if name == "single_pixel":
        g[5][5] = 8
        return g
    if name == "full_grid":
        for r in range(10):
            for c in range(10):
                g[r][c] = 5
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    if len(seeds) != 1:
        return ["expected exactly one cyan seed"]
    h, w = len(grid), len(grid[0])
    r, c = seeds[0]
    errs: list[str] = []
    if min(r, c, h - 1 - r, w - 1 - c) < 3:
        errs.append("cyan seed must have >=3-cell margin for both stair arms")
    extras = [(rr, cc, v) for rr, row in enumerate(grid) for cc, v in enumerate(row) if v not in (0, 8)]
    if extras:
        errs.append("input should contain only background and one seed")
    return errs
