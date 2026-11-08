"""Generator for ARC task 5b6cbef5.

Rule: `(rule! (lambda (g) (self-tile g)))`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay,
)

GENERATOR_ID = "a1fffe30b85b"
VERSION = "1.3.0"
TASK_ID = "a1fffe30b85b"
SUMMARY = (
    "Small H × W binary grid (bg=0 + 1 fg color, H, W ≤ 9). Rule: "
    "self-tile — produce H² × W² output. For block at (br, bc) in "
    "[0, H) × [0, W): if input[br][bc] is fg, copy input into that "
    "block; if input[br][bc] is bg, leave that block all 0. The "
    "input thus serves as both a mask and a template."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is small enough that self-tile stays within ARC bounds (≤9 each side)",
    "input contains at least one zero and at least one foreground cell",
    "foreground cells share one color, matching the source examples",
]

HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("dense_fg", "single_fg")

AXES = {
    "grid_h": {"type": "int", "default": "rng 2..9", "valid": "2..9"},
    "grid_w": {"type": "int", "default": "rng 2..9", "valid": "2..9"},
    "fg_color": {"type": "color", "default": "rng", "valid": "1..9"},
    "fill_ratio": {"type": "float", "default": "rng 0.20..0.80", "valid": "0.05..0.95"},
    "texture": {"type": "str", "default": "helpful only",
                "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    # Self-tile produces H² × W² output, so input size capped at 5
    # so output stays within ARC's 30×30 limit.
    if difficulty == "easy":
        s_lo, s_hi = 2, 3
    elif difficulty == "hard":
        s_lo, s_hi = 4, 5
    else:
        s_lo, s_hi = 2, 5

    h = ctx.draw_int("grid_h", s_lo, s_hi)
    w = ctx.draw_int("grid_w", s_lo, s_hi)
    fg = ctx.draw_color("fg_color", exclude={0})
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, fg, rng)

    if "texture" in overrides:
        texture = overrides["texture"]
    else:
        texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES))
    palette = [0, fg]
    g = fill_texture(texture, h, w, palette, rng)

    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.4)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.05)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)

    flat = [v for row in g for v in row]
    if all(v == 0 for v in flat):
        g[0][0] = fg
    elif all(v != 0 for v in flat):
        g[h - 1][w - 1] = 0
    return g


def _draw_from_degenerate(name, h, w, fg, rng):
    """Edge-case input where the self-tile signature is hidden.

    dense_fg  — almost every cell is fg; output is nearly uniform.
    single_fg — exactly one fg cell; subtle output.
    """
    g = full_grid(h, w, 0)
    if name == "dense_fg":
        for r in range(h):
            for c in range(w):
                g[r][c] = fg
        bg_r = rng.randrange(h)
        bg_c = rng.randrange(w)
        g[bg_r][bg_c] = 0
        return g
    if name == "single_fg":
        rr = rng.randrange(h)
        rc = rng.randrange(w)
        g[rr][rc] = fg
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    h = len(grid); w = len(grid[0]) if h else 0
    vals = [v for row in grid for v in row]
    nonzero = {v for v in vals if v != 0}
    msgs = []
    if not (2 <= h <= 5 and 2 <= w <= 5):
        msgs.append(f"input dims {h}x{w} would make self-tile exceed 30x30 or underteach")
    if len(nonzero) != 1:
        msgs.append("expected exactly one foreground color")
    if not any(v == 0 for v in vals):
        msgs.append("no background cell; self-tile mask is fully on")
    if not any(v != 0 for v in vals):
        msgs.append("no foreground cell; self-tile output would be empty")
    return msgs
