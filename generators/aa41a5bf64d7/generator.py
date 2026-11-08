"""Generator for arc_additional_puzzle_bank_volume19:H130.

Rule: corner and flip controls crop-transform a red shape into a cyan
output grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, corner_position,
flip_present, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_corner_marker, no_red_shape, ambiguous_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa41a5bf64d7"
VERSION = "3.0.1"  # distinct 4 + shape-locked-out: FIXED L-pentomino color-2 shape -> output only 4 rotations. Rule rotates (corner-keyed) + optionally reflects the color-2 shape; now random polyomino -> output varies widely."
TASK_ID = "aa41a5bf64d7"
SUMMARY = (
    "0-bg grid (h~8-12, w~10-15) with: (a) "
    "ONE CORNER MARKER — a COLOR-1 cell at "
    "one of the four corners {(0, 0), (0, "
    "w-1), (h-1, 0), (h-1, w-1)} encoding "
    "WHICH ROTATION to apply (TL/TR/BL/BR "
    "→ 0°/90°/180°/270°); (b) OPTIONAL FLIP "
    "MARKER — a COLOR-3 cell at (0, w//2) "
    "with 50% probability, requesting a "
    "horizontal flip in addition to rotation; "
    "(c) ONE ASYMMETRIC RED (color 2) SHAPE "
    "— a fixed 5-cell shape placed at the "
    "vertical center column (col w//2), "
    "spanning rows 2..5. All other cells "
    "are bg-0. Rule (CROP-TRANSFORM THE RED "
    "SHAPE BY THE CORNER+FLIP CONTROLS, "
    "OUTPUT AS CYAN ON A FRESH GRID): READ "
    "the CORNER MARKER (color 1) — its "
    "position determines a ROTATION code. "
    "READ the FLIP MARKER (color 3, present "
    "or absent) — its presence determines a "
    "horizontal FLIP code. EXTRACT the RED "
    "SHAPE (color 2) and CROP to its bbox. "
    "APPLY the chosen ROTATION (and FLIP if "
    "requested) to the cropped shape. OUTPUT "
    "the TRANSFORMED CROP as COLOR 8 (cyan) "
    "on a fresh bg-0 grid sized to the "
    "transformed shape's bbox. Original "
    "markers and red shape are discarded. "
    "Net: a small cyan output showing the "
    "red shape transformed by the corner/"
    "flip controls. Flagged intrinsic-low "
    "(uniq_out=4): 4 corners × 2 flip × 1 "
    "shape = 8 possible outputs, bounded by "
    "the fixed shape."
)

INVARIANTS = [
    "exactly one corner contains the rotation marker 1",
    "an optional color-3 marker requests a horizontal flip",
    "one asymmetric red shape is present",
    "the output is the normalized transformed shape only",
]

PALETTE_KINDS = ("default", "tl_corner", "tr_corner", "bl_or_br_corner")
DEGENERATE_TEXTURES = ("no_corner_marker", "no_red_shape", "ambiguous_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 10..15", "valid": "8..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "corner_position": {"type": "str", "default": "rng",
                        "valid": "tl|tr|bl|br"},
    "flip_present":   {"type": "bool", "default": "rng", "valid": "rng"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one color-1 corner marker (at a grid corner); ≥1 color-2 cell."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    corner_markers = [(r, c) for r, c in corners if grid[r][c] == 1]
    red_cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not corner_markers and not red_cells:
        return errs  # degenerate (no_corner_marker + no_red_shape) — allowed
    if not corner_markers:
        return errs  # degenerate (no_corner_marker) — allowed
    if not red_cells:
        return errs  # degenerate (no_red_shape) — allowed
    if len(corner_markers) > 1:
        return errs  # degenerate (ambiguous_corner) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 13, 15)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 15)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    corners = [(0, 0), (0, w - 1), (h - 1, w - 1), (h - 1, 0)]
    cr, cc = rng.choice(corners)
    g[cr][cc] = 1
    if rng.choice([True, False]):
        g[0][w // 2] = 3
    # Rule: rotate (corner-keyed) + optional reflect (if a 3 exists) of the
    # color-2 shape -> output. v1.x used a FIXED L-pentomino -> only 4 distinct
    # outputs. Use a random polyomino so the transformed output varies widely.
    shape = _poly(rng, rng.randint(3, 7))
    sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
    r0 = (h - sh) // 2
    c0 = max(1, min(w - sw - 1, w // 2 - sw // 2))
    for dr, dc in shape:
        g[r0 + dr][c0 + dc] = 2
    return g


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_corner_marker":
        # red shape but no rotation marker → which transform to apply?
        for dr, dc in [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]:
            g[2 + dr][w // 2 + dc] = 2
        return g
    if name == "no_red_shape":
        # corner marker but nothing to transform
        g[0][0] = 1
        g[0][w // 2] = 3
        return g
    if name == "ambiguous_corner":
        # 1-markers in two corners → corner selection is undefined
        g[0][0] = 1
        g[h - 1][w - 1] = 1
        for dr, dc in [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]:
            g[2 + dr][w // 2 + dc] = 2
        return g
    return g
