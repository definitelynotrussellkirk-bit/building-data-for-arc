"""Generator for arc_puzzle_bank_sixteenth_21_bundle:hard_111_decode_library_sequence_into_strip.

Input is a fixed 5x11 layout: rows 0-2 hold a LIBRARY of three 3x3 panels
at cols 0-2, 4-6, 8-10; row 4 holds four (index, transform-code) tokens at
cols (0,1)/(3,4)/(6,7)/(9,10). Rule: for each token, fetch library panel
index-1, apply the transform code (1-7 = identity / rot-cw / rot-180 /
rot-ccw / flip-lr / flip-ud / transpose), and pack the four transformed
panels into a 3x15 output strip with a 1-col gap.

This generator randomizes the three library panels (distinct-color random
3x3 shapes) and the four tokens.

Combinatorial axes: the library panels (shapes + colors) and the
sequence's four (index, code) tokens.
Degenerates: no_library, no_sequence, mismatched_indices.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "724578f159f2"
VERSION = "3.1.0"  # ensure normal token rows exercise at least one non-identity transform  # diversity: random library panels + random token sequence (was 4 libs x 5 seqs ~17)
TASK_ID = "724578f159f2"
SUMMARY = (
    "Fixed 5x11 grid. Rows 0-2: a LIBRARY of three 3x3 panels (distinct-"
    "color random shapes) at cols 0-2/4-6/8-10. Row 4: four (index 1-3, "
    "transform 1-7) tokens at cols (0,1)/(3,4)/(6,7)/(9,10). Rule: decode "
    "each token (fetch library[index-1], apply the dihedral transform) and "
    "pack the four results into a 3x15 strip. The library shapes/colors and "
    "the four tokens all vary freely (was 4 fixed libraries x 5 fixed "
    "sequences, ~17 distinct)."
)

INVARIANTS = [
    "three 3x3 library panels occupy cols 0-2, 4-6, 8-10",
    "row 4 holds four tokens (index in 1-3, transform code in 1-7)",
    "each library panel is a non-empty single-color shape",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_library", "no_sequence", "mismatched_indices")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "library":        {"type": "str", "default": "random", "valid": "random"},
    "sequence":       {"type": "str", "default": "random", "valid": "random"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "library_panels_then_sequence",
                       "valid": "library_panels_then_sequence"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_library|no_sequence|mismatched_indices"},
}


def _paste(g, panel, top, left):
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            g[top + r][left + c] = value


def _rand_panel(rng, color, ncells):
    positions = rng.sample([(r, c) for r in range(3) for c in range(3)], ncells)
    panel = [[0, 0, 0] for _ in range(3)]
    for (r, c) in positions:
        panel[r][c] = color
    return panel


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    if difficulty == "easy":
        cell_lo, cell_hi, codes = 3, 5, [1, 2, 3, 5, 6]
    elif difficulty == "hard":
        cell_lo, cell_hi, codes = 4, 7, [1, 2, 3, 4, 5, 6, 7]
    else:
        cell_lo, cell_hi, codes = 3, 6, [1, 2, 3, 4, 5, 6, 7]

    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 3)
    library = [_rand_panel(rng, colors[i], rng.randint(cell_lo, cell_hi))
               for i in range(3)]
    sequence = [(rng.randint(1, 3), rng.choice(codes)) for _ in range(4)]
    if all(code == 1 for _idx, code in sequence):
        sequence[rng.randrange(4)] = (sequence[0][0], 2 if 2 in codes else codes[-1])

    g = full_grid(5, 11, 0)
    for left, panel in zip((0, 4, 8), library):
        _paste(g, panel, 0, left)
    for left, (index, code) in zip((0, 3, 6, 9), sequence):
        g[4][left] = index
        g[4][left + 1] = code
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(5, 11, 0)
    lib = [
        [[1, 0, 0], [1, 1, 1], [0, 0, 1]],
        [[0, 2, 0], [2, 2, 2], [0, 2, 0]],
        [[3, 3, 0], [0, 3, 0], [0, 3, 3]],
    ]
    seq = [(1, 1), (2, 2), (3, 3), (1, 4)]
    if name == "no_library":
        for left, (index, code) in zip((0, 3, 6, 9), seq):
            g[4][left] = index; g[4][left + 1] = code
        return g
    if name == "no_sequence":
        for left, panel in zip((0, 4, 8), lib):
            _paste(g, panel, 0, left)
        return g
    if name == "mismatched_indices":
        for left, panel in zip((0, 4, 8), lib):
            _paste(g, panel, 0, left)
        for left, (index, code) in zip((0, 3, 6, 9), [(1, 1), (2, 2), (3, 3), (1, 4)]):
            g[4][left] = index; g[4][left + 1] = code
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if len(grid) != 5 or any(len(row) != 11 for row in grid):
        return ["expected fixed 5x11 input layout"]
    for left in (0, 4, 8):
        vals = [grid[r][left + c] for r in range(3) for c in range(3) if grid[r][left + c] != 0]
        if not vals:
            msgs.append(f"library panel at col {left} is empty")
        elif len(set(vals)) != 1:
            msgs.append(f"library panel at col {left} should be single-color, got {sorted(set(vals))}")
    tokens = []
    for left in (0, 3, 6, 9):
        index, code = grid[4][left], grid[4][left + 1]
        tokens.append((index, code))
        if index not in (1, 2, 3) or code not in (1, 2, 3, 4, 5, 6, 7):
            msgs.append(f"bad token {(index, code)} at row-4 col {left}")
    if all(code == 1 for _index, code in tokens):
        msgs.append("normal sequence should include at least one non-identity transform")
    if any(grid[3][c] != 0 for c in range(11)):
        msgs.append("row 3 should remain a blank separator between library and tokens")
    return msgs
