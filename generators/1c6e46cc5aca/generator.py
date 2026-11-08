"""Generator for c920a713.

Rule: nested rectangle outlines are canonicalized into concentric output
layers.

Combinatorial axes (8): grid_h/w, layers, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_frames, single_frame, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "1c6e46cc5aca"
VERSION = "3.0.0"  # shape-locked-in (fixed 15x17) + n capped at 3-4 -> output only 5x5/7x7 (out=2 shapes). Output is (2n-1)x(2n-1) for n nested frames; canon uses n=5-7 on varied 12-25 grids. Now vary n=3..6 with dynamically-sized nested frames and varied (non-square) grid -> input size varies, output 5x5..11x11.
TASK_ID = "1c6e46cc5aca"
SUMMARY = (
    "15×17 grid with 3-4 rectangular OUTLINES, each in a distinct "
    "non-zero color. Outlines are nested (largest outermost) so the "
    "interruption-topology sort is well-defined: each outline's "
    "bbox contains the next-smaller outline's bbox. Outline = "
    "rectangle border only (interior is 0 / inner outlines). Rule: "
    "detect each color's outline rectangle. Compute interruption "
    "topology — outline A interrupts B if A's outline crosses any "
    "of B's edge cells. Topologically sort colors so interrupters "
    "come first (outermost). Output: (2n-1) × (2n-1) square where "
    "n = number of colors. Build concentric layers using "
    "distance-to-edge: layer k (0=outermost) gets the k-th color "
    "in the sort. Output cell at (r, c) = colors[min(r, c, "
    "size-1-r, size-1-c)]."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "each non-bg color forms a single rectangular outline (border only)",
    "outlines are nested (each strictly contains the next)",
    "3-4 outlines in distinct non-zero colors",
    "outermost outline fits within 15×17 grid with 1-cell margin",
]

LAYER_KINDS = ("L3", "L4")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_frames", "single_frame", "full_grid")
HELPFUL_TEXTURES = LAYER_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "15", "valid": "15"},
    "grid_w":         {"type": "int", "default": "17", "valid": "17"},
    "layers":         {"type": "choice", "default": "rng helpful",
                       "valid": "3|4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "rng 3..4", "valid": "3..4"},
    "texture":        {"type": "str", "default": "alias for layers",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    tx = overrides.get("texture")
    if tx in LAYER_KINDS:
        layers = int(tx[1])
    elif difficulty == "easy":
        layers = ctx.draw_int("layers", 3, 4)
    elif difficulty == "hard":
        layers = ctx.draw_int("layers", 5, 6)
    else:
        layers = ctx.draw_int("layers", 4, 5)
    colors = ctx.draw_distinct_colors("colors", n=layers, exclude={0})
    # nested frames step 2 inward from a margin; the output is (2n-1)x(2n-1)
    # regardless of grid size, so vary the grid (and make it non-square) to
    # diversify the INPUT while keeping nesting valid. Min dim to fit n frames
    # with innermost >= 2 thick: 4n-1+2*margin.
    margin = ctx.draw_int("margin", 1, 3)
    base = 4 * layers - 1 + 2 * margin
    h = min(30, base + ctx.draw_int("extra_h", 0, 5))
    w = min(30, base + ctx.draw_int("extra_w", 0, 5))
    g = full_grid(h, w, 0)
    for i in range(layers):
        r1 = margin + 2 * i; c1 = margin + 2 * i
        r2 = h - 1 - margin - 2 * i; c2 = w - 1 - margin - 2 * i
        draw_frame(g, r1, c1, r2, c2, colors[i])
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify nested rectangular outlines invariants for 1c6e46cc5aca."""
    errs = []
    h, w = len(grid), len(grid[0])
    flat = [grid[r][c] for r in range(h) for c in range(w)]
    colors = {v for v in flat if v != 0}
    if len(colors) < 3:
        errs.append(f"only {len(colors)} non-zero colors (need >=3 nested outlines)")
    if flat.count(0) == 0:
        errs.append("no background (0) cells")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(15, 17, 0)
    if name == "no_frames":
        return g
    if name == "single_frame":
        draw_frame(g, 1, 1, 13, 15, 3)
        return g
    if name == "full_grid":
        for r in range(15):
            for c in range(17):
                g[r][c] = 5
        return g
    return g
