"""Generator for arc_puzzle_bank_21_set18_s:S18_H6 — fill marker bbox in each lattice cell.

Rule: color-5 lines form a lattice (outer border + internal dividers) that
splits the grid into rectangular CELLS. Each cell holds color-2 MARKER dots.
The rule closes, per row then per column, the span of non-zero cells within
each cell and paints it 8 — i.e. it fills the rook-closure (bounding box) of
each cell's markers with color 8. The 5-lattice is preserved.

The old docstring ("multi-color motifs in panels ... output is a clean pack")
was WRONG: it scattered random colors {2..9} with no 5-lattice, so the rule's
structure was absent and the colour distribution (nc=9) didn't match the
canonical {0,2,5}. This rewrite CONSTRUCTS a color-5 lattice of cells, each
seeded with color-2 markers; only colors {0,2,5} appear.

Combinatorial axes: lattice shape (cell rows/cols), cell sizes, per-cell
marker count/positions, grid size.
Degenerates: no_markers, single_cell, dense_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4ab216be16ea"
VERSION = "3.0.1"  # WRONG-TASK ('multi-color motifs/gallery pack' docstring, nc=9): real rule fills the bbox of color-2 markers inside each color-5 lattice cell with 8. Old gen scattered random colours {2..9} with no 5-lattice (canonical is {0,2,5}). Now builds a 5-lattice of cells each seeded with 2-markers; colours {0,2,5} only.
TASK_ID = "4ab216be16ea"

SUMMARY = (
    "0-bg grid with a color-5 LATTICE (outer border + internal dividers) "
    "splitting it into rectangular CELLS. Each cell holds color-2 MARKER "
    "dots at varied positions. Rule: within each cell, fill the rook-closure "
    "(bounding box) of the markers with color 8, preserving the 5-lattice. "
    "Only colors {0,2,5} appear in the input."
)

INVARIANTS = [
    "background is 0",
    "color-5 lines form a full lattice (border + dividers) of cells",
    "each cell contains >=1 color-2 marker",
    "input colors are exactly a subset of {0,2,5}",
]

PALETTE_KINDS = ("default",)
DEGENERATE_TEXTURES = ("no_markers", "single_cell", "dense_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "derived", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "7..24"},
    "cell_rows":      {"type": "int", "default": "rng 1..2", "valid": "1..2"},
    "cell_cols":      {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "cell_h":         {"type": "int", "default": "rng 3..7", "valid": "3..7"},
    "cell_w":         {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "markers":        {"type": "int", "default": "rng 2..5 per cell", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "default",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _draw_lattice(g, cell_rows, cell_cols, cell_h, cell_w):
    div_rows = [i * (cell_h + 1) for i in range(cell_rows + 1)]
    div_cols = [j * (cell_w + 1) for j in range(cell_cols + 1)]
    for r in div_rows:
        for c in range(len(g[0])):
            g[r][c] = 5
    for c in div_cols:
        for r in range(len(g)):
            g[r][c] = 5
    return div_rows, div_cols


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        cr = ctx.draw_int("cell_rows", 1, 1); cc = ctx.draw_int("cell_cols", 1, 2)
        ch = ctx.draw_int("cell_h", 3, 5); cw = ctx.draw_int("cell_w", 3, 5)
    elif difficulty == "hard":
        cr = ctx.draw_int("cell_rows", 1, 2); cc = ctx.draw_int("cell_cols", 2, 3)
        ch = ctx.draw_int("cell_h", 4, 7); cw = ctx.draw_int("cell_w", 4, 6)
    else:
        cr = ctx.draw_int("cell_rows", 1, 2); cc = ctx.draw_int("cell_cols", 2, 3)
        ch = ctx.draw_int("cell_h", 3, 6); cw = ctx.draw_int("cell_w", 3, 6)
    rng = ctx.draw_rng("layout")

    h = cr * (ch + 1) + 1
    w = cc * (cw + 1) + 1
    g = full_grid(h, w, 0)
    _draw_lattice(g, cr, cc, ch, cw)
    # color-2 markers in each cell (varied count/positions)
    for i in range(cr):
        for j in range(cc):
            top = i * (ch + 1) + 1
            left = j * (cw + 1) + 1
            interior = [(top + rr, left + ccc) for rr in range(ch) for ccc in range(cw)]
            nmk = rng.randint(2, min(5, len(interior)))
            for (r, c) in rng.sample(interior, nmk):
                g[r][c] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify color-5 lattice + color-2 marker invariants."""
    if not grid or not grid[0]:
        return ["empty grid"]
    problems = []
    flat = [v for row in grid for v in row]
    bad_colors = [v for v in flat if v not in (0, 2, 5)]
    if bad_colors:
        problems.append(f"input contains colors outside {{0,2,5}}: {sorted(set(bad_colors))}")
    if 5 not in flat:
        problems.append("no color-5 lattice cells found")
    if 2 not in flat:
        problems.append("no color-2 marker cells found")
    return problems


def _draw_from_degenerate(name, rng):
    rng = rng or __import__("random").Random(0)
    cr, cc, ch, cw = 1, 2, 5, 5
    h = cr * (ch + 1) + 1
    w = cc * (cw + 1) + 1
    g = full_grid(h, w, 0)
    _draw_lattice(g, cr, cc, ch, cw)
    if name == "no_markers":
        return g                                   # lattice only -> no 8s
    if name == "single_cell":
        g2 = full_grid(ch + 2, cw + 2, 0)
        _draw_lattice(g2, 1, 1, ch, cw)
        g2[2][2] = 2; g2[4][4] = 2
        return g2
    if name == "dense_cell":
        for rr in range(1, ch + 1):
            for ccc in range(1, cw + 1):
                g[rr][ccc] = 2                     # left cell fully marked
        return g
    return g
