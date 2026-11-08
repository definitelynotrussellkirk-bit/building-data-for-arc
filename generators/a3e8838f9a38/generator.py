"""Generator for ARC task 0692e18c.

Rule: input is n × n. Output is n² × n²; for each (r, c):
  br, bc = r // n, c // n; sr, sc = r % n, c % n
  out[r][c] = mode(g, 0) if input[br][bc] != 0 AND input[sr][sc] == 0
  else 0
i.e., fractal — bg-mask tiled onto fg anchors.

Combinatorial axes (8): side, fg_color, fg_density, fg_layout (texture),
bg_count_target, fg_anchor_pattern (where the nonzero anchors are),
include_extra_palette, noise_overlay.
Degenerates: all_zero, all_filled, single_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density,
)

GENERATOR_ID = "a3e8838f9a38"
VERSION = "1.2.1"
TASK_ID = "a3e8838f9a38"
SUMMARY = (
    "Square n × n grid (n in 3..5) with a binary mask using bg=0 and "
    "one fg color (the mode). Rule: output is n² × n². For each "
    "(R, C) where R, C in [0, n²-1]: br = R//n, bc = C//n (outer block "
    "index); sr = R%n, sc = C%n (inner cell index). If input[br][bc] "
    "is fg (non-zero), then output[R][C] = fg if input[sr][sc] is bg, "
    "else 0. If input[br][bc] is bg, output[R][C] = 0. Equivalent to "
    "tiling the inverse of the input onto the fg anchor positions — "
    "a fractal."
)

# Rivals: 'output is input' refuted by demos (output is n² × n²).
# 'output is input tiled n times (without inverse)' refuted by demos
# showing inverse pattern. 'output is solid n² × n² of fg' refuted.
# 'output is input rotated 90' refuted. 'use bg as the fill (instead
# of fg color)' refuted by demos showing fg color. 3 demos with
# different mask patterns pin the fractal structure.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is square n × n with n in 3..5",
    "fg color is the mode (excluding bg=0)",
    "≥1 zero AND ≥1 fg cell (so output is non-trivial)",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "checkerboard", "frame", "ring", "plus", "cross",
)
DEGENERATE_TEXTURES = ("all_zero", "all_filled", "single_zero")

AXES = {
    "side":           {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "fg_color":       {"type": "color", "default": "rng (≠0)", "valid": "1..9"},
    "fg_density":     {"type": "float", "default": "rng 0.4..0.7", "valid": "0..1"},
    "texture":        {"type": "str", "default": "rng helpful",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_count_target": {"type": "int", "default": "rng 2..n*n/2", "valid": "1..n*n"},
    "fg_anchor_pattern": {"type": "str", "default": "rng helpful",
                          "valid": "diffuse|clustered|edge|center"},
    "noise_overlay":  {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
    "include_extra_palette": {"type": "bool", "default": "false", "valid": "true|false"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is square n×n with n in 3..5; contains both zero and
    non-zero cells (non-trivial fractal mask)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != w:
        errs.append(f"grid is not square: {h}×{w}")
        return errs
    if h < 3 or h > 5:
        errs.append(f"grid side {h} not in 3..5")
    has_zero = any(grid[r][c] == 0 for r in range(h) for c in range(w))
    has_nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not has_zero:
        errs.append("no zero cell (mask is all-filled; output would be all-zero)")
    if not has_nonzero:
        errs.append("no non-zero cell (mask is all-zero; output would be all-zero)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        s_lo, s_hi = 3, 4
    elif difficulty == "hard":
        s_lo, s_hi = 5, 5
    else:
        s_lo, s_hi = 3, 5
    n = ctx.draw_int("side", s_lo, s_hi)
    rng = ctx.draw_rng("cells")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], n, rng)
    fg = int(overrides.get("fg_color", ctx.draw_color("fg_color", exclude={0})))
    palette = [0, fg]
    if bool(overrides.get("include_extra_palette", False)):
        extras = list(ctx.draw_distinct_colors("extras", n=1, exclude={0, fg}))
        palette.append(extras[0] if extras else fg)
    texture = overrides.get("texture",
                            ctx.draw_choice("texture", list(HELPFUL_TEXTURES)))
    g = fill_texture(texture, n, n, palette, rng)
    fill_d = float(overrides.get("fg_density",
                                 ctx.draw_rng("fg_density").uniform(0.4, 0.7)))
    if fill_d < 1.0:
        g = apply_bg_density(g, palette, rng, 1.0 - fill_d)
    target_zeros = int(overrides.get("bg_count_target",
                                     ctx.draw_int("bg_count_target", 2,
                                                  max(2, n * n // 2))))
    cur_zeros = sum(1 for r in range(n) for c in range(n) if g[r][c] == 0)
    while cur_zeros < target_zeros:
        rr = rng.randint(0, n - 1); cc = rng.randint(0, n - 1)
        if g[rr][cc] != 0:
            g[rr][cc] = 0
            cur_zeros += 1
    # Ensure ≥1 fg cell so anchor pattern has anchors.
    if not any(g[r][c] != 0 for r in range(n) for c in range(n)):
        g[0][0] = fg
    # Ensure ≥1 zero cell so output isn't all 0.
    if not any(g[r][c] == 0 for r in range(n) for c in range(n)):
        g[n - 1][n - 1] = 0
    return g


def _draw_from_degenerate(name, n, rng):
    g = full_grid(n, n, 0)
    fg = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if name == "all_zero":
        # All bg — rule's anchor condition (input[br][bc] != 0) never fires.
        g[0][0] = fg
        return g
    if name == "all_filled":
        for r in range(n):
            for c in range(n):
                g[r][c] = fg
        # Need ≥1 zero
        g[n - 1][n - 1] = 0
        return g
    if name == "single_zero":
        for r in range(n):
            for c in range(n):
                g[r][c] = fg
        g[n // 2][n // 2] = 0
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    n = len(grid)
    if any(len(row) != n for row in grid) or not (3 <= n <= 5):
        errors.append("input must be square with side 3..5")
    vals = [v for row in grid for v in row]
    nonzero = [v for v in vals if v != 0]
    if not nonzero:
        errors.append("need at least one nonzero anchor cell")
    if 0 not in vals:
        errors.append("need at least one zero cell so inverse tile is visible")
    if len(set(nonzero)) > 1:
        errors.append("default instance should use a single foreground color")
    return errors
