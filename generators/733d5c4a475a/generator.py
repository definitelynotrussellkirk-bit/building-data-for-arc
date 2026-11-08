"""Generator for arc_puzzle_bank_twentyfirst21:M143 — translate shape by 9→9 vector.

Rule: two 9-markers define a translation vector v = (9b.r - 9a.r,
9b.c - 9a.c). Apply v to the colored shape; original shape stays;
9s are erased; out-of-bounds copy cells are silently dropped.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, no_shape, zero_vector.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "733d5c4a475a"
VERSION = "2.0.2"
TASK_ID = "733d5c4a475a"
SUMMARY = (
    "0-bg grid (h, w~6-9) with: (a) EXACTLY TWO "
    "color-9 (maroon) MARKERS at distinct positions "
    "(a, b sorted by row then col) defining a "
    "translation VECTOR v = (b.r - a.r, b.c - a.c) "
    "with v ≠ (0, 0); (b) ONE small connected SHAPE "
    "(3-4 cells from a polyomino bank) in some "
    "non-{0, 9} color, placed in the upper-left "
    "region with at least one cell that translates "
    "in-bounds. Rule: read the vector v from the two "
    "9-markers. For each non-9 shape, PAINT a "
    "TRANSLATED COPY at (cell + v) for each cell in "
    "the shape — using the shape's ORIGINAL color, "
    "skipping cells that fall OOB. The two 9-markers "
    "are ERASED in output (replaced by 0). Original "
    "shape stays + translated copy added. Net: each "
    "shape sprouts a ghost copy displaced by the 9→9 "
    "vector; the 9-markers themselves vanish."
)

# Rivals: 'output is input' refuted by demos. 'preserve 9s in output'
# refuted. 'translate by (a - b)' refuted by demos with sign-clear
# vectors. 'use color 9 for translated copy' refuted. 'translate
# only one shape (ignore others)' refuted by multi-shape demos.
# 'don't preserve original' refuted by demos showing both. 4 demos
# with varied vectors pin the rule.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "exactly two color-9 markers at distinct positions (defining a non-zero vector)",
    "≥1 connected shape in some non-{0, 9} color",
    "at least one translated cell lands in-bounds (so the rule has visible effect)",
    "original shape and translated copy don't overlap each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_shape", "zero_vector")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "shape_with_marker_pair",
                       "valid": "shape_with_marker_pair"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_markers|no_shape|zero_vector"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify marker vector is present and visibly translates the shape."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    nines = sorted((r, c) for r in range(h) for c in range(w) if grid[r][c] == 9)
    shape_cells = {(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 9)}
    if len(nines) != 2:
        errs.append(f"expected exactly 2 color-9 markers, got {len(nines)}")
    if not shape_cells:
        errs.append("no shape cells (non-{0,9}) found")
    if len(nines) == 2 and shape_cells:
        (ar, ac), (br, bc) = nines
        dr, dc = br - ar, bc - ac
        if dr == 0 and dc == 0:
            errs.append("marker vector must be non-zero")
        translated = {(r + dr, c + dc) for r, c in shape_cells
                      if 0 <= r + dr < h and 0 <= c + dc < w}
        if not translated:
            errs.append("marker vector translates every shape cell out of bounds")
        if translated & shape_cells:
            errs.append("translated copy overlaps the original shape")
    return errs


_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 9, 11)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 6, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    color = rng.choice(list(random_palette(rng, 4, exclude={9})))
    shape = rng.choice(_SHAPES)
    sh = max(c[0] for c in shape) + 1
    sw = max(c[1] for c in shape) + 1
    sr = rng.randint(0, max(0, h // 2 - sh))
    sc = rng.randint(0, max(0, w // 2 - sw))
    paint_at(g, sr, sc, shape, color)
    shape_abs = {(sr + dr0, sc + dc0) for dr0, dc0 in shape}
    empty = [(r, c) for r in range(h - 1) for c in range(w) if g[r][c] == 0]
    rng.shuffle(empty)
    for nine_a_r, nine_a_c in empty:
        max_dr = h - nine_a_r - 1
        if max_dr < 1:
            continue
        dr_options = list(range(1, max_dr + 1))
        rng.shuffle(dr_options)
        dc_options = [dc for dc in range(-min(2, nine_a_c), min(2, w - nine_a_c - 1) + 1)
                      if dc != 0]
        rng.shuffle(dc_options)
        for dr in dr_options:
            for dc in dc_options:
                nine_b_r = nine_a_r + dr
                nine_b_c = nine_a_c + dc
                if g[nine_b_r][nine_b_c] != 0:
                    continue
                translated = {(r + dr, c + dc) for r, c in shape_abs
                              if 0 <= r + dr < h and 0 <= c + dc < w}
                if not translated or translated & shape_abs:
                    continue
                g[nine_a_r][nine_a_c] = 9
                g[nine_b_r][nine_b_c] = 9
                return g
    raise RuntimeError("could not place a visible non-overlapping marker vector")


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # Shape but no 9-markers — rule's vector readout fails;
        # translation undefined.
        for r, c in [(2, 2), (2, 3), (3, 2)]: g[r][c] = 4
        return g
    if name == "no_shape":
        # Markers but no shape — rule has nothing to translate.
        g[2][5] = 9; g[5][5] = 9
        return g
    if name == "zero_vector":
        # Both 9-markers at the same position (delta = 0,0) —
        # rule's translation is identity; effect invisible.
        for r, c in [(1, 1), (1, 2), (2, 1)]: g[r][c] = 4
        g[3][5] = 9
        return g
    return g
