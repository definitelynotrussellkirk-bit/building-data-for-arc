"""Generator for ARC task 68b16354.

Rule: `(rule! flip-ud)`.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay, apply_border,
)

GENERATOR_ID = "a6294f07bff6"
VERSION = "1.3.0"  # defect-lint distribution-drift: default band median area ~112 vs
# canonical ~25 (demos are 5x5..7x7 dense noise). Default band now 3..12 per side —
# canonical-like center; the hard band keeps the 10..20 stress sizes.
TASK_ID = "a6294f07bff6"
SUMMARY = (
    "Arbitrary rectangular grid with H≥2 rows and a small palette of "
    "colors. Rule: reverse the row order (flip-ud) — output[r] = "
    "input[H-1-r]. Column order, grid dimensions, and palette are "
    "unchanged. Top and bottom rows must differ so the flip is "
    "visible in the demo."
)

# Rivals: 'output is input' refuted by demos where top row ≠ bottom row.
# 'flip-lr (mirror columns)' refuted by demos where left col ≠ right col
# AND the output preserves columns. 'rotate-180' refuted by demos where
# the leftmost column doesn't reverse — flip-ud reverses rows but
# keeps within-row column order; rot180 reverses both. 'transpose'
# refuted by non-square demos. 3 demos with asymmetric content (one
# row-mirror-asymmetric AND one col-mirror-asymmetric) pin flip-ud.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input is a rectangular grid with at least two rows",
    "top and bottom rows differ so the vertical flip is visible",
    "input is NOT left-right symmetric (so flip-ud is distinguishable from rot180)",
    "colors are sampled from a small palette",
]

# All 9 helpful textures apply (flip-ud is rule-agnostic wrt content).
# Each exposes a different aspect: gradient → axis-direction visible;
# frame → frame preserved; checkerboard → still checker; etc.
HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes",
    "gradient", "checkerboard", "frame", "ring", "plus",
)
DEGENERATE_TEXTURES = ("ud_symmetric",)

AXES = {
    "grid_h":       {"type": "int",   "default": "2-6 easy / 3-12 med / 10-20 hard", "valid": "2..30"},
    "grid_w":       {"type": "int",   "default": "1-6 easy / 3-12 med / 8-20 hard", "valid": "1..30"},
    "palette_size": {"type": "int",   "default": "rng 2..9",  "valid": "2..10"},
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
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 2, 6, 1, 6, 2, 4
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 10, 20, 8, 20, 5, 9
    else:
        h_lo, h_hi, w_lo, w_hi, c_lo, c_hi = 3, 12, 3, 12, 2, 9

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
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

    # Fingerprint parity with canonical: the demos change >=70% of cells under
    # flip-ud (dense asymmetric noise). Symmetric-leaning textures (frame, ring,
    # checkerboard) can flip almost nothing — a near-identity demo teaches
    # nothing. Scramble top-half rows until the flip is substantial.
    def _flip_changed_frac():
        return sum(1 for r in range(h) for c in range(w)
                   if g[r][c] != g[h - 1 - r][c]) / float(h * w)
    guard = 0
    while h >= 2 and _flip_changed_frac() < 0.25 and guard < 10:
        rr = rng.randrange(0, max(1, h // 2))
        g[rr] = [rng.choice(palette) for _ in range(w)]
        guard += 1

    # Invariant: top and bottom rows must differ so the flip is visible.
    if g[0] == g[-1]:
        g[0][0] = palette[0]
        g[-1][0] = palette[1] if len(palette) > 1 else palette[0]
    # Invariant: input must NOT be left-right symmetric, else flip-ud
    # is indistinguishable from rot180. Break LR-symmetry by toggling
    # one cell in the top row if needed.
    if w >= 2 and len(palette) >= 2 and all(row == row[::-1] for row in g):
        target_c = 0 if g[0][0] != palette[1] else 1
        new_color = palette[1] if g[0][target_c] != palette[1] else palette[0]
        g[0][target_c] = new_color
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify flip-ud distinguishable invariants for a6294f07bff6."""
    errs = []
    h, w = len(grid), len(grid[0])
    if h < 2:
        errs.append(f"grid height {h} < 2 (flip-ud needs >=2 rows)")
    colors = {grid[r][c] for r in range(h) for c in range(w)}
    if len(colors) < 2:
        errs.append(f"only {len(colors)} distinct color(s) — flip would be invisible")
    # Top and bottom rows should differ
    if h >= 2 and [grid[0][c] for c in range(w)] == [grid[h-1][c] for c in range(w)]:
        errs.append("top and bottom rows are identical (flip-ud would be invisible)")
    return errs


def _draw_from_degenerate(name, h, w, palette, rng):
    """Edge-case input where the rule's effect is hidden.

    ud_symmetric — every column is a palindrome top-to-bottom, so flip-ud
                   leaves the grid unchanged (output == input).
    """
    g = full_grid(h, w, palette[0])
    if name == "ud_symmetric":
        half = (h + 1) // 2
        for r in range(half):
            row = [rng.choice(palette) for _ in range(w)]
            g[r] = list(row)
            g[h - 1 - r] = list(row)
        return g
    for r in range(h):
        for c in range(w):
            g[r][c] = rng.choice(palette)
    return g
