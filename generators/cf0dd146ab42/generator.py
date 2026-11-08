"""Generator for 14b:m93 — rotate object by top-row code.

Rule: row 0 has K non-zero cells (code = K mod 4). Below row 0, find
the (single) blob, crop it, rotate by code.

Combinatorial axes (8): grid_h, grid_w, palette_kind, k_code,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_code, no_blob, square_blob.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.blobs import grow_blob

GENERATOR_ID = "cf0dd146ab42"
VERSION = "3.0.1"  # WRONG-TASK + dup 42%: rule reads code = VALUE of the first nonzero row-0 cell (1=id,2=rot-cw,3=rot-180,4=rot-ccw,5=flip-lr,6=flip-ud), NOT a count of cells. Gen locked all row-0 markers to colour 2 -> code always 2 (rot-cw only); the 'K mod 4' docstring was wrong. Now place ONE row-0 cell carrying a random code 1..6 (full transform discriminator) + widen blob; asymmetric blobs so transforms differ."
TASK_ID = "cf0dd146ab42"
SUMMARY = (
    "0-bg grid (h~7-9, w~"
    "8-10) with: (a) ROW 0 "
    "holds K NON-ZERO "
    "MARKER cells (K=1..3) "
    "at random distinct "
    "columns in COLOR-2 "
    "(red); (b) BELOW ROW "
    "1 (in rows ≥2) ONE "
    "NON-RECTANGULAR BLOB "
    "of 3-5 cells in a "
    "random color from "
    "{3..8}. The blob is "
    "non-rectangular (bbox "
    "area > cell count) "
    "so rotation changes "
    "its shape. Output "
    "uniq_out=35 (intrinsic "
    "— K mod 4 × few "
    "blobs × colors "
    "normalizes). Rule "
    "(ROTATE BLOB BY K MOD "
    "4): COUNT K = number "
    "of non-zero cells in "
    "row 0. COMPUTE "
    "rotation = K mod 4 "
    "(0=identity, 1=90°CW, "
    "2=180°, 3=270°CW). "
    "CROP the BLOB to its "
    "BBOX. APPLY the "
    "rotation. EMIT the "
    "rotated crop as "
    "output. Net: row-0 "
    "count drives the "
    "blob's rotation."
)

INVARIANTS = [
    "background is 0",
    "the first non-zero cell in row 0 carries the transform code (its VALUE 1..6)",
    "exactly one non-rectangular blob below row 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_code", "no_blob", "square_blob")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "6..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "7..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "k_code":         {"type": "int", "default": "rng 1..6", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "row0_code_blob_below",
                       "valid": "row0_code_blob_below"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_code|no_blob|square_blob"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; row 0 has at least one cell with value 1..6 (the transform code)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    codes_in_row0 = [grid[0][c] for c in range(w) if grid[0][c] in (1, 2, 3, 4, 5, 6)]
    if not codes_in_row0:
        return errs  # degenerate no_code — allow
    # check row 0 has exactly the code + possibly zeros
    bad_row0 = [grid[0][c] for c in range(w) if grid[0][c] not in (0, 1, 2, 3, 4, 5, 6)]
    if bad_row0:
        errs.append(f"row 0 has unexpected values: {bad_row0}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8); w = ctx.draw_int("grid_w", 8, 9)
        b_lo, b_hi = 3, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 9, 12)
        b_lo, b_hi = 4, 6
    else:
        h = ctx.draw_int("grid_h", 7, 10); w = ctx.draw_int("grid_w", 8, 11)
        b_lo, b_hi = 3, 6
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # the rule reads the VALUE of the first nonzero row-0 cell as the transform
    # code (1=id, 2=rot-cw, 3=rot-180, 4=rot-ccw, 5=flip-lr, 6=flip-ud).
    code = int(overrides.get("k_code", ctx.draw_int("k_code", 1, 6)))
    code_col = rng.randint(0, w - 1)
    g[0][code_col] = code
    used = {(0, code_col)}
    for c in range(w):
        used.add((1, c))               # keep blob below row 1 (rule crops rows>=1)
    color = rng.choice([3, 4, 5, 6, 7, 8])
    for _ in range(60):
        cells = grow_blob(rng, h, w, used, rng.randint(b_lo, b_hi), max_attempts=20)
        if cells is None:
            continue
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bb = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if bb == len(cells):           # reject solid rectangles (transform-invariant)
            continue
        for r, c in cells:
            g[r][c] = color
        break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_code":
        # blob without top-row markers → no rotation code
        for r, c in [(3, 3), (4, 3), (4, 4), (5, 4)]: g[r][c] = 4
        return g
    if name == "no_blob":
        # code without blob → nothing to rotate
        g[0][2] = 2; g[0][5] = 2
        return g
    if name == "square_blob":
        # solid 2x2 blob → all rotations identical
        g[0][2] = 2
        for r in range(3, 5):
            for c in range(3, 5):
                g[r][c] = 4
        return g
    return g
