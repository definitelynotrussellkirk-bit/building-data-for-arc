"""Generator for arc_puzzle_bank_third_21_bundle:easy_18_mirror_singletons_across_vertical_midline.

Combinatorial axes (8): grid_h, grid_w, palette_kind, markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, markers_in_right, even_width.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "215fb6d6e0a6"
VERSION = "1.2.1"  # require visible off-center, multi-color mirror witnesses
TASK_ID = "215fb6d6e0a6"
SUMMARY = "Colored markers in the left half (and optional center column) are mirrored across the vertical midline. Each non-zero (r, c) gets copied to (r, w-1-c) in the same color. Original markers preserved."

# Rivals: 'output is input' refuted by any demo where markers appear in
# the right half. 'mirror horizontally (180°)' refuted by ≥1 demo where
# the same row is preserved (vertical-only mirror). 'mirror only one
# color' refuted by any demo with ≥2 colors. 'use different color in
# mirror' refuted by any demo (mirror retains source color). 3 demos
# with varied marker positions + colors cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "all nonzero cells are singleton markers",
    "markers are placed on one side or the center column",
    "mirror destinations are initially empty unless the marker is on the center column",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "markers_in_right", "even_width")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 9..13 odd", "valid": "5..23"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "markers":        {"type": "int", "default": "rng 3..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "left_half", "valid": "left_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 11)
        target = ctx.draw_int("markers", 2, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 13, 19)
        target = ctx.draw_int("markers", 5, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 11, 15)
        target = ctx.draw_int("markers", 3, 6)
    if w % 2 == 0:
        w += 1
    g = full_grid(h, w, 0)
    left_cols = list(range((w - 1) // 2))
    choices = [(r, c) for r in range(h) for c in left_cols]
    rng.shuffle(choices)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i, (r, c) in enumerate(choices[:target]):
        g[r][c] = colors[i % len(colors)]
    if h >= 5 and target >= 4:
        g[rng.randrange(h)][w // 2] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 11
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # no markers → mirror is identity, rule has no visible effect
        return g
    if name == "markers_in_right":
        # markers on right half → invariant says they should start on left, ambiguous mirror direction
        for r, c in [(1, 7), (3, 8), (5, 9)]:
            g[r][c] = 4
        return g
    if name == "even_width":
        # even width → no center column, midline runs between two columns, mirror not well-defined
        eg = full_grid(h, 10, 0)
        for r, c in [(1, 1), (3, 3), (5, 0)]:
            eg[r][c] = 5
        return eg
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid is empty or ragged"]
    h, w = len(grid), len(grid[0])
    if w % 2 == 0:
        errs.append("default instance has even width")
    center = w // 2
    markers = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not markers:
        errs.append("no markers to mirror")
    left_markers = [(r, c) for r, c in markers if c < center]
    if not left_markers:
        errs.append("no off-center left-half marker to make the mirror visible")
    marker_colors = {grid[r][c] for r, c in markers}
    if len(markers) >= 2 and len(marker_colors) < 2:
        errs.append("need at least two marker colors to refute recolor/one-color shortcuts")
    for r, c in markers:
        if c > center:
            errs.append("marker starts right of the vertical midline")
            break
        mc = w - 1 - c
        if mc != c and grid[r][mc] != 0:
            errs.append("mirror destination is not empty")
            break
    return errs
