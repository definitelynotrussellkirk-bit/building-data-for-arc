"""Generator for ARC task 74dd1130.

Rule: `(rule! transpose)`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay, apply_border,
)

GENERATOR_ID = "19a48004b265"
VERSION = "2.1.0"  # guard against monochrome/symmetric transpose demos
TASK_ID = "19a48004b265"
SUMMARY = (
    "Multicolor grid (h, w ∈ 2-18, by "
    "difficulty), palette of 2-9 "
    "distinct colors drawn at random "
    "(may include 0), filled by "
    "TEXTURE ∈ {noise / sparse / blob / "
    "stripes / gradient / checkerboard "
    "/ frame / ring / plus} via "
    "fill_texture. After base fill: "
    "(a) apply_bg_density (0-50%) "
    "introduces bg sparsity; "
    "(b) apply_noise_overlay (0-10%) "
    "flips random cells; (c) "
    "apply_border per BORDER_MODE ∈ "
    "{free, always_bg, always_fg} "
    "may overwrite the outer border. "
    "The grid is GENERALLY NOT "
    "TRANSPOSE-SYMMETRIC (rectangular "
    "or asymmetric content), so the "
    "rule has visible effect. Rule "
    "(TRANSPOSE THE GRID — SWAP ROWS "
    "AND COLUMNS): OUTPUT[c][r] = "
    "INPUT[r][c] for all (r, c). "
    "Result is a w×h grid where the "
    "input's rows become the output's "
    "columns and vice versa. Net: "
    "the entire grid is reflected "
    "across the main diagonal — "
    "each cell value moves to its "
    "transposed position."
)

INVARIANTS = [
    "input is a rectangular grid",
    "examples may be square or rectangular",
    "colors are sampled from a small palette",
]

# All 9 helpful textures apply. Transpose is rule-agnostic wrt content;
# different textures expose different aspects (gradient axis-swap,
# frame preserved, checkerboard preserved, plus inverted, etc.).
HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("transpose_symmetric",)

AXES = {
    "grid_h":       {"type": "int",   "default": "rng 2..18", "valid": "1..30"},
    "grid_w":       {"type": "int",   "default": "rng 2..18", "valid": "1..30"},
    "palette_size": {"type": "int",   "default": "rng 2..9",  "valid": "1..10"},
    "texture":      {"type": "str",   "default": "rng helpful",
                     "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
    "bg_density":   {"type": "float", "default": "rng 0..0.5",  "valid": "0..0.95"},
    "noise_overlay": {"type": "float", "default": "rng 0..0.10", "valid": "0..0.5"},
    "border_mode":  {"type": "str",   "default": "rng free|always_bg|always_fg",
                     "valid": "free|always_bg|always_fg"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, c_lo, c_hi = 2, 6, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, c_lo, c_hi = 10, 18, 5, 9
    else:
        h_lo, h_hi, c_lo, c_hi = 2, 18, 2, 9

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    n_colors = ctx.draw_int("palette_size", c_lo, c_hi)
    palette = ctx.draw_distinct_colors("palette", n=n_colors)
    rng = ctx.draw_rng("cells")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, palette, rng)

    if "texture" in overrides:
        texture = overrides["texture"]
    else:
        texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES))
    g = fill_texture(texture, h, w, palette, rng)

    bg_d = float(overrides.get("bg_density",
                               ctx.draw_rng("bg_density").uniform(0.0, 0.5)))
    if bg_d > 0.0:
        g = apply_bg_density(g, palette, rng, bg_d)
    no = float(overrides.get("noise_overlay",
                             ctx.draw_rng("noise_overlay").uniform(0.0, 0.10)))
    if no > 0.0:
        g = apply_noise_overlay(g, palette, rng, no)
    bm = overrides.get(
        "border_mode",
        ctx.draw_choice("border_mode", ["free", "free", "free", "always_bg", "always_fg"]),
    )
    g = apply_border(g, palette, rng, bm)
    # Some texture/border/density combinations collapse to a monochrome or
    # square transpose-symmetric input, hiding the operation. Add a tiny
    # deterministic asymmetric cue while staying inside the sampled palette.
    if len({v for row in g for v in row}) < 2:
        g[0][0] = palette[0]
        g[min(h - 1, 1)][w - 1] = palette[1]
    if h == w and h > 1 and all(g[r][c] == g[c][r] for r in range(h) for c in range(w)):
        g[0][1] = palette[0]
        g[1][0] = palette[1]
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify grid is a valid input for the transpose rule."""
    errors = []
    h = len(grid)
    if h == 0:
        errors.append("empty grid")
        return errors
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        errors.append("ragged grid (rows differ in width)")
    if h > 30 or w > 30:
        errors.append(f"grid too large: {h}x{w} > 30x30")
    for r in range(h):
        for c in range(len(grid[r])):
            v = grid[r][c]
            if not (0 <= v <= 9):
                errors.append(f"invalid value {v} at ({r},{c})")
                break
    return errors


def _draw_from_degenerate(name, h, w, palette, rng):
    """Build a degenerate (edge-case) input grid for the transpose rule.

    Caller opts in by passing `texture=<name>` and is responsible for
    capping at most one degenerate per multi-pair puzzle. More than one
    degenerate makes the rule unrecoverable from demonstrations.

    Currently supported names:
      transpose_symmetric  — input g satisfies transpose(g) == g, so
                             output equals input. Forces the model to
                             verify the rule rather than pattern-match.
    """
    g = full_grid(h, w, palette[0])
    if name == "transpose_symmetric":
        # Build a symmetric grid: g[r][c] = g[c][r].
        # Only meaningful when h == w (transpose-symmetric requires square).
        n = min(h, w)
        for r in range(n):
            for c in range(r, n):
                color = rng.choice(palette)
                g[r][c] = color
                if r != c:
                    g[c][r] = color
        return g
    # Unknown degenerate name → safe fallback to a noise grid.
    for r in range(h):
        for c in range(w):
            g[r][c] = rng.choice(palette)
    return g

def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    w=len(grid[0]); msgs=[]
    if any(len(row)!=w for row in grid): msgs.append("grid must be rectangular")
    vals={v for row in grid for v in row}
    if not vals <= set(range(10)): msgs.append("grid values must be ARC colors 0..9")
    if len(vals)<2: msgs.append("transpose demonstrations should use at least two colors")
    return msgs
