"""Generator for ef26cbf6.

Rule: blue cells in yellow-separated sections inherit marker colors
from paired sections.

Combinatorial axes (8): cell_size, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors,
n_markers.
Degenerates: no_separators, no_markers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c2478bfbf97e"
VERSION = "3.0.1"
TASK_ID = "c2478bfbf97e"
SUMMARY = (
    "Grid n × n (n = 2*cell_size + 1, cell_size ∈ {3, 4}) "
    "with: (a) full color-4 (yellow) SEPARATOR row at row "
    "cell_size and full color-4 separator column at col "
    "cell_size — splits grid into 4 SECTIONS; (b) one "
    "MARKER cell in distinct non-{0, 1, 4} color in each "
    "of two sections (top-left, bottom-left). (c) BLUE "
    "(color-1) cells scattered in the right-column "
    "sections. Rule: for each blue cell, look at its "
    "section's row position relative to separator and "
    "inherit the marker color from the same-row "
    "left-column section (top → m1's color, bottom → m2's "
    "color). Output: blue cells replaced by their "
    "section-paired marker color."
)

INVARIANTS = [
    "yellow separator rows and columns divide the grid into equal sections",
    "some sections contain one non-blue non-yellow marker color",
    "blue cells in marker-free sections use a marker from same row or column",
    "marker colors are distinct from each other and from 0, 1, 4",
]

CELL_SIZES = ("c3", "c4")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_separators", "no_markers", "full_grid")
HELPFUL_TEXTURES = CELL_SIZES

AXES = {
    "cell_size":      {"type": "str", "default": "rng helpful",
                       "valid": "|".join(CELL_SIZES)},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "position_bias":  {"type": "str", "default": "fixed", "valid": "fixed"},
    "n_distinct_colors":{"type": "int", "default": "2", "valid": "2"},
    "n_markers":      {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for cell_size",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _ranges(sizes):
    """band sizes -> (list of (lo,hi) ranges, total dim, sep positions)."""
    ranges = []
    seps = []
    pos = 0
    for i, s in enumerate(sizes):
        ranges.append((pos, pos + s - 1))
        pos += s
        if i < len(sizes) - 1:
            seps.append(pos)
            pos += 1
    return ranges, pos, seps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has yellow (4) separator rows/cols; has blue (1) cells; has marker cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    # Full-width yellow rows (separators)
    yellow_rows = [r for r in range(h) if all(grid[r][c] == 4 for c in range(w))]
    yellow_cols = [c for c in range(w) if all(grid[r][c] == 4 for r in range(h))]
    blues = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    markers = [(r, c) for r in range(h) for c in range(w)
               if grid[r][c] not in (0, 1, 4)]
    if not yellow_rows and not yellow_cols:
        errs.append("no full-width/height yellow (4) separator lines found")
    if not blues:
        errs.append("no blue (1) cells found")
    if not markers:
        errs.append("no marker cells (non-{0,1,4}) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    # Rule: full color-4 rows/cols split the grid into a band grid of sections.
    # Some sections carry a single marker (non-{0,1,4}); blue (1) cells inherit
    # the marker from a section in the SAME row-band first, else SAME col-band.
    # mode "rowmark": one col-band is the marker column (1 marker per row-band),
    #   every other section is blue -> resolves via its row-band  (= canonical train0).
    # mode "colmark": one row-band is the marker row -> blue resolves via col-band
    #   (= canonical train1).
    if difficulty == "easy":
        nb_lo, nb_hi, sz_lo, sz_hi = 2, 2, 2, 3
    elif difficulty == "hard":
        nb_lo, nb_hi, sz_lo, sz_hi = 2, 4, 2, 4
    else:
        nb_lo, nb_hi, sz_lo, sz_hi = 2, 3, 2, 4

    mode = rng.choice(["rowmark", "colmark"])
    nbands_r = rng.randint(nb_lo, nb_hi)
    nbands_c = rng.randint(nb_lo, nb_hi)
    if mode == "rowmark":
        nbands_c = max(2, nbands_c)   # need a marker col + >=1 blue col
    else:
        nbands_r = max(2, nbands_r)   # need a marker row + >=1 blue row

    row_sizes = [rng.randint(sz_lo, sz_hi) for _ in range(nbands_r)]
    col_sizes = [rng.randint(sz_lo, sz_hi) for _ in range(nbands_c)]
    row_ranges, h, sep_rows = _ranges(row_sizes)
    col_ranges, w, sep_cols = _ranges(col_sizes)

    g = full_grid(h, w, 0)
    for r in sep_rows:
        for c in range(w):
            g[r][c] = 4
    for c in sep_cols:
        for r in range(h):
            g[r][c] = 4

    n_markers = max(nbands_r, nbands_c)
    markers = list(ctx.draw_distinct_colors("markers", n=n_markers,
                                            exclude={0, 1, 4}))

    def _put_marker(rr, cr, color):
        r = rng.randint(rr[0], rr[1])
        c = rng.randint(cr[0], cr[1])
        g[r][c] = color

    def _put_blue(rr, cr):
        cells = [(r, c) for r in range(rr[0], rr[1] + 1)
                 for c in range(cr[0], cr[1] + 1)]
        k = rng.randint(1, len(cells))
        for (r, c) in rng.sample(cells, k):
            g[r][c] = 1

    if mode == "rowmark":
        j0 = rng.randrange(nbands_c)            # the marker column-band
        for i, rr in enumerate(row_ranges):
            _put_marker(rr, col_ranges[j0], markers[i])
            for j, cr in enumerate(col_ranges):
                if j != j0:
                    _put_blue(rr, cr)
    else:
        i0 = rng.randrange(nbands_r)            # the marker row-band
        for j, cr in enumerate(col_ranges):
            _put_marker(row_ranges[i0], cr, markers[j])
            for i, rr in enumerate(row_ranges):
                if i != i0:
                    _put_blue(rr, cr)
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_separators":
        g[1][1] = 2
        return g
    if name == "no_markers":
        for i in range(7):
            g[3][i] = 4; g[i][3] = 4
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 4
        return g
    return g
