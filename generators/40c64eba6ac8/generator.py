"""Two equal-bbox shapes in colors2/3 produce a Boolean-operation gallery.

Canonical Racket paints cyan union/intersection/A-minus-B/B-minus-A panels.
Only shape_h and shape_w are exact controls (2..6 in every band). Default
sizes increase with difficulty; private degenerate fixtures are diagnostic.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "40c64eba6ac8"
VERSION = "1.3.0"
TASK_ID = "40c64eba6ac8"
SUMMARY = "Two equal-bbox shapes in colors 2 and 3, isolated."

INVARIANTS = [
    "background is 0",
    "exactly two connected components: one in color 2, one in color 3",
    "their bbox dimensions are identical",
]

RULE_HASH = "81233c946d34"
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ("identical_shapes", "disjoint_shapes", "unequal_bboxes")
AXES = {name:{"type":"int","valid":"2..6","default":"band range within 2..6"} for name in ("shape_h","shape_w")}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _full_bbox_mask(cells, sh, sw):
    """The Racket rule crops each object to its ACTUAL object bbox.

    Starting every random walk at (0, 0) only fixes the top/left edges; unless
    the mask also touches the bottom row and right column, the crop fed to the
    boolean operators is smaller than the advertised shape_h/shape_w container.
    """
    return bool(cells) and any(r == sh - 1 for r, _ in cells) and any(c == sw - 1 for _, c in cells)


def _useful_bool_pair(cells_a, cells_b, sh, sw):
    return (
        _full_bbox_mask(cells_a, sh, sw)
        and _full_bbox_mask(cells_b, sh, sw)
        and bool(cells_a & cells_b)
        and bool(cells_a - cells_b)
        and bool(cells_b - cells_a)
    )


def _fallback_masks(sh, sw):
    # Two connected masks with the same full bbox, nonempty intersection, and
    # nonempty one-sided differences, so all four boolean panels are meaningful.
    cells_a = {(0, c) for c in range(sw)} | {(r, 0) for r in range(sh)}
    cells_b = {(0, c) for c in range(sw)} | {(r, sw - 1) for r in range(sh)}
    return cells_a, cells_b


def _paint_pair(sh, sw, cells_a, cells_b):
    h = sh * 2 + 4
    w = sw * 2 + 4
    g = full_grid(h, w, 0)
    ar = 1; ac = 1
    for dr, dc in cells_a:
        g[ar + dr][ac + dc] = 2
    br = sh + 3; bc = sw + 3
    for dr, dc in cells_b:
        g[br + dr][bc + dc] = 3
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if set(overrides)-set(AXES): raise ValueError("unknown override")
    if difficulty not in (None,"easy","medium","hard"): raise ValueError("unknown difficulty")
    if type(sample_index) is not int or sample_index<0: raise ValueError("invalid sample_index")
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    lo,hi={"easy":(2,3),"medium":(3,5),"hard":(4,6),None:(2,6)}[difficulty]
    sh=ctx.draw_int_strict("shape_h",*( (2,6) if "shape_h" in overrides else (lo,hi)))
    sw=ctx.draw_int_strict("shape_w",*( (2,6) if "shape_w" in overrides else (lo,hi)))
    rng = ctx.draw_rng("layout")
    for _ in range(120):
        cells_a = set()
        cells_b = set()
        for cells in (cells_a, cells_b):
            cells.add((0, 0))
            target = rng.randint(max(3, sh * sw // 2), sh * sw)
            attempts = 0
            while len(cells) < target and attempts < 160:
                attempts += 1
                r, c = rng.choice(list(cells))
                for dr, dc in rng.sample([(-1, 0), (1, 0), (0, -1), (0, 1)], 4):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < sh and 0 <= nc < sw and (nr, nc) not in cells:
                        cells.add((nr, nc))
                        if len(cells) >= target:
                            break
        if _useful_bool_pair(cells_a, cells_b, sh, sw):
            return _paint_pair(sh, sw, cells_a, cells_b)
    cells_a, cells_b = _fallback_masks(sh, sw)
    return _paint_pair(sh, sw, cells_a, cells_b)


def _draw_from_degenerate(name, rng):
    sh, sw = 3, 3
    h = sh * 2 + 4
    w = sw * 2 + 4
    g = full_grid(h, w, 0)
    if name == "identical_shapes":
        # cells_a == cells_b → all 4 ops collapse: union == intersect == both,
        # A-B == B-A == empty.
        cells = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)]
        for dr, dc in cells: g[1 + dr][1 + dc] = 2
        for dr, dc in cells: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    if name == "disjoint_shapes":
        # cells_a ∩ cells_b = ∅ — intersection empty, A-B==A, B-A==B.
        for dr, dc in [(0, 0), (1, 0), (2, 0)]: g[1 + dr][1 + dc] = 2
        for dr, dc in [(0, 1), (0, 2), (1, 2)]: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    if name == "unequal_bboxes":
        # A is 3x3, B is 2x2 — equal-bbox precondition fails.
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1)]: g[1 + dr][1 + dc] = 2
        for dr, dc in [(0, 0), (0, 1), (1, 0), (1, 1)]: g[sh + 3 + dr][sw + 3 + dc] = 3
        return g
    return g

def _color_cells(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _norm_mask(cells):
    r1, c1, _, _ = _bbox(cells)
    return {(r - r1, c - c1) for r, c in cells}


def _dims(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return (r2 - r1 + 1, c2 - c1 + 1)


def _connected(cells):
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (r + dr, c + dc)
            if q in cells and q not in seen:
                seen.add(q); todo.append(q)
    return len(seen) == len(cells)


def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    vals = {v for row in grid for v in row}
    extra = vals - {0, 2, 3}
    if extra:
        errs.append(f"unexpected colors {sorted(extra)}")
    cells_a = set(_color_cells(grid, 2))
    cells_b = set(_color_cells(grid, 3))
    if not cells_a or not cells_b:
        return errs + ["missing one of color-2/color-3 shapes"]
    if not _connected(cells_a):
        errs.append("color-2 shape is not one 4-connected component")
    if not _connected(cells_b):
        errs.append("color-3 shape is not one 4-connected component")
    if _dims(cells_a) != _dims(cells_b):
        errs.append(f"cropped object bbox mismatch: {_dims(cells_a)} vs {_dims(cells_b)}")
    ma = _norm_mask(cells_a)
    mb = _norm_mask(cells_b)
    if not (ma & mb):
        errs.append("boolean intersection panel would be empty")
    if not (ma - mb):
        errs.append("A-minus-B panel would be empty")
    if not (mb - ma):
        errs.append("B-minus-A panel would be empty")
    return errs


def observe_overrides(grid):
    sh,sw=_dims(_color_cells(grid,2))
    return {"shape_h":sh,"shape_w":sw}


def rule_mirror(grid):
    if self_check(grid): raise ValueError("invalid boolean operands")
    a=_norm_mask(_color_cells(grid,2));b=_norm_mask(_color_cells(grid,3))
    sh,sw=_dims(_color_cells(grid,2))
    out=full_grid(2*sh+1,2*sw+1,0)
    for cells,rr,cc in ((a|b,0,0),(a&b,0,sw+1),(a-b,sh+1,0),(b-a,sh+1,sw+1)):
        for r,c in cells: out[r+rr][c+cc]=8
    return out
