"""Generator for arc_puzzle_bank_twelfth_21_bundle:hard_84_decode_sequence_of_transformed_library_shapes.

Rule: rows 0..2 hold sparse index/transform/color code columns; three 4x4
library panels start at row 4. Each program triple selects one panel + a
transform + a target color; output concatenates the transformed recolored
crops with one-cell gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_program (rows 0..2 empty → no codes to decode);
no_library (panel area empty → rule's lookup returns nothing);
identity_transform (every transform code is 1 (identity) → output =
recolored panels unchanged).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "982c2905b543"
VERSION = "2.0.1"  # shape-locked-in is rule-intrinsic (canonical input ALWAYS 8x14: fixed program rows 0..2 + three 4x4 library panels at cols 0,5,10). distinct already 143/144. Maximize the content axes: randomize the 3 library shapes (random 4x4-fitting polyominoes) and the program triples (idx 1..3, transform 1..5) instead of the fixed 4x5 banks.
TASK_ID = "982c2905b543"
SUMMARY = "Decode three indexed library shapes (random polyominoes in 4x4 panels), transform each, recolor, and pack as a centered strip with 1-cell gaps. The 8x14 canvas is rule-intrinsic; library shapes, program triples and colors vary."

INVARIANTS = [
    "rows 0..2 hold sparse index, transform, and output-color code columns",
    "three 4x4 library panels start at row 4 and columns 0, 5, and 10",
    "each code column selects one panel, one transform, and one target color",
    "the output concatenates the transformed recolored crops with one-cell gaps",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_program", "no_library", "identity_transform")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "library":           {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "program":           {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "position_bias":     {"type": "str", "default": "fixed_program_plus_library",
                          "valid": "fixed_program_plus_library"},
    "n_distinct_colors": {"type": "int", "default": "rng 6..6", "valid": "6..6"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_LIBRARIES = [
    [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    ],
    [
        [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
        [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    [
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
    ],
    [
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)],
    ],
]

_PROGRAMS = [
    [(1, 1), (2, 2), (3, 3)],
    [(3, 4), (1, 5), (2, 3)],
    [(2, 1), (2, 4), (1, 2)],
    [(1, 5), (3, 1), (1, 4)],
    [(3, 3), (2, 2), (1, 1)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_panel_shape(rng):
    """Random connected polyomino fitting within a 4x4 library panel."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        k = rng.randint(4, 7)
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
        norm = [(r - rmin, c - cmin) for r, c in cells]
        if max(r for r, _ in norm) <= 3 and max(c for _, c in norm) <= 3:
            return norm
    return [(0, 0), (1, 0), (2, 0), (2, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is 8×14; rows 0-2 have nonzero cells at even cols; row 4 has nonzero cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != 8 or w != 14:
        errs.append(f"expected 8x14 grid; got {h}x{w}")
        return errs
    # Rows 0-2: at least one nonzero in even columns 0,2,4,6,8,10,12
    prog_ok = any(grid[r][c] != 0 for r in range(3) for c in range(0, 14, 2))
    if not prog_ok:
        errs.append("rows 0-2 have no nonzero cells in even columns (program code)")
    # Row 4+: library panels exist
    lib_ok = any(grid[r][c] != 0 for r in range(4, 8) for c in range(14))
    if not lib_ok:
        errs.append("rows 4-7 have no nonzero cells (library panels missing)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # Random library: three distinct 4x4-fitting shapes (the rule selects among
    # them by program index, so they should differ).
    libs = []; seen = set()
    for _ in range(60):
        if len(libs) >= 3:
            break
        s = _rand_panel_shape(rng); key = tuple(sorted(s))
        if key not in seen:
            seen.add(key); libs.append(s)
    while len(libs) < 3:
        libs.append([(0, 0), (1, 0), (2, 0), (2, 1)])
    # Random program: three (panel-index 1..3, transform-code 1..5) triples.
    program = [(rng.randint(1, 3), rng.randint(1, 5)) for _ in range(3)]
    source_colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    output_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)

    g = full_grid(8, 14, 0)
    for col, (idx, code), color in zip((0, 2, 4), program, output_colors):
        g[0][col] = idx
        g[1][col] = code
        g[2][col] = color
    for left, cells, color in zip((0, 5, 10), libs, source_colors):
        _paint(g, 4, left, cells, color)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 14, 0)
    if name == "no_program":
        # Rows 0..2 empty — no codes to decode.
        for left, cells, color in zip((0, 5, 10), _LIBRARIES[0], [3, 4, 5]):
            _paint(g, 4, left, cells, color)
        return g
    if name == "no_library":
        # Library area empty — rule's lookup returns nothing.
        for col, (idx, code), color in zip((0, 2, 4), _PROGRAMS[0], [3, 4, 5]):
            g[0][col] = idx
            g[1][col] = code
            g[2][col] = color
        return g
    if name == "identity_transform":
        # All transform codes = 1 (identity).
        for col, idx, color in zip((0, 2, 4), [1, 2, 3], [3, 4, 5]):
            g[0][col] = idx
            g[1][col] = 1   # all identity
            g[2][col] = color
        for left, cells, color in zip((0, 5, 10), _LIBRARIES[0], [3, 4, 5]):
            _paint(g, 4, left, cells, color)
        return g
    return g
