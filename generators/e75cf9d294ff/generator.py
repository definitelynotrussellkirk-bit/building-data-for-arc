"""Generator for arc_puzzle_bank_fourteenth_21_bundle:hard_92_decode_templates_into_2x2_gallery.

Rule: top five rows hold four 5-col template panels separated by blank
columns. Each template has a distinct selector color. Row 6 stores four
selector + transform pairs. Output arranges the decoded transformed
templates as a 2x2 gallery with one-cell gaps.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_program (row 6 empty → no codes to decode);
no_library (template area empty → rule's lookup returns nothing);
identity_transforms (every transform code = 1 → output gallery is
just recolored templates).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e75cf9d294ff"
VERSION = "2.1.0"  # v2.1.0: template panels start at rule columns 0,6,12,18 and rows 0..4; no out-of-bounds or ignored row-5 template cells.
TASK_ID = "e75cf9d294ff"
SUMMARY = "Decode four selector-color and transform-code pairs into a 2x2 transformed template gallery."

INVARIANTS = [
    "the top five rows contain four five-column template panels separated by blank columns",
    "each template panel has a distinct selector color",
    "row 6 stores four selector-color and transform-code pairs",
    "the output arranges the decoded transformed templates as a 2x2 gallery with one-cell gaps",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_program", "no_library", "identity_transforms")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "library":           {"type": "int", "default": "rng 0..3", "valid": "0..3"},
    "program":           {"type": "int", "default": "rng 0..4", "valid": "0..4"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "fixed_4_panel_library",
                          "valid": "fixed_4_panel_library"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_LIBRARIES = [
    [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2)],
        [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
    ],
    [
        [(0, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
        [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
    ],
    [
        [(0, 1), (1, 1), (2, 0), (2, 1), (2, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2)],
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
    ],
    [
        [(0, 0), (1, 0), (2, 0), (3, 0), (3, 1)],
        [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 1), (3, 1)],
        [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1)],
    ],
]

_PROGRAMS = [
    [(0, 1), (1, 2), (2, 3), (3, 4)],
    [(3, 5), (0, 6), (1, 1), (2, 2)],
    [(1, 3), (2, 4), (0, 5), (3, 6)],
    [(2, 2), (3, 1), (2, 5), (0, 4)],
    [(0, 6), (1, 5), (3, 3), (2, 1)],
]


def _paint(g, top, left, cells, color):
    for r, c in cells:
        g[top + r][left + c] = color


def _rand_template(rng):
    """A connected polyomino (4-6 cells) fitting in the 5x5 panel."""
    k = rng.randint(4, 6)
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        t = (r + dr, c + dc)
        nr = cells | {t}
        bh = max(x for x, _ in nr) - min(x for x, _ in nr) + 1
        bw = max(y for _, y in nr) - min(y for _, y in nr) + 1
        if bh <= 5 and bw <= 5:
            cells.add(t)
    mr = min(x for x, _ in cells); mc = min(y for _, y in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], 4)
    templates = [_rand_template(rng) for _ in range(4)]

    g = full_grid(7, 23, 0)
    for idx, (cells, color) in enumerate(zip(templates, colors)):
        _paint(g, 0, idx * 6, cells, color)
    # program: 4 (selector-color, transform-code 1-6) pairs in row 6.
    # Use every selector once and require at least two transform codes with
    # one non-identity, otherwise the decode/transform rule is under-taught.
    selectors = colors[:]
    rng.shuffle(selectors)
    for _ in range(40):
        codes = [rng.randint(1, 6) for _ in range(4)]
        if len(set(codes)) >= 2 and any(code != 1 for code in codes):
            break
    else:
        codes = [1, 2, 3, 4]
    for pos, (selector, code) in enumerate(zip(selectors, codes)):
        g[6][pos * 2] = selector
        g[6][pos * 2 + 1] = code
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 23, 0)
    if name == "no_program":
        # Row 6 empty.
        for idx, (cells, color) in enumerate(zip(_LIBRARIES[0], [3, 4, 5, 6])):
            _paint(g, 0, idx * 6, cells, color)
        return g
    if name == "no_library":
        # No templates in rows 1-4.
        for pos, (selector_idx, code) in enumerate(_PROGRAMS[0]):
            g[6][pos * 2] = [3, 4, 5, 6][selector_idx]
            g[6][pos * 2 + 1] = code
        return g
    if name == "identity_transforms":
        for idx, (cells, color) in enumerate(zip(_LIBRARIES[0], [3, 4, 5, 6])):
            _paint(g, 0, idx * 6, cells, color)
        for pos in range(4):
            g[6][pos * 2] = [3, 4, 5, 6][pos]
            g[6][pos * 2 + 1] = 1   # all identity
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not isinstance(grid, list) or len(grid) != 7 or any(not isinstance(row, list) or len(row) != 23 for row in grid):
        return ["decode-template examples must be exact 7x23 grids"]
    if any(grid[5][c] != 0 for c in range(23)):
        errs.append("row 5 should be blank separator between library and program")
    library_colors = []
    for idx in range(4):
        panel = [row[idx * 6: idx * 6 + 5] for row in grid[:5]]
        vals = {v for row in panel for v in row if v != 0}
        if len(vals) != 1:
            errs.append("each 5x5 library panel should contain exactly one selector color")
        else:
            library_colors.append(next(iter(vals)))
    if len(set(library_colors)) != 4:
        errs.append("the four library selector colors must be distinct")
    pairs = [(grid[6][i], grid[6][i + 1]) for i in range(0, 8, 2)]
    if any(sel == 0 or code == 0 for sel, code in pairs):
        errs.append("row 6 should contain four selector/code pairs")
    if any(sel not in library_colors for sel, _ in pairs):
        errs.append("every program selector should refer to a library color")
    if any(code not in range(1, 7) for _, code in pairs):
        errs.append("transform codes must be 1..6")
    if len({code for _, code in pairs}) < 2:
        errs.append("program should exercise more than one transform code")
    return errs
