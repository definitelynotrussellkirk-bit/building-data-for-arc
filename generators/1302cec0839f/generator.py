"""Generator for 5b:hard_32 — shape match matrix.

Rule: components sorted by (col, row). Output NxN: cell (r, c) = 8 iff
shape r and shape c have identical normalized binary masks, else 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, all_same_shape, all_distinct_shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1302cec0839f"
VERSION = "2.1.0"  # fix all_background: force >=2 DISTINCT shapes actually placed (n_groups>=2, >=2 ids used) so the matrix always has 0s + 8s instead of a solid-8 all-same-shape board
TASK_ID = "1302cec0839f"
SUMMARY = (
    "0-bg grid with N (2-6) isolated 4-conn components in distinct colors. "
    "Components are partitioned into shape-equivalence groups: members of a "
    "group share an identical normalized binary mask (random polyomino), "
    "groups differ. Rule sorts components by (col,row) and emits an NxN "
    "matrix with 8 where shape r == shape c, else 0. N varies so the "
    "output size and the equivalence pattern both vary widely."
)

INVARIANTS = [
    "background is 0",
    "N (2-6) isolated 4-conn components in distinct colors",
    "components partitioned into shape-equivalence groups (distinct groups have distinct binary masks)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_components", "all_same_shape", "all_distinct_shapes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..16", "valid": "8..22"},
    "grid_w":         {"type": "int", "default": "rng 14..20", "valid": "12..22"},
    "n_components":   {"type": "int", "default": "rng 2..5", "valid": "2..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "= N", "valid": "2..6"},
    "position_bias":  {"type": "str", "default": "n_isolated_components",
                       "valid": "n_isolated_components"},
    "n_distinct_colors": {"type": "int", "default": "= N", "valid": "2..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _place(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _ in range(40):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1): continue
        for dr, dc in shape:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def _norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return tuple(sorted((r - mr, c - mc) for r, c in cells))


def _poly(rng, size, maxd=4):
    """Random connected polyomino (size cells) fitting maxd x maxd, normalized."""
    for _ in range(60):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(list(cells))
            dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            cells.add((r + dr, c + dc))
        n = _norm(cells)
        if max(r for r, _ in n) < maxd and max(c for _, c in n) < maxd:
            return n
    return _norm({(0, 0), (1, 0), (0, 1)})


def _distinct_shapes(rng, k):
    """k distinct normalized polyomino masks (varied sizes)."""
    out = []
    seen = set()
    attempts = 0
    while len(out) < k and attempts < 200:
        attempts += 1
        sz = rng.randint(2, 5)
        s = _poly(rng, sz)
        if s not in seen:
            seen.add(s); out.append(s)
    # pad deterministically if unlucky
    fallback = [_norm({(0, 0)}), _norm({(0, 0), (0, 1)}),
                _norm({(0, 0), (0, 1), (1, 0)}),
                _norm({(0, 0), (0, 1), (1, 0), (1, 1)}),
                _norm({(0, 0), (1, 0), (2, 0)}),
                _norm({(0, 0), (0, 1), (0, 2)})]
    for f in fallback:
        if len(out) >= k:
            break
        if f not in seen:
            seen.add(f); out.append(f)
    return out[:k]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        n_lo, n_hi = 2, 3; h = ctx.draw_int("grid_h", 9, 12); w = ctx.draw_int("grid_w", 12, 15)
    elif difficulty == "hard":
        n_lo, n_hi = 4, 6; h = ctx.draw_int("grid_h", 13, 18); w = ctx.draw_int("grid_w", 16, 22)
    else:
        n_lo, n_hi = 3, 6; h = ctx.draw_int("grid_h", 11, 16); w = ctx.draw_int("grid_w", 14, 20)

    n = ctx.draw_int("n_components", n_lo, n_hi)
    # Random shape-equivalence partition: assign each component a group id.
    # n_groups in 2..n so >=2 distinct shapes exist; duplicates appear when
    # n_groups < n (members share a mask -> off-diagonal 8s).
    n_groups = rng.randint(2, n)
    group_shapes = _distinct_shapes(rng, n_groups)
    group_ids = [rng.randrange(n_groups) for _ in range(n)]
    # Guarantee at least TWO distinct shapes are actually placed; otherwise
    # every shape matches and the matrix is a solid-8 board (degenerate
    # all_background output). With >=2 distinct shapes the matrix always
    # carries both 8 (diagonal) and 0 (the mismatched pair).
    if len(set(group_ids)) < 2:
        group_ids[0], group_ids[1] = 0, 1
    shapes = [group_shapes[gid] for gid in group_ids]

    for _retry in range(8):
        g = full_grid(h, w, 0)
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)
        ok = True
        for color, shape in zip(colors, shapes):
            if not _place(g, rng, list(shape), color):
                ok = False; break
        if ok:
            return g
    # last-resort small fallback: two distinct components
    g = full_grid(max(h, 8), max(w, 8), 0)
    _place(g, rng, [(0, 0), (0, 1), (1, 0)], 4)
    _place(g, rng, [(0, 0), (1, 0), (1, 1), (2, 1)], 6)
    return g


def _components_4conn(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == 0 or seen[r][c]:
                continue
            color = g[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] \
                            and g[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None):
    """Input must hold >=2 isolated components spanning >=2 distinct
    normalized shapes, so the shape-match matrix is never a solid board."""
    issues = []
    comps = _components_4conn(grid)
    if len(comps) < 2:
        issues.append(f"only {len(comps)} components (<2)")
        return issues
    shapes = {_norm(cells) for cells in comps}
    if len(shapes) < 2:
        issues.append("all components share one shape -> solid-8 matrix")
    return issues


def _draw_from_degenerate(name, rng):
    h, w = 9, 14
    g = full_grid(h, w, 0)
    same = [(0, 0), (0, 1), (1, 0)]
    distinct = [(0, 0), (1, 0), (1, 1), (2, 1)]
    if name == "no_components":
        # Empty grid — output matrix is 0x0, ill-defined.
        return g
    if name == "all_same_shape":
        # All 3 components have the same shape — output matrix is all-8.
        for dr, dc in same: g[1 + dr][1 + dc] = 4
        for dr, dc in same: g[1 + dr][6 + dc] = 5
        for dr, dc in same: g[5 + dr][1 + dc] = 6
        return g
    if name == "all_distinct_shapes":
        # All 3 distinct shapes — output matrix is identity (no off-diagonal matches).
        for dr, dc in same: g[1 + dr][1 + dc] = 4
        for dr, dc in distinct: g[1 + dr][6 + dc] = 5
        for dr, dc in [(0, 0), (0, 1), (0, 2), (1, 1)]: g[5 + dr][1 + dc] = 6
        return g
    return g
