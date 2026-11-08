"""Generator for arc_additional_puzzle_bank_volume9:M59.

Rule: among the color-6 objects, find the one whose translation-normalized
shape is UNIQUE (appears exactly once); output that shape cropped to its
bbox, painted in color 6.

This generator places one UNIQUE shape plus several DUPLICATED shapes
(each stamped >=2 times in the same orientation, each distinct from the
unique), so exactly one shape has count 1.

Combinatorial axes: grid size, the unique shape, the duplicate shapes and
their copy counts, and all positions.
Degenerates: all_same_shape, two_uniques, no_blobs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "bf097cbccabe"
VERSION = "2.1.1"
TASK_ID = "bf097cbccabe"
SUMMARY = (
    "0-bg grid (size varies). Several color-6 (magenta) objects: one UNIQUE "
    "shape plus 1-3 other shapes each duplicated 2-3 times (same "
    "orientation), all placed apart. Rule: output the shape that appears "
    "exactly once, cropped to its bbox, in color 6. The grid size, the "
    "unique shape, the duplicate shapes/counts and all positions vary "
    "freely (was five fixed blobs, ~13 distinct)."
)

INVARIANTS = [
    "all objects are color 6, separated (each its own component)",
    "exactly one translation-normalized shape appears once; all others appear >=2 times",
    "the unique shape differs from every duplicated shape",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_shape", "two_uniques", "no_blobs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "11..22"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "11..24"},
    "n_dup_shapes":   {"type": "int", "default": "varies", "valid": "1..3"},
    "copies":         {"type": "int", "default": "varies", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "blobs_apart", "valid": "blobs_apart"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_same_shape|two_uniques|no_blobs"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return frozenset((r - mr, c - mc) for r, c in cells)


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _place_cluster(occ, cells, h, w):
    cset = set(cells)
    for (r, c) in cells:
        if not (0 <= r < h and 0 <= c < w) or occ[r][c]:
            return False
    for (r, c) in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = r + dr, c + dc
                if (rr, cc) in cset:
                    continue
                if 0 <= rr < h and 0 <= cc < w and occ[rr][cc]:
                    return False
    for (r, c) in cells:
        occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all non-bg cells are color 6; at least two 4-connected components."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    bad = [(r, c) for r in range(h) for c in range(w) if grid[r][c] not in (0, 6)]
    if bad:
        errs.append(f"non-bg cells not all color 6: {len(bad)} offending cells")
    # Count 4-connected components of color 6
    visited = [[False] * w for _ in range(h)]
    n_comp = 0
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 6 and not visited[sr][sc]:
                n_comp += 1
                stack = [(sr, sc)]
                while stack:
                    r, c = stack.pop()
                    if visited[r][c]:
                        continue
                    visited[r][c] = True
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 6 and not visited[nr][nc]:
                            stack.append((nr, nc))
    if n_comp < 2:
        errs.append(f"need ≥2 color-6 components to have a unique shape; found {n_comp}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")

    # output = the UNIQUE color-6 shape's crop, so output diversity = shape-size
    # variety. v1.x drew shapes size 3-5 -> too few distinct polyominoes -> dup 35%.
    # Widen the size range (bigger polyominoes = exponentially more shapes).
    if difficulty == "easy":
        hr, wr, sr, dr_, cr = (11, 14), (11, 15), (3, 5), (1, 1), (2, 2)
    elif difficulty == "hard":
        hr, wr, sr, dr_, cr = (16, 24), (17, 26), (5, 9), (2, 3), (2, 3)
    else:
        hr, wr, sr, dr_, cr = (13, 20), (14, 22), (3, 7), (1, 2), (2, 3)

    for _attempt in range(40):
        unique = _poly(rng, rng.randint(*sr))
        dup_shapes = []
        for _ in range(rng.randint(*dr_)):
            for _t in range(20):
                cand = _poly(rng, rng.randint(*sr))
                if cand != unique and cand not in dup_shapes:
                    dup_shapes.append(cand)
                    break
        if not dup_shapes:
            continue

        # build the list of objects: unique once, each dup shape >=2 copies
        objs = [unique]
        for d in dup_shapes:
            for _ in range(rng.randint(*cr)):
                objs.append(d)
        rng.shuffle(objs)

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = True
        for shape in objs:
            sl = sorted(shape)
            sh = max(r for r, c in sl) + 1; sw = max(c for r, c in sl) + 1
            done = False
            for _t in range(40):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                cells = [(top + r, left + c) for r, c in sl]
                if _place_cluster(occ, cells, h, w):
                    paint_at(g, top, left, sl, 6)
                    done = True
                    break
            if not done:
                placed = False
                break
        if placed:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    g = full_grid(12, 14, 0)
    s = [(0, 0), (1, 0), (1, 1)]
    u = [(0, 0), (0, 1), (1, 0), (1, 1)]
    if name == "all_same_shape":
        for (top, left) in [(1, 1), (1, 6), (6, 1)]:
            paint_at(g, top, left, s, 6)
        return g
    if name == "two_uniques":
        paint_at(g, 1, 1, s, 6)
        paint_at(g, 1, 6, u, 6)
        return g
    if name == "no_blobs":
        return g
    return g
