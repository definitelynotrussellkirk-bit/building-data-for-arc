"""Generator for a740d043.

Rule: bbox of non-1 cells → subgrid → replace 1s with 0.

Combinatorial axes (8): grid_h/w, n_objects, palette_size,
object_shape_kind, object_size_kind, position_bias,
inter_object_margin, decoy_density.
Degenerates: single_object, no_objects, full_grid_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import normalize, rect_cells
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "f8c9982c35c2"
VERSION = "1.2.1"  # ensure normal crops contain bg, avoiding solid-color outputs
TASK_ID = "f8c9982c35c2"
SUMMARY = "1-bg grid with non-1 cells; rule extracts bbox and converts 1s to 0."

INVARIANTS = [
    "background is 1 (rule's bg)",
    ">=2 non-1 cells (so bbox is non-trivial)",
    "no 0 in input (rule writes 0 for bg in output)",
    "all non-1 cells fit in a bbox of size >=2x2",
]

OBJECT_SHAPES = ("vertical_line", "horizontal_line", "rect",
                 "L_shape", "T_shape", "diag", "block_2x2")
SIZE_KINDS = ("small", "medium", "large")
DEGENERATE_TEXTURES = ("single_object", "no_objects", "full_grid_object")
HELPFUL_TEXTURES = OBJECT_SHAPES

AXES = {
    "grid_h":              {"type": "int", "default": "rng 7..14", "valid": "6..18"},
    "grid_w":              {"type": "int", "default": "rng 7..14", "valid": "6..18"},
    "n_objects":           {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":        {"type": "int", "default": "= n_objects",
                            "valid": "1..7"},
    "object_shape_kind":   {"type": "str", "default": "rng helpful",
                            "valid": "vertical_line|horizontal_line|rect|L_shape|T_shape|diag|block_2x2"},
    "object_size_kind":    {"type": "str", "default": "rng small|medium|large",
                            "valid": "small|medium|large"},
    "position_bias":       {"type": "str", "default": "rng spread|center|edge",
                            "valid": "spread|center|edge"},
    "inter_object_margin": {"type": "int", "default": "1", "valid": "1..3"},
    "texture":             {"type": "str", "default": "alias for object_shape_kind",
                            "valid": "vertical_line|horizontal_line|rect|L_shape|T_shape|diag|block_2x2|single_object|no_objects|full_grid_object"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 6, 9, 1, 2
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 13, 18, 3, 5
    else:
        h_lo, h_hi, n_lo, n_hi = 7, 14, 2, 4
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    n_objs = int(overrides.get("n_objects",
                               ctx.draw_int("n_objects", n_lo, n_hi)))
    n_objs = max(1, min(6, n_objs))
    palette = list(ctx.draw_distinct_colors("palette",
                                            n=n_objs,
                                            exclude={0, 1}))
    while len(palette) < n_objs:
        palette.append(palette[0])
    shape_kind = (overrides.get("texture") or
                  overrides.get("object_shape_kind")
                  or ctx.draw_choice("object_shape_kind",
                                     list(OBJECT_SHAPES)))
    # A single vertical or horizontal line creates a one-dimensional bbox, so
    # the canonical crop is a thin strip instead of the advertised non-trivial
    # 2-D extraction.  Keep line textures for multi-object cases, but use a
    # compact 2-D object when this episode only has one object.
    if n_objs == 1 and shape_kind in ("vertical_line", "horizontal_line"):
        shape_kind = "block_2x2"
    size_kind = overrides.get("object_size_kind",
                              ctx.draw_choice("object_size_kind",
                                              list(SIZE_KINDS)))
    margin = int(overrides.get("inter_object_margin", 1))
    g = full_grid(h, w, 1)
    placed = 0
    for i in range(n_objs):
        cells = _shape_cells(shape_kind, size_kind, h, w, rng)
        if place_no_overlap(rng, g, cells, palette[i], bg=1,
                            margin=margin, max_tries=40):
            placed += 1
    if placed < 1:
        cells = normalize(rect_cells(2, 3))
        place_no_overlap(rng, g, cells, palette[0], bg=1,
                         margin=1, max_tries=20)
    # Last-resort guard: ensure the non-1 bbox spans both axes.
    nz = [(r, c) for r in range(h) for c in range(w) if g[r][c] != 1]
    if nz:
        rs = [r for r, _ in nz]; cs = [c for _, c in nz]
        if max(rs) == min(rs):
            rr = min(h - 1, max(0, rs[0] + (1 if rs[0] == 0 else -1)))
            g[rr][cs[0]] = palette[0]
        if max(cs) == min(cs):
            cc = min(w - 1, max(0, cs[0] + (1 if cs[0] == 0 else -1)))
            g[rs[0]][cc] = palette[0]
    _ensure_bbox_has_background(g, bg=1)
    return g


def _bbox_of_non_bg(g, bg=1):
    nz = [(r, c) for r, row in enumerate(g) for c, v in enumerate(row) if v != bg]
    if not nz:
        return None
    return (min(r for r, _ in nz), max(r for r, _ in nz),
            min(c for _, c in nz), max(c for _, c in nz))


def _ensure_bbox_has_background(g, bg=1):
    """Carve a bg cell inside the crop bbox if the crop would be solid."""
    bbox = _bbox_of_non_bg(g, bg=bg)
    if bbox is None:
        return
    r0, r1, c0, c1 = bbox
    if any(g[r][c] == bg for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)):
        return
    candidates = []
    if r1 - r0 >= 2 and c1 - c0 >= 2:
        candidates.extend((r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1))
    candidates.extend((r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    for r, c in candidates:
        old = g[r][c]
        g[r][c] = bg
        if _bbox_of_non_bg(g, bg=bg) == bbox:
            return
        g[r][c] = old


def _shape_cells(kind, size_kind, h, w, rng):
    s_lo, s_hi = {"small": (2, 3), "medium": (3, 4), "large": (4, 5)}[size_kind]
    if kind == "vertical_line":
        n = rng.randint(s_lo, s_hi)
        return normalize([(i, 0) for i in range(n)])
    if kind == "horizontal_line":
        n = rng.randint(s_lo, s_hi)
        return normalize([(0, c) for c in range(n)])
    if kind == "rect":
        rh = rng.randint(s_lo, s_hi); rw = rng.randint(s_lo, s_hi)
        return normalize(rect_cells(rh, rw))
    if kind == "L_shape":
        n = rng.randint(s_lo, s_hi)
        cells = [(0, c) for c in range(n)]
        cells += [(r, 0) for r in range(1, n)]
        return normalize(cells)
    if kind == "T_shape":
        n = rng.randint(s_lo, s_hi)
        cells = [(0, c) for c in range(n)]
        cells += [(r, n // 2) for r in range(1, n)]
        return normalize(cells)
    if kind == "diag":
        n = rng.randint(s_lo, s_hi)
        return normalize([(i, i) for i in range(n)])
    if kind == "block_2x2":
        return normalize([(0, 0), (0, 1), (1, 0), (1, 1)])
    return normalize(rect_cells(2, 3))


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 1)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if name == "single_object":
        for r in range(2, 5):
            g[r][2] = color
        return g
    if name == "no_objects":
        return g
    if name == "full_grid_object":
        for r in range(h):
            for c in range(w):
                g[r][c] = color
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if any(v == 0 for row in grid for v in row):
        errs.append("input should not contain color 0")
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 1]
    if len(nz) < 2:
        errs.append("expected at least two non-background cells")
    if nz:
        rs = [r for r, _ in nz]; cs = [c for _, c in nz]
        if max(rs) == min(rs) or max(cs) == min(cs):
            errs.append("non-1 bounding box should span at least 2 rows and 2 cols")
        bbox_has_bg = any(
            grid[r][c] == 1
            for r in range(min(rs), max(rs) + 1)
            for c in range(min(cs), max(cs) + 1)
        )
        if not bbox_has_bg:
            errs.append("non-1 bounding box contains no bg=1 cell; rule output would be solid")
    return errs
