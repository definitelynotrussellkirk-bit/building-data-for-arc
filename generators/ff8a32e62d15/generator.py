"""Generator for arc_puzzle_bank_sixth_21_bundle:easy_37_replace_components_by_bboxes.

Rule: each component replaced by a cyan bbox-border outline.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, only_singletons, only_2x2.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff8a32e62d15"
VERSION = "2.0.0"
TASK_ID = "ff8a32e62d15"

SUMMARY = "Separated components are replaced by cyan bounding-box borders."

INVARIANTS = [
    "background is 0",
    "components are 4-connected",
    "components are separated by at least one background cell",
    "output ignores original colors and uses 8 for bbox borders",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "only_singletons", "only_2x2")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "7-10 easy / 9-14 med / 13-20 hard", "valid": "5..20"},
    "grid_w":         {"type": "int", "default": "7-10 easy / 9-14 med / 13-20 hard", "valid": "5..20"},
    "components":     {"type": "int", "default": "2-3 easy / 3-6 med / 5-9 hard", "valid": "1..10"},
    "comp_size":      {"type": "int", "default": "rng 2..smax (5/7/8 by difficulty)", "valid": "2..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|warm|cool|varied"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "scattered_components",
                       "valid": "scattered_components"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|no_components|only_singletons|only_2x2"},
}


def _rand_poly(rng, max_h, max_w, size):
    """Random 4-connected polyomino of `size` cells within a max_h x max_w bbox."""
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    cells = [(0, 0)]
    guard = 0
    while len(cells) < size and guard < 200:
        guard += 1
        gr, gc = rng.choice(cells)
        for dr, dc in rng.sample(dirs, 4):
            nr, nc = gr + dr, gc + dc
            if (nr, nc) in cells:
                continue
            rs = [r for r, _ in cells] + [nr]
            cs = [c for _, c in cells] + [nc]
            if (max(rs) - min(rs)) < max(1, max_h) and (max(cs) - min(cs)) < max(1, max_w):
                cells.append((nr, nc))
                break
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target = ctx.draw_int("components", 2, 3)
        smax = 5
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 20)
        w = ctx.draw_int("grid_w", 13, 20)
        target = ctx.draw_int("components", 5, 9)
        smax = 8
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        target = ctx.draw_int("components", 3, 6)
        smax = 7
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Random connected polyominoes of varied size -> varied bbox dims. Output is
    # color-blind cyan bboxes, so bbox variety is exactly what drives output
    # diversity (the old fixed 5-shape bank capped it). bbox+halo reserved so
    # outlines stay distinct.
    occ = [[False] * w for _ in range(h)]

    def bbox_blocked(r0, c0, bh, bw):
        for r in range(r0 - 1, r0 + bh + 1):
            for c in range(c0 - 1, c0 + bw + 1):
                if 0 <= r < h and 0 <= c < w and occ[r][c]:
                    return True
        return False

    placed = 0
    for _ in range(800):
        if placed >= target:
            break
        shape = _rand_poly(rng, min(smax, h - 2), min(smax, w - 2),
                           rng.randint(2, smax))
        bh = max(r for r, _ in shape) + 1
        bw = max(c for _, c in shape) + 1
        if bh > h or bw > w:
            continue
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        if bbox_blocked(r0, c0, bh, bw):
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        for r in range(r0 - 1, r0 + bh + 1):
            for c in range(c0 - 1, c0 + bw + 1):
                if 0 <= r < h and 0 <= c < w:
                    occ[r][c] = True
        placed += 1
    if placed == 0:                       # guarantee at least one component
        g[1][1] = 3; g[1][2] = 3; g[2][1] = 3
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 10
    g = full_grid(h, w, 0)
    if name == "no_components":
        # Empty grid — rule has no components to bbox.
        return g
    if name == "only_singletons":
        # All 1x1 components — rule's bbox-border for a 1-cell
        # component is the cell itself; replacing color → 8 makes
        # the rule a recolor with no shape change.
        g[2][2] = 4; g[2][7] = 6; g[6][3] = 7; g[7][8] = 3
        return g
    if name == "only_2x2":
        # All 2x2 solid components — rule's bbox-border has no
        # interior; rule's "border replaces component" does not
        # introduce any zero cells.
        for r in range(2, 4):
            for c in range(2, 4): g[r][c] = 4
        for r in range(6, 8):
            for c in range(7, 9): g[r][c] = 6
        return g
    return g


def _nonzero_components(g):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and g[nr][nc] != 0):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    msgs = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be a non-empty rectangle"]
    comps = _nonzero_components(grid)
    min_components = 5 if difficulty == "hard" else 2 if difficulty == "easy" else 3
    if len(comps) < min_components:
        msgs.append(f"expected at least {min_components} separated components; found {len(comps)}")
    if any(len(comp) == 1 for comp in comps):
        msgs.append("default examples should not contain singleton components")
    for i, comp in enumerate(comps):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        if max(rs) - min(rs) < 1 and max(cs) - min(cs) < 1:
            msgs.append(f"component {i} has a degenerate bbox")
            break
    return msgs
