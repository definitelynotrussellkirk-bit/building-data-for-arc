"""Generator for arc_additional_puzzles_21_set14_bundle:H97.

Rule: sort objects by (r1, c1); n×n matrix with 8 if normalized cells
equal, 0 else.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, shape_spread, texture.
Degenerates: all_same_shape, all_different, single_object.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "d91c1bde3d35"
VERSION = "2.1.1"  # n x n shape-congruence matrix; n_objects pinned 3-4 -> distinct 19, out_shapes 3. Widen n 2-5 + n_classes up to 4 -> more output sizes + richer matrices. (Residual dup = small-matrix ceiling.)
TASK_ID = "d91c1bde3d35"
SUMMARY = "N non-touching objects drawn from a few exact-shape classes; output is the n x n shape-equality matrix."

INVARIANTS = [
    "2+ non-touching objects in distinct colours",
    "objects come from >=2 exact-shape classes (distinct cell counts)",
    "same-class objects are identical normalized shapes (so matrix has block structure)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("all_same_shape", "all_different", "single_object")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "7..15"},
    "grid_w":         {"type": "int", "default": "rng 12..14", "valid": "9..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "n_objects":      {"type": "int", "default": "3-4", "valid": "2..5"},
    "n_classes":      {"type": "int", "default": "rng 2..3 exact-shape classes", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|all_same_shape|all_different|single_object"},
}

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nr, nc = r + dr, c + dc
        if (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _place(g, cells, r0, c0, color, occ):
    hh, ww = len(g), len(g[0])
    ac = [(r0 + r, c0 + c) for r, c in cells]
    for (r, c) in ac:
        if not (0 <= r < hh and 0 <= c < ww):
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occ:
                    return False
    for (r, c) in ac:
        g[r][c] = color
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                occ.add((r + dr, c + dc))
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10); w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_objects", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15); w = ctx.draw_int("grid_w", 15, 18)
        n = ctx.draw_int("n_objects", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 13, 16)
        n = ctx.draw_int("n_objects", 3, 5)
    n_classes = ctx.draw_int("n_classes", 2, min(4, n - 1))
    rng = ctx.draw_rng("layout")

    # one base per exact-shape class (distinct cell counts -> never equal across classes);
    # same-class objects are the IDENTICAL shape (same orientation).
    counts = rng.sample(range(2, 6), n_classes)
    bases = [_motif(rng, k) for k in counts]
    assign = list(range(n_classes)) + [rng.randint(0, n_classes - 1)
                                       for _ in range(n - n_classes)]
    rng.shuffle(assign)
    colors = rng.sample(list(range(2, 10)), n)

    for grow in (0, 3, 6):
        g = full_grid(h + grow, w + grow, 0)
        occ = set()
        placed = True
        for i, cls in enumerate(assign):
            cells = bases[cls]
            bh = max(r for r, _ in cells) + 1; bw = max(c for _, c in cells) + 1
            candidates = [(r, c) for r in range(len(g) - bh + 1)
                          for c in range(len(g[0]) - bw + 1)]
            rng.shuffle(candidates)
            if not any(_place(g, cells, r0, c0, colors[i], occ) for r0, c0 in candidates):
                placed = False
                break
        if placed:
            return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the non-degenerate shape-congruence matrix regime.

    The canonical output is an n x n equality matrix over normalized object
    shapes.  Helpful examples should therefore contain multiple objects, at
    least two shape classes, and at least one repeated class to show non-diagonal
    8s; otherwise the task collapses to identity/all-same special cases.
    """
    h, w = len(grid), len(grid[0])
    seen = set()
    objects = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARD:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            norm = tuple(sorted((rr - r0, cc - c0) for rr, cc in cells))
            objects.append((color, norm))

    issues = []
    if len(objects) < 2:
        issues.append(f"only {len(objects)} object(s); need 2+")
    colors = [color for color, _ in objects]
    if len(colors) != len(set(colors)):
        issues.append("object colours are not distinct")
    shapes = [norm for _, norm in objects]
    classes = {norm for norm in shapes}
    if len(classes) < 2:
        issues.append("less than two exact-shape classes")
    counts = {norm: shapes.count(norm) for norm in classes}
    if not any(v >= 2 for v in counts.values()):
        issues.append("no repeated shape class; output would be identity-only")
    return issues


def _draw_from_degenerate(name, rng):
    h, w = 9, 13
    g = full_grid(h, w, 0)
    shape_a = [(0, 0), (1, 0), (2, 0)]
    shape_b = [(0, 0), (0, 1), (0, 2), (1, 1)]
    shape_c = [(0, 0), (0, 1), (1, 0), (1, 1)]
    if name == "all_same_shape":
        # every object normalizes to the same shape → matrix is all-8
        paint_at(g, 1, 1, shape_a, 2)
        paint_at(g, 1, w - 4, shape_a, 3)
        paint_at(g, h - 4, w // 2 - 1, shape_a, 4)
        return g
    if name == "all_different":
        # every object has a unique shape → matrix is identity (only diag is 8)
        paint_at(g, 1, 1, shape_a, 2)
        paint_at(g, 1, w - 4, shape_b, 3)
        paint_at(g, h - 3, w // 2 - 2, shape_c, 4)
        return g
    if name == "single_object":
        # only one object → the matrix degenerates to a 1×1 trivial case
        paint_at(g, h // 2, w // 2, shape_a, 5)
        return g
    return g
