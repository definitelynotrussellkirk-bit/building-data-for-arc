"""Generator for puzzle `arc_additional_puzzles_21_set21_bundle:E144`
(concept 372eb4bb0894 — `(rule! (crop-to-content g))`).

Rule: crop the grid to the tight bounding box of its non-bg cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, content_fills_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "022240cb671b"
VERSION = "2.1.1"
TASK_ID = "022240cb671b"
SUMMARY = (
    "0-bg grid (h, w~8-16) with 1-3 small "
    "RECTANGULAR OBJECTS (1×1 up to ~h/4 × "
    "w/4) painted in distinct non-zero colors "
    "from a palette of 2-5 colors. Objects are "
    "placed at INTERIOR positions with 1-cell "
    "margin from the grid edges and from each "
    "other, so the non-bg content's bbox is "
    "strictly smaller than the input grid (the "
    "grid is padded with bg). Rule: COMPUTE "
    "the BOUNDING BOX of all NON-BG cells "
    "(rmin..rmax × cmin..cmax). CROP the grid "
    "to exactly that bbox — output is the "
    "rectangular subgrid containing only the "
    "content, with all bg padding outside the "
    "bbox stripped away. Net: input is padded; "
    "output is the tight bbox crop of the "
    "content (smaller dimensions)."
)

# Rivals: 'extract the object' refuted by multi-object/scatter crops
# that keep interior bg. 'output is always a solid block' refuted by
# blob/scatter shapes. 'content never touches the edge' refuted by
# border_touch boards (crop trims only the far sides). 3 demos with
# varied shapes + >=1 border-touching board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "grid has >=1 non-bg cell (an empty grid crashes crop-to-content)",
    "the content bbox is strictly smaller than the grid (crop shrinks)",
]

SHAPE_KINDS = ("rect", "blob", "scatter", "line")
DEGENERATE_TEXTURES = ("content_fills_grid", "single_cell")
HELPFUL_TEXTURES = SHAPE_KINDS + ("border_touch",)

AXES = {
    "grid_h":     {"type": "int", "default": "rng 8..16", "valid": "5..25"},
    "grid_w":     {"type": "int", "default": "rng 8..16", "valid": "5..25"},
    "n_objects":  {"type": "int", "default": "rng 1..3", "valid": "1..5"},
    "shape_kind": {"type": "str", "default": "rng",
                   "valid": "rect|blob|scatter|line",
                   "doc": "Content geometry — crops keep interior bg."},
    "texture":    {"type": "str", "default": "rng helpful",
                   "valid": "rect|blob|scatter|line|border_touch|"
                            "content_fills_grid|single_cell",
                   "doc": "Shape kind, border_touch, or a degenerate name."},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 non-bg cell; content bbox strictly smaller than grid."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("grid is all-background: crop-to-content would crash")
        return errs
    r1 = min(r for r, _ in nz); r2 = max(r for r, _ in nz)
    c1 = min(c for _, c in nz); c2 = max(c for _, c in nz)
    if r1 == 0 and r2 == h - 1 and c1 == 0 and c2 == w - 1:
        errs.append("content fills entire grid: crop is identity (no shrink)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("rect", "blob", "scatter", "line", "border_touch"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
        n = ctx.draw_int("n_objects", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16)
        w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_objects", 2, 3)
    else:
        h = ctx.draw_int("grid_h", 8, 16)
        w = ctx.draw_int("grid_w", 8, 16)
        n = ctx.draw_int("n_objects", 1, 3)
    palette_n = ctx.draw_int("fg_palette", 2, 5)

    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("placement")
    palette = list(ctx.draw_distinct_colors("palette", n=palette_n, exclude={0}))
    kind = texture if texture in SHAPE_KINDS else \
        overrides.get("shape_kind", rng.choice(SHAPE_KINDS))
    placed = 0
    for i in range(n):
        cells = _shape_cells(kind, rng, h, w)
        color = palette[i % len(palette)]
        if place_no_overlap(rng, g, cells, color, bg=0, margin=1, max_tries=30):
            placed += 1
    if placed == 0:
        rr = rng.randint(1, h - 2)
        rc = rng.randint(1, w - 2)
        g[rr][rc] = palette[0]

    if texture == "border_touch":
        # push the content against 1-2 borders: the crop trims only the
        # far sides (content was previously always margin-padded)
        rows = [r for r in range(h) if any(g[r][c] for c in range(w))]
        cols = [c for c in range(w) if any(g[r][c] for r in range(h))]
        dr = -min(rows) if rng.random() < 0.5 else 0
        dc = -min(cols) if (dr == 0 or rng.random() < 0.5) else 0
        if dr or dc:
            ng = full_grid(h, w, 0)
            for r in rows:
                for c in range(w):
                    if g[r][c]:
                        ng[r + dr][c + dc] = g[r][c]
            g = ng
        # crop must still shrink: content never spans BOTH dimensions fully
        rows = [r for r in range(h) if any(g[r][c] for c in range(w))]
        cols = [c for c in range(w) if any(g[r][c] for r in range(h))]
        if len(rows) == h and len(cols) == w:
            g[h - 1] = [0] * w
    return g


def _shape_cells(kind, rng, h, w):
    if kind == "rect":
        rh = rng.randint(1, max(1, h // 4))
        rw = rng.randint(1, max(1, w // 4))
        return normalize(rect_cells(rh, rw))
    if kind == "line":
        k = rng.randint(2, max(2, min(h, w) // 3))
        if rng.random() < 0.5:
            return [(0, c) for c in range(k)]
        return [(r, 0) for r in range(k)]
    if kind == "scatter":
        # loose cells in a small window — the crop keeps the bg between
        win = rng.randint(3, 4)
        n_cells = rng.randint(3, 5)
        spots = [(r, c) for r in range(win) for c in range(win)]
        rng.shuffle(spots)
        return normalize(spots[:n_cells])
    # blob
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(rng.randint(3, 6)):
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc))
            seen.add((r + dr, c + dc))
    return normalize(cells)


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (content always exists;
    the old empty_grid degenerate crashes crop-to-content).

    content_fills_grid — crop is the identity.
    single_cell        — 1x1 output, trivial crop.
    """
    h = ctx.draw_int("grid_h", 8, 12)
    w = ctx.draw_int("grid_w", 8, 12)
    rng = ctx.draw_rng("degenerate_placement")
    g = full_grid(h, w, 0)
    if name == "content_fills_grid":
        base = rng.randint(1, 7)
        for r in range(h):
            for c in range(w):
                g[r][c] = 1 + ((r + c + base) % 3)
        return g
    # single_cell
    g[rng.randrange(h)][rng.randrange(w)] = rng.randint(1, 9)
    return g
