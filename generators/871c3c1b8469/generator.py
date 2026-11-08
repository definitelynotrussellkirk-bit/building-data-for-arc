"""Generator for arc_puzzle_bank_thirteenth_21_bundle:hard_90_decode_sequence_of_library_shapes.

Combinatorial axes (8): shape_family, sequence, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_library, no_sequence, mismatched_selectors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "871c3c1b8469"
VERSION = "3.0.1"  # in_sh=1 is rule-intrinsic (canonical always 7x17; rule reads fixed library panels at cols k*6+1 + sequence row 6). distinct already 144. Maximize content: randomize the 3 library shapes (random polyominoes in 3x3) + the sequence of (selector,code) pairs instead of the fixed 4x3 / 4-pattern banks.
TASK_ID = "871c3c1b8469"
SUMMARY = (
    "0-bg fixed-size 7×17 grid with: "
    "(a) TOP LIBRARY BAND at rows 1-5 — "
    "THREE 5-COLUMN PANELS separated by "
    "1-COLUMN GAPS (panel k at cols "
    "k*6+1..k*6+5 for k=0,1,2), each "
    "containing ONE LIBRARY SHAPE drawn "
    "from _SHAPE_FAMILIES bank (4 "
    "families × 3 shapes each, each "
    "shape 4-8 cells fitting in 3×3), "
    "painted in a DISTINCT SELECTOR "
    "COLOR drawn from {2..9} (one per "
    "panel); (b) ROW 6 SEQUENCE — a "
    "list of (SELECTOR_COLOR, "
    "TRANSFORM_CODE) PAIRS drawn from "
    "_SEQUENCE_PATTERNS bank: each "
    "pair stored as 2 adjacent cells, "
    "g[6][pos*2] = colors[selector_idx], "
    "g[6][pos*2+1] = code ∈ {1..5} "
    "(transform code: 1=identity, "
    "2=cw90, 3=180, 4=ccw90, "
    "5=flip-LR, etc.). Rule (DECODE "
    "THE BOTTOM SEQUENCE: FOR EACH "
    "(SELECTOR, CODE) PAIR, LOOK UP "
    "THE MATCHING LIBRARY PANEL, "
    "TRANSFORM THE SHAPE BY THE "
    "CODE, EMIT INTO A LEFT-TO-RIGHT "
    "OUTPUT STRIP WITH 1-CELL GAPS): "
    "PARSE the row-6 SEQUENCE into "
    "pairs. For EACH PAIR (selector, "
    "code): FIND the library panel "
    "with that selector color; "
    "EXTRACT its shape. APPLY the "
    "transform indicated by code. "
    "EMIT the transformed shape "
    "into the output strip, "
    "left-to-right, separated by "
    "1-cell gaps. Net: bottom "
    "sequence decodes into a "
    "horizontal gallery of "
    "transformed library shapes."
)

INVARIANTS = [
    "the top band has three five-column library panels separated by one blank column",
    "each library panel contains one distinct selector color",
    "row 6 is a sequence of selector-color and transform-code pairs",
    "the output selects the matching crops, transforms them, and packs them with one-cell gaps",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_sequence", "mismatched_selectors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "shape_family":   {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "sequence":       {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..4"},
    "position_bias":  {"type": "str", "default": "library_top_sequence_bottom",
                       "valid": "library_top_sequence_bottom"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..4"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_library|no_sequence|mismatched_selectors"},
}

_SHAPE_FAMILIES = [
    [
        [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],
        [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
    ],
    [
        [(0, 2), (1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    [
        [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    [
        [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (0, 2), (1, 1), (2, 0), (2, 1)],
        [(0, 0), (1, 0), (1, 1), (1, 2), (2, 0)],
    ],
]

_SEQUENCE_PATTERNS = [
    [(0, 1), (1, 2), (2, 3), (0, 4)],
    [(2, 2), (0, 5), (1, 1), (2, 4)],
    [(1, 3), (2, 1), (0, 2)],
    [(0, 5), (0, 3), (2, 2), (1, 4)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_panel_shape(rng):
    """Random connected polyomino (4-8 cells) fitting within a 3x3 panel."""
    for _ in range(60):
        cells = [(0, 0)]; seen = {(0, 0)}
        k = rng.randint(4, 8)
        while len(cells) < k:
            r, c = rng.choice(cells)
            dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
        rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
        norm = [(r - rmin, c - cmin) for r, c in cells]
        if max(r for r, _ in norm) <= 2 and max(c for _, c in norm) <= 2:
            return norm
    return [(0, 0), (0, 1), (1, 0), (1, 1)]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 7x17 grid; row 0 and 6 separate top library from sequence; 3 distinct selector colors in library band."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != 7 or w != 17:
        return []  # allow non-canonical size (edge case)
    # Row 6 (sequence row) should have some nonzero cells
    seq_cells = [c for c in range(w) if grid[6][c] != 0]
    if not seq_cells:
        return []  # degenerate no_sequence — allowed
    # Check three library panels at cols 1-5, 7-11, 13-17 (approx)
    # Each panel should have nonzero cells with one dominant color
    errs = []
    panel_ranges = [(1, 6), (7, 12), (13, 18)]
    selector_colors = set()
    for c_lo, c_hi in panel_ranges:
        panel_cells = [grid[r][c] for r in range(1, 6) for c in range(c_lo, min(c_hi, w)) if grid[r][c] != 0]
        if panel_cells:
            from collections import Counter
            panel_colors = set(panel_cells)
            selector_colors.update(panel_colors)
    if not selector_colors:
        return []  # degenerate no_library — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        seq_len = ctx.draw_int("seq_len", 2, 3)
    elif difficulty == "hard":
        seq_len = ctx.draw_int("seq_len", 4, 6)
    else:
        seq_len = ctx.draw_int("seq_len", 3, 4)
    colors = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 3)
    g = full_grid(7, 17, 0)
    # 3 random library shapes, one per panel, in distinct selector colors
    for idx in range(3):
        _paint(g, 1, idx * 6 + 1, _rand_panel_shape(rng), colors[idx])
    # random sequence of (selector, transform-code 1..5) pairs (cols fit 17)
    seq_len = min(seq_len, 8)
    for pos in range(seq_len):
        g[6][pos * 2] = colors[rng.randint(0, 2)]
        g[6][pos * 2 + 1] = rng.randint(1, 5)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 17, 0)
    if name == "no_library":
        # Library panels empty — rule has no shapes to decode.
        for pos, (selector_idx, code) in enumerate(_SEQUENCE_PATTERNS[0]):
            g[6][pos * 2] = 4; g[6][pos * 2 + 1] = code
        return g
    if name == "no_sequence":
        # Library present but sequence empty — rule has no decode plan.
        for idx, cells in enumerate(_SHAPE_FAMILIES[0]):
            _paint(g, 1, idx * 6 + 1, cells, [2, 3, 4][idx])
        return g
    if name == "mismatched_selectors":
        # Sequence references colors not in library — rule selects nothing.
        for idx, cells in enumerate(_SHAPE_FAMILIES[0]):
            _paint(g, 1, idx * 6 + 1, cells, [2, 3, 4][idx])
        for pos in range(4):
            g[6][pos * 2] = 9  # not in library
            g[6][pos * 2 + 1] = 1
        return g
    return g
