"""Generator for arc_puzzle_bank_eighteenth_21_bundle:hard_121_decode_library_with_transform_codes.

Use index and transform rows to decode a sequence of 4x4 library panels.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_program (no codes in rows 5-6 → rule's per-step
output is empty, no panels packed), all_identity (all transform codes
are identity → rule's transform stage is invisible, output equals
selected panels), out_of_range_index (index > 3 → rule's library
lookup fails; output undefined).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9a287cf72db6"
VERSION = "2.1.0"  # 2.1.0: require transform-code diversity in self-check.
TASK_ID = "9a287cf72db6"
SUMMARY = (
    "Fixed 7×14 0-bg grid with: (a) ROWS "
    "0..3 (the LIBRARY): THREE 4×4 "
    "PROTOTYPE PANELS at column offsets "
    "(0, 5, 10), separated by 1-column "
    "gaps. Each panel holds a motif "
    "drawn from one of 4 _LIBRARIES sets "
    "(each set has 3 distinct prototype "
    "shapes), each panel painted in a "
    "DISTINCT non-0 color from {2..9}; "
    "(b) ROW 5 (INDEX ROW): sparse "
    "INDEX CODES placed at specific "
    "columns (drawn from one of 5 "
    "_PROGRAMS layouts), where each "
    "index ∈ {1, 2, 3} selects one of "
    "the 3 prototypes; (c) ROW 6 "
    "(TRANSFORM ROW): TRANSFORM CODES "
    "at the same columns as the index "
    "codes, where each code encodes a "
    "dihedral transform (1=identity, "
    "2=rot90, 3=flip-LR, 4=flip-UD per canonical rule (not rot180). "
    "Rule (DECODE THE PROGRAM "
    "— FOR EACH (INDEX, CODE) PAIR, "
    "SELECT THE INDEXED PROTOTYPE, "
    "APPLY THE TRANSFORM, PACK THE "
    "RESULTS): scan ROW 5 left-to-"
    "right for INDEX CODES. For EACH "
    "column c with g[5][c] = idx and "
    "g[6][c] = code: LOOK UP the idx-"
    "th library prototype panel. APPLY "
    "the transform code to that panel. "
    "PACK the transformed panels "
    "LEFT-TO-RIGHT into an OUTPUT "
    "GRID with 1-cell gaps between, "
    "preserving each prototype's "
    "color. Library rows, index/code "
    "rows, and gaps are discarded. "
    "Net: the output is a sequence of "
    "transformed prototype panels "
    "decoded by the index/transform "
    "program."
)

INVARIANTS = [
    "the first four rows contain three 4x4 prototype panels separated by one blank column",
    "row 5 lists one-based prototype indexes at sparse code positions",
    "row 6 lists transform codes at the same positions",
    "the output is the selected transformed panels packed left-to-right with one-cell gaps",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_program", "all_identity", "out_of_range_index")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "library":        {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "program":        {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "library_plus_program",
                       "valid": "library_plus_program"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "fixed_layout", "valid": "fixed_layout"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|empty_program|all_identity|out_of_range_index"},
}

_LIBRARIES = [
    [
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (1, 2), (2, 1)],
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
    [(1, 1), (2, 2), (3, 3), (1, 4)],
    [(3, 2), (1, 3), (2, 4)],
    [(2, 1), (2, 3), (3, 4), (1, 2)],
    [(1, 4), (3, 1), (1, 2), (2, 3)],
    [(3, 3), (2, 2), (1, 1)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    library = ctx.draw_int("library", 0, len(_LIBRARIES) - 1)
    program = ctx.draw_int("program", 0, len(_PROGRAMS) - 1)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)

    g = full_grid(7, 14, 0)
    for left, cells, color in zip((0, 5, 10), _LIBRARIES[library], colors):
        _paint(g, 0, left, cells, color)

    for c, (index, code) in zip((0, 2, 6, 10), _PROGRAMS[program]):
        g[5][c] = index
        g[6][c] = code
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 14, 0)
    library = 0
    for left, cells, color in zip((0, 5, 10), _LIBRARIES[library], (2, 3, 4)):
        _paint(g, 0, left, cells, color)
    if name == "empty_program":
        # Rows 5-6 empty — rule's per-step output loop is empty;
        # no panels are packed.
        return g
    if name == "all_identity":
        # All transform codes are 1 (identity) — rule's transform
        # stage is invisible; output equals selected panels.
        for c, idx in zip((0, 2, 6, 10), (1, 2, 3, 1)):
            g[5][c] = idx
            g[6][c] = 1
        return g
    if name == "out_of_range_index":
        # Index 5 — rule's library lookup fails (only 3 panels);
        # output undefined for that step.
        for c, (idx, code) in zip((0, 2, 6, 10), [(5, 1), (1, 2), (5, 3), (2, 1)]):
            g[5][c] = idx
            g[6][c] = code
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the decode-library input layout."""
    errs = []
    if not isinstance(grid, list) or len(grid) != 7 or not grid or len(grid[0]) != 14:
        return ["grid must be 7x14"]
    if any(len(row) != 14 for row in grid):
        return ["grid rows must be rectangular width 14"]
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("grid values must be colors 0..9")
    # Three 4x4 library panels separated by blank columns 4 and 9.
    panel_colors = []
    for left in (0, 5, 10):
        vals = {grid[r][c] for r in range(4) for c in range(left, left + 4)} - {0}
        if len(vals) != 1:
            errs.append(f"library panel at col {left} must use exactly one nonzero color")
        else:
            panel_colors.append(next(iter(vals)))
    if len(set(panel_colors)) != 3:
        errs.append("the three library panels must use distinct colors")
    for c in (4, 9):
        if any(grid[r][c] != 0 for r in range(4)):
            errs.append(f"library separator column {c} must stay blank")
    if any(grid[4][c] != 0 for c in range(14)):
        errs.append("row 4 must be the blank separator between library and code rows")
    idx_cols = [c for c, v in enumerate(grid[5]) if v != 0]
    tf_cols = [c for c, v in enumerate(grid[6]) if v != 0]
    if idx_cols != tf_cols:
        errs.append("index row and transform row must have codes in exactly the same columns")
    if len(idx_cols) < 3:
        errs.append("program must contain at least three index/transform pairs")
    bad_indexes = [(c, grid[5][c]) for c in idx_cols if grid[5][c] not in (1, 2, 3)]
    if bad_indexes:
        errs.append(f"index codes must be in 1..3, got {bad_indexes[:3]}")
    bad_tf = [(c, grid[6][c]) for c in tf_cols if grid[6][c] not in (1, 2, 3, 4)]
    if bad_tf:
        errs.append(f"transform codes must be in 1..4, got {bad_tf[:3]}")
    if tf_cols and not any(grid[6][c] != 1 for c in tf_cols):
        errs.append("default program must exercise a non-identity transform")
    if tf_cols and len({grid[6][c] for c in tf_cols}) < 2:
        errs.append("program should include at least two transform codes")
    for r in range(7):
        for c in range(14):
            if r < 4 and c in (4, 9):
                continue
            if r < 4 and any(start <= c < start + 4 for start in (0, 5, 10)):
                continue
            if r in (5, 6) and c in idx_cols:
                continue
            if r == 4:
                continue
            if grid[r][c] != 0:
                errs.append(f"unexpected nonzero outside panels/code slots at {(r, c)}")
                return errs
    return errs
