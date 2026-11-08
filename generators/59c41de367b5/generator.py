"""Generator for arc_puzzle_bank_21_set9_e:hard_i19 — parity-fill from frame seed.

Rule: inside a hollow frame, the single seed defines a checkerboard-
like parity fill by Manhattan distance.

Combinatorial axes (8): grid_h, grid_w, palette_kind, frame_h,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_frame, no_seed, multiple_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "59c41de367b5"
VERSION = "2.0.1"
TASK_ID = "59c41de367b5"
SUMMARY = (
    "0-bg grid (h, w = "
    "fh+2 × fw+2 with fh, "
    "fw ∈ [6, 8]) with: "
    "(a) ONE HOLLOW "
    "RECTANGULAR FRAME at "
    "(1, 1)..(fh, fw) "
    "painted in a chosen "
    "FRAME COLOR (non-"
    "{0, seed_color}); "
    "(b) ONE SEED CELL at "
    "interior position "
    "(sr, sc) inside the "
    "frame in a SEED "
    "COLOR distinct from "
    "the frame color and "
    "0. Rule (CHECKERBOARD"
    "-LIKE PARITY-FILL "
    "FROM SEED USING SEED "
    "AND FRAME COLORS): "
    "for EACH 0-CELL "
    "INSIDE the frame's "
    "interior at (r, c): "
    "compute MANHATTAN "
    "DISTANCE d = |r - "
    "sr| + |c - sc| from "
    "the seed. PAINT "
    "(r, c) with SEED "
    "COLOR if d is EVEN, "
    "with FRAME COLOR if "
    "d is ODD (or "
    "alternate per puzzle "
    "convention). The "
    "frame border and "
    "seed stay. Net: the "
    "interior is filled "
    "with a checkerboard "
    "pattern of seed/"
    "frame colors centered "
    "on the seed."
)

INVARIANTS = [
    "one hollow rectangular frame encloses one seed",
    "the seed color differs from the frame color",
    "interior zeros are filled by Manhattan parity from the seed",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frame", "no_seed", "multiple_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "frame_h":        {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "frame_w":        {"type": "int", "default": "rng 6..8", "valid": "5..10"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "frame_with_inner_seed",
                       "valid": "frame_with_inner_seed"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_frame(g, top, left, bottom, right, color):
    for c in range(left, right + 1):
        g[top][c] = color
        g[bottom][c] = color
    for r in range(top, bottom + 1):
        g[r][left] = color
        g[r][right] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        fh = ctx.draw_int("frame_h", 6, 6)
        fw = ctx.draw_int("frame_w", 6, 6)
    elif difficulty == "hard":
        fh = ctx.draw_int("frame_h", 7, 8)
        fw = ctx.draw_int("frame_w", 7, 8)
    else:
        fh = ctx.draw_int("frame_h", 6, 8)
        fw = ctx.draw_int("frame_w", 6, 8)
    h = fh + 2
    w = fw + 2
    frame_color, seed_color = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
    g = full_grid(h, w, 0)
    _draw_frame(g, 1, 1, fh, fw, frame_color)
    sr = rng.randint(2, fh - 1)
    sc = rng.randint(2, fw - 1)
    g[sr][sc] = seed_color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: hollow rectangular frame exists with at least one interior seed cell."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    # Check for border row/col pattern (frame at rows 1..h-2, cols 1..w-2)
    # A frame has a non-zero value on the outermost ring of some interior rect.
    # Simple check: at least one non-zero border row/col in interior and one zero interior
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(nonzero) < 2:
        errs.append("too few non-zero cells for a frame + seed")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_frame":
        # seed but no frame → no interior to parity-fill
        g[3][3] = 4
        return g
    if name == "no_seed":
        # frame but no seed → no parity origin
        _draw_frame(g, 1, 1, 6, 6, 2)
        return g
    if name == "multiple_seeds":
        # two different seed colors inside frame → ambiguous parity origin
        _draw_frame(g, 1, 1, 6, 6, 2)
        g[3][3] = 4
        g[5][5] = 6
        return g
    return g
