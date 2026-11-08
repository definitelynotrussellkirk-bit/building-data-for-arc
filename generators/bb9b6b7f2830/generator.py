"""Generator for arc_puzzle_bank_tenth21:H65 — move labelled shapes to marker columns.

Rule: the BOTTOM ROW holds destination MARKERS — cells coloured 1/2/3 at
certain columns. In the upper region, each label digit (1/2/3) sits just
LEFT of a coloured SHAPE (the shape's first cell is within 1-3 cols to the
right of the label). For each label, the rule MOVES that shape down to its
marker's column, BOTTOM-ALIGNED just above the bottom row, painted in the
shape's own colour. The bottom-row markers are kept; everything else clears.

Combinatorial axes: grid size, n_labels (1-3), per-label shape, shape colour,
shape/label positions, marker columns.
Degenerates: no_markers, no_shapes, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bb9b6b7f2830"
# 2.0.0: COMPLETE REWRITE. Old generator was a WRONG-TASK stub (3-4 random
# motifs, "vertical pack" docstring) -> dup-outputs(17%), uniq 0.17 and
# semantically meaningless. The real rule moves each upper label+shape pair
# down to a matching bottom-row marker column. Now builds exactly that.
VERSION = "2.0.1"  # add self_check
TASK_ID = "bb9b6b7f2830"

SUMMARY = (
    "0-bg grid with a bottom row of 1-3 marker cells (colours 1/2/3) at "
    "distinct columns, and for each marker one upper label digit (the same "
    "1/2/3) sitting just left of a coloured shape (colour 4..9). Rule moves "
    "each labelled shape to its marker's column, bottom-aligned above the "
    "bottom row, in the shape's colour; markers stay."
)

INVARIANTS = [
    "background is 0",
    "bottom row has 1-3 distinct-column markers in {1,2,3}",
    "each label digit appears once in the upper region left of a shape",
    "shapes are colours in 4..9 and don't overlap; markers fit their moved shape",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "no_shapes", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..12", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 12..15", "valid": "9..20"},
    "n_labels":       {"type": "int", "default": "rng 1..3", "valid": "1..3"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "= n_labels", "valid": "1..3"},
    "position_bias":  {"type": "str", "default": "labels_top_markers_bottom",
                       "valid": "labels_top_markers_bottom"},
    "n_distinct_colors": {"type": "int", "default": "= n_labels", "valid": "1..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _poly(rng, size, max_dim=3):
    cells = {(0, 0)}; frontier = [(0, 0)]
    while len(cells) < size and frontier:
        r, c = rng.choice(frontier)
        opts = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))]
        rng.shuffle(opts)
        grown = False
        for nr, nc in opts:
            if (nr, nc) in cells:
                continue
            rs = [x for x, _ in cells] + [nr]; cs = [y for _, y in cells] + [nc]
            if max(rs) - min(rs) + 1 > max_dim or max(cs) - min(cs) + 1 > max_dim:
                continue
            cells.add((nr, nc)); frontier.append((nr, nc)); grown = True
            break
        if not grown:
            frontier.remove((r, c))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; bottom row has marker cells in {1,2,3}; shapes in {4..9}."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not nonzero:
        return errs  # degenerate
    bottom_markers = [grid[h - 1][c] for c in range(w) if grid[h - 1][c] in (1, 2, 3)]
    if not bottom_markers:
        return errs  # degenerate no_markers
    shapes = any(grid[r][c] in range(4, 10) for r in range(h) for c in range(w))
    if not shapes:
        errs.append("no shape cells (colors 4-9) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 12, 13)
        n_labels = ctx.draw_int("n_labels", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 15, 20)
        n_labels = ctx.draw_int("n_labels", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 12, 16)
        n_labels = ctx.draw_int("n_labels", 2, 3)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)

    labels = rng.sample([1, 2, 3], n_labels)
    shape_colors = rng.sample([4, 5, 6, 7, 8, 9], n_labels)

    # Assign each label a distinct destination column in the bottom row, with
    # enough room for the moved shape's max width (<=3) to fit.
    marker_cols = rng.sample(range(0, w - 3), n_labels)
    for lab, mc in zip(labels, marker_cols):
        g[h - 1][mc] = lab

    # Place each label tag + its shape in the upper region (rows 0..h-3),
    # in horizontal bands so they stay separated.
    bands = max(1, (h - 2) // 3)
    used = [[False] * w for _ in range(h)]
    for i, (lab, color) in enumerate(zip(labels, shape_colors)):
        shape = _poly(rng, rng.randint(2, 5))
        sw = max(c for _, c in shape) + 1
        sh = max(r for r, _ in shape) + 1
        placed = False
        for _ in range(120):
            band = i % bands
            sr = rng.randint(band * 3, max(band * 3, min(h - 2 - sh, band * 3 + 2)))
            # shape column; leave room on the left for the label + 1..3 gap.
            gap = rng.randint(1, 3)
            sc = rng.randint(gap + 1, w - sw)
            cells = [(sr + dr, sc + dc) for dr, dc in shape]
            # The label must sit in the SAME ROW as the shape's leftmost cell
            # in that row, 'gap' columns to its left (rule scans c+1..c+3).
            # Choose a shape row and the leftmost shape cell in it.
            row_cells = {}
            for dr, dc in shape:
                rr = sr + dr; cc = sc + dc
                row_cells.setdefault(rr, []).append(cc)
            lr = rng.choice(list(row_cells.keys()))
            leftmost = min(row_cells[lr])
            lc = leftmost - gap
            if lc < 0:
                continue
            occ = [(lr, lc)] + cells
            if any(not (0 <= r < h - 1 and 0 <= c < w) for r, c in occ):
                continue
            # No other non-{0} cell between the label and the shape on row lr
            # (so the rule's "first hit" is the shape).
            if any(used[lr][cc] for cc in range(lc + 1, leftmost)):
                continue
            bad = False
            for r, c in occ:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < h and 0 <= cc < w and used[rr][cc]:
                            bad = True
                if bad:
                    break
            if bad:
                continue
            g[lr][lc] = lab
            for r, c in cells:
                g[r][c] = color
            for r, c in occ:
                used[r][c] = True
            placed = True
            break
        if not placed:
            continue
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # upper label+shape but no bottom markers -> no destination
        g[1][1] = 1
        for r, c in [(1, 3), (2, 3), (2, 4)]:
            g[r][c] = 5
        return g
    if name == "no_shapes":
        # bottom markers but no upper label+shape -> nothing to move
        g[h - 1][2] = 1
        g[h - 1][7] = 2
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 5
        return g
    return g
