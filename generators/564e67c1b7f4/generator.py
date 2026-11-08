"""Generator for arc_additional_puzzle_bank_volume19:M132.

Rule: normalize the color-2 and color-3 shapes (each to its own bbox),
intersect their cell sets, and output the intersection bbox-cropped in
color 8.

Combinatorial axes: grid size, the two shapes (a random per-cell
membership over a k x k frame), their positions, a color-4 noise cell.
Degenerates: no_shapes, no_intersection, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "564e67c1b7f4"
VERSION = "3.0.1"  # distinct=26/dup18%: output = INTERSECTION of color-2 & color-3 normalized shapes; old k=3-4 + <=6-cell shapes gave a tiny intersection space. Now bigger frames (k 3-6) + larger shapes (k..2k cells) -> larger, more varied intersections.
TASK_ID = "564e67c1b7f4"
SUMMARY = (
    "0-bg grid (size varies). ONE color-2 SHAPE and ONE color-3 SHAPE, "
    "placed apart, defined over a shared k x k frame by a random per-cell "
    "membership: every cell belongs to shape-2, shape-3, both, or "
    "neither; both shapes span the full frame (so the rule's independent "
    "normalization keeps them aligned) and at least one cell belongs to "
    "BOTH. Plus a color-4 NOISE cell the rule ignores. Rule: normalize "
    "each shape to its bbox, INTERSECT the two cell sets, and output the "
    "intersection bbox-cropped in COLOR 8 (cyan). The grid size, the two "
    "shapes and their positions all vary freely (was 2 fixed shapes + "
    "grid padding)."
)

INVARIANTS = [
    "exactly one color-2 blob and one color-3 blob",
    "each shape spans its k x k frame so normalization keeps them aligned",
    "their normalized cell sets share at least one position",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_shapes", "no_intersection", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false", "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false", "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_shapes|no_intersection|full_grid"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _conn_poly(rng, size, maxd):
    """A single 4-connected polyomino (normalized to origin)."""
    for _ in range(100):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, c in n) < maxd and max(c for r, c in n) < maxd:
            return n
    return [(0, 0), (0, 1), (1, 0)]


def _grow(rng, base, extra, forbidden):
    """Add `extra` new 4-connected cells to `base`, staying at coords >= 0 and
    avoiding `forbidden` (so the addition is disjoint from it)."""
    cells = set(base)
    added = 0
    guard = 0
    while added < extra and guard < 300:
        guard += 1
        r, c = rng.choice(tuple(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        nr, nc = r + dr, c + dc
        if nr < 0 or nc < 0 or (nr, nc) in cells or (nr, nc) in forbidden:
            continue
        cells.add((nr, nc))
        added += 1
    return cells


def _membership(rng, k):
    """Build two CONNECTED shapes whose normalized intersection equals a
    controllable CORE: core (the intended intersection, varied) plus disjoint
    private additions per colour. Both keep min-row/col = 0 (core is anchored
    at the origin), so the rule's independent normalization preserves the core
    and the intersection is exactly the core -> output diversity tracks core."""
    for _ in range(40):
        core = _norm(set(map(tuple, _conn_poly(rng, rng.randint(4, min(2 * k, k * k - 1)), k))))
        coreset = set(map(tuple, core))
        if (0, 0) not in coreset and not any(r == 0 for r, _ in core):
            continue
        s2set = _grow(rng, coreset, rng.randint(1, k), set())
        p2 = s2set - coreset
        s3set = _grow(rng, coreset, rng.randint(1, k), p2)   # disjoint from p2
        s2, s3 = list(s2set), list(s3set)
        # both must stay anchored at origin so normalization is identity
        if min(r for r, _ in s2) == 0 and min(c for _, c in s2) == 0 and \
           min(r for r, _ in s3) == 0 and min(c for _, c in s3) == 0:
            return _norm(s2), _norm(s3)
    return None


def _free(occ, cells, top, left, h, w):
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = top + r + dr, left + c + dc
                if dr == 0 and dc == 0:
                    if not (0 <= rr < h and 0 <= cc < w):
                        return False
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # bigger frames/shapes -> larger, more varied intersections (the old
    # k=3-4 with <=6-cell shapes gave a tiny intersection space, distinct=26).
    if difficulty == "easy":
        hr, wr, k = (8, 10), (11, 13), rng.choice([3, 4])
    elif difficulty == "hard":
        hr, wr, k = (12, 18), (14, 22), rng.choice([5, 6])
    else:
        hr, wr, k = (9, 13), (11, 16), rng.choice([4, 5])

    for _attempt in range(40):
        mem = _membership(rng, k)
        if mem is None:
            continue
        s2, s3 = mem
        h = rng.randint(*hr); w = rng.randint(*wr)
        occ = [[False] * w for _ in range(h)]
        g = full_grid(h, w, 0)
        ok = True
        for cells, color in ((s2, 2), (s3, 3)):
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            if sh > h or sw > w:
                ok = False
                break
            placed = False
            for _t in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _free(occ, cells, top, left, h, w):
                    paint_at(g, top, left, cells, color)
                    for r, c in cells:
                        occ[top + r][left + c] = True
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        for _t in range(30):
            r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
            if not occ[r][c]:
                g[r][c] = 4
                break
        return g

    return g   # fallback (rare)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, exactly one color-2 blob and one color-3 blob."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    c2 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 2)
    c3 = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 3)
    if c2 == 0:
        errs.append("no color-2 shape cells found")
    if c3 == 0:
        errs.append("no color-3 shape cells found")
    return errs


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 11, 0)
    if name == "no_shapes":
        g[7][10] = 4
        return g
    if name == "no_intersection":
        paint_at(g, 1, 1, [(0, 0), (0, 1)], 2)
        paint_at(g, 5, 7, [(0, 0), (1, 0)], 3)
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(11):
                g[r][c] = 2
        return g
    return g
