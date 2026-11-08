"""Generator for arc_additional_puzzle_bank_volume4:H25 — Set difference of normalized 1 vs 2.

Rule: a = normalize(1-cells), b = normalize(2-cells), c = a - b. Crop to
c's bbox; paint to color 3 in fresh grid.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_1_shape, no_2_shape, equal_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b9feca32493"
VERSION = "2.2.0"  # add executable normalized-subset self-check  # keep normalized 2-shape a connected proper subset of the normalized 1-shape
TASK_ID = "8b9feca32493"
SUMMARY = "A 1-shape (5-9 cell random polyomino) and a 2-shape (a proper subset of it) placed apart. Rule: output normalized(1-cells) minus normalized(2-cells), cropped to bbox and painted 3. The 1-shape, the dropped subset and grid size vary."

INVARIANTS = [
    "exactly one connected blob of color 1 and one of color 2",
    "their normalized cell sets differ (1-shape has cells not in 2-shape)",
    "shapes placed in opposite halves of grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_1_shape", "no_2_shape", "equal_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..10", "valid": "7..14"},
    "grid_w":         {"type": "int", "default": "rng 10..13", "valid": "8..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..2"},
    "position_bias":  {"type": "str", "default": "two_shapes_separated",
                       "valid": "two_shapes_separated"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..2"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _is_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    todo = [next(iter(cells))]
    seen = {todo[0]}
    while todo:
        r, c = todo.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if nb in cells and nb not in seen:
                seen.add(nb)
                todo.append(nb)
    return len(seen) == len(cells)


def _preserves_normalization(cells):
    # The canonical rule normalizes both color sets before subtracting. If the
    # 2-shape subset loses every cell from the top row or every cell from the
    # left column, normalization shifts it and it is no longer a subset of the
    # normalized 1-shape.
    return any(r == 0 for r, _ in cells) and any(c == 0 for _, c in cells)


def _connected_proper_subset(shape1, rng):
    """Drop cells while preserving the generator's teaching invariant.

    The previous implementation popped arbitrary cells and then renormalized.
    That often made color-2 disconnected or shifted it out of the normalized
    color-1 frame, contradicting the rule this task is supposed to teach:
    normalized(2-cells) must be a connected proper subset of normalized(1-cells).
    Return None for skinny bridge shapes with no safe deletion so the caller can
    redraw the source shape instead of emitting a mislabeled example.
    """
    shape1 = list(shape1)
    cells = set(shape1)
    target_size = rng.randint(1, max(1, len(shape1) - 2))

    # Randomly peel removable boundary/leaf cells. The shapes are tiny, so many
    # retries are deterministic-fast and avoid raise/drop generation failures.
    for _attempt in range(80):
        keep = set(shape1)
        order = list(shape1)
        rng.shuffle(order)
        for cell in order:
            if len(keep) <= target_size:
                break
            cand = keep - {cell}
            if cand and _is_connected(cand) and _preserves_normalization(cand):
                keep = cand
        if 0 < len(keep) < len(cells) and _is_connected(keep) and _preserves_normalization(keep):
            return sorted(keep)

    for cell in sorted(cells, reverse=True):
        cand = cells - {cell}
        if cand and _is_connected(cand) and _preserves_normalization(cand):
            return sorted(cand)
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9); w = ctx.draw_int("grid_w", 10, 12); t_lo, t_hi = 4, 6
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14); w = ctx.draw_int("grid_w", 13, 16); t_lo, t_hi = 7, 9
    else:
        h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 11, 14); t_lo, t_hi = 5, 8
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    shape1 = shape2 = None
    for _shape_attempt in range(120):
        cand = [(0, 0)]
        target = rng.randint(t_lo, t_hi)
        while len(cand) < target:
            rb, cb = rng.choice(cand)
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            nr, nc = rb + dr, cb + dc
            if (nr, nc) not in cand:
                cand.append((nr, nc))
        minr = min(r for r, _ in cand); minc = min(c for _, c in cand)
        cand = [(r - minr, c - minc) for r, c in cand]
        sub = _connected_proper_subset(cand, rng)
        if sub is not None:
            shape1, shape2 = cand, sub
            break
    if shape1 is None:
        # Guaranteed teachable fallback: normalized shape2 is connected, proper,
        # and still a subset after both shapes are normalized.
        shape1 = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 1)]
        shape2 = [(0, 0), (0, 1), (1, 0), (1, 1)]
    sh1_h = max(r for r, _ in shape1) + 1; sh1_w = max(c for _, c in shape1) + 1
    sh2_h = max(r for r, _ in shape2) + 1; sh2_w = max(c for _, c in shape2) + 1
    r1 = rng.randint(0, max(0, h // 2 - sh1_h))
    c1 = rng.randint(0, max(0, w // 2 - sh1_w))
    r2 = rng.randint(min(h - sh2_h, h // 2), max(h // 2, h - sh2_h))
    c2 = rng.randint(min(w - sh2_w, w // 2), max(w // 2, w - sh2_w))
    for r, c in shape1: g[r1 + r][c1 + c] = 1
    for r, c in shape2: g[r2 + r][c2 + c] = 2
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 12
    g = full_grid(h, w, 0)
    if name == "no_1_shape":
        # Only 2-shape — rule's "a = normalize(1-cells)" is empty;
        # set difference is empty.
        for r, c in [(5, 7), (6, 7), (6, 8)]: g[r][c] = 2
        return g
    if name == "no_2_shape":
        # Only 1-shape — rule's "c = a - b" yields all of a;
        # output reproduces the 1-shape as 3.
        for r, c in [(2, 2), (3, 2), (3, 3), (4, 3)]: g[r][c] = 1
        return g
    if name == "equal_shapes":
        # 1-shape and 2-shape have identical normalized cells —
        # rule's set difference is empty; output undefined.
        for r, c in [(2, 2), (3, 2), (3, 3)]: g[r][c] = 1
        for r, c in [(6, 8), (7, 8), (7, 9)]: g[r][c] = 2
        return g
    return g


def _cells_of(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]


def _components_for(cells):
    cells = set(cells)
    comps = []
    while cells:
        start = cells.pop()
        stack = [start]
        comp = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (r + dr, c + dc)
                if nb in cells:
                    cells.remove(nb)
                    stack.append(nb)
                    comp.append(nb)
        comps.append(comp)
    return comps


def _norm_cells(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    one = _cells_of(grid, 1)
    two = _cells_of(grid, 2)
    if len(_components_for(one)) != 1:
        errors.append("color-1 cells should form exactly one connected blob")
    if len(_components_for(two)) != 1:
        errors.append("color-2 cells should form exactly one connected blob")
    if one and two:
        n1 = _norm_cells(one)
        n2 = _norm_cells(two)
        if not (n2 < n1):
            errors.append("normalized color-2 blob must be a proper subset of normalized color-1 blob")
    return sorted(set(errors))
