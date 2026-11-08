"""Generator for arc_additional_puzzles_21_set12_bundle:M80.

Rule: sort objects by (color asc, r1 asc, c1 asc); produce N×N matrix
where (r,c) = 8 if obj r matches obj c under any rotation, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: all_unique, single_object, all_identical.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "df3185f767ea"
VERSION = "1.3.0"  # fix all_background: n_classes could be 1 -> all objects rotation-equivalent -> solid-8 matrix. Require >=2 distinct-size shape classes (always rotation-inequivalent) so the matrix carries both 8 and 0.
TASK_ID = "df3185f767ea"
SUMMARY = (
    "N (2-5) small, well-separated, distinct-color shapes drawn from random "
    "rotation-classes (distinct-size base polyominoes, each placed at a random "
    "rotation). Rule: sort objects by (color, r1, c1) and output the N x N matrix "
    "where (i,j)=8 if objects i and j match under any rotation, else 0."
)

INVARIANTS = [
    "2-5 connected non-bg objects (4-connectivity), separated by >=1 cell",
    "distinct colors; objects within a class are rotations of one base",
    "shape classes have distinct cell counts so they are rotation-inequivalent",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_unique", "single_object", "all_identical")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 10..14", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 13..16", "valid": "10..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 3..5", "valid": "2..5"},
    "n_classes":      {"type": "int", "default": "rng 1..min(n,4)", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "= n_objects", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "spread",
                       "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "= n_objects", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _poly(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _rot(cells):
    rot = [(c, -r) for r, c in cells]
    rmin = min(r for r, _ in rot); cmin = min(c for _, c in rot)
    return [(r - rmin, c - cmin) for r, c in rot]


def _free(g, top, left, cells):
    h, w = len(g), len(g[0])
    for dr, dc in cells:
        r, c = top + dr, left + dc
        if not (0 <= r < h and 0 <= c < w):
            return False
        for ar in (r - 1, r, r + 1):
            for ac in (c - 1, c, c + 1):
                if 0 <= ar < h and 0 <= ac < w and g[ar][ac] != 0:
                    return False
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # output is the n x n rotation-equivalence matrix; vary object count + classes
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11); w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_objects", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 16); w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_objects", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 14); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_objects", 3, 5)
    rng = ctx.draw_rng("layout")
    # >=2 distinct-size base shapes -> classes are rotation-inequivalent, so the
    # matrix always has off-diagonal 0s (not the solid-8 all-same-shape board).
    n_classes = ctx.draw_int("n_classes", 2, min(max(n, 2), 4))
    for _attempt in range(40):
        g = full_grid(h, w, 0)
        sizes = rng.sample(range(2, 6), n_classes)
        bases = [_poly(rng, k) for k in sizes]
        assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                           for _ in range(n - n_classes)]
        rng.shuffle(assign)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for cls, col in zip(assign, colors):
            cells = bases[cls]
            for _ in range(rng.randint(0, 3)):   # random rotation within the class
                cells = _rot(cells)
            sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
            placed = False
            for _ in range(120):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _free(g, top, left, cells):
                    paint_at(g, top, left, cells, col)
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if ok:
            return g
    return g   # graceful fallback


def self_check(grid, *, difficulty=None, meta=None):
    """Objects must span >=2 rotation-inequivalent shapes, so the rotation-
    match matrix is never a solid-8 board."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    shapes = set()
    n_obj = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or seen[r][c]:
                continue
            col = grid[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] \
                            and grid[nr][nc] == col:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            n_obj += 1
            rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
            norm = [(r - rmin, c - cmin) for r, c in cells]
            forms = []
            for _ in range(4):
                forms.append(tuple(sorted(norm)))
                norm = _rot(norm)
            shapes.add(min(forms))
    if n_obj < 2:
        return [f"only {n_obj} objects (need >=2)"]
    if len(shapes) < 2:
        return ["all objects are rotation-equivalent -> solid-8 matrix"]
    return []


def _draw_from_degenerate(name, rng):
    h, w = 10, 13
    g = full_grid(h, w, 0)
    if name == "all_unique":
        # all 3 shapes pairwise rotation-inequivalent → off-diagonal matrix all 0
        s1 = [(0, 0), (0, 1), (0, 2)]  # I3
        s2 = [(0, 0), (0, 1), (1, 0), (1, 1)]  # square
        s3 = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]  # L5
        paint_at(g, 1, 1, s1, 4)
        paint_at(g, 1, w - 4, s2, 6)
        paint_at(g, h - 4, 3, s3, 7)
        return g
    if name == "single_object":
        # one object → matrix is 1x1, no comparison possible
        paint_at(g, 3, 5, [(0, 0), (1, 0), (1, 1)], 4)
        return g
    if name == "all_identical":
        # all 3 shapes identical → matrix is all 8 (saturated)
        common = [(0, 0), (1, 0), (1, 1)]
        paint_at(g, 1, 1, common, 4)
        paint_at(g, 1, w - 4, common, 6)
        paint_at(g, h - 4, 3, common, 7)
        return g
    return g
