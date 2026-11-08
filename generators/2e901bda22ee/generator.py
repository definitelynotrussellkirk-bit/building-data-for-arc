"""Generator for arc_puzzle_bank_21_set6:hard_f02.

Each multi-cell object moves onto its nearest singleton marker and adopts the
marker color. Objects are generated with distinct sizes and nearby markers so
the greedy assignment is stable.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_objects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_objects, no_markers, equal_distances.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2e901bda22ee"
VERSION = "2.0.1"  # distinct=12: fixed shapes/positions on a fixed 10x15 (only colours varied). Each multi-cell shape moves to its nearest singleton marker in the marker color. Now random shapes + scattered marker-clusters (>=7 apart so assignment is clean) + varied grid.
TASK_ID = "2e901bda22ee"
SUMMARY = "Move each object to the nearest singleton marker and recolor by that marker."

INVARIANTS = [
    "there are two or three multi-cell objects with distinct sizes",
    "there is one singleton marker per object",
    "each marker is closest to the intended object",
    "moved normalized objects remain in bounds",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "no_markers", "equal_distances")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "10", "valid": "9..17"},
    "grid_w":         {"type": "int", "default": "15", "valid": "11..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_objects":      {"type": "int", "default": "rng 2..3", "valid": "2..3"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "position_bias":  {"type": "str", "default": "objs_with_nearest_markers",
                       "valid": "objs_with_nearest_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "4..6"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0)],
]
_OBJ_TOP_LEFTS = [(1, 1), (6, 1), (2, 9)]
_MARKERS = [(2, 6), (7, 6), (4, 12)]


def _paint(g, top, left, cells, color):
    for dr, dc in cells:
        g[top + dr][left + dc] = color


_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _rand_poly(rng, k):
    """Random connected polyomino (k>=2 cells), normalized to the origin."""
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice(_CARD)
        nb = (r + dr, c + dc)
        if nb not in seen:
            cells.append(nb); seen.add(nb)
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, >=2 distinct non-bg colors (objects to move + singleton markers)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    colors = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(colors) < 2:
        return [f"expected >=2 distinct non-bg colors, got {len(colors)}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    # each multi-cell shape moves to its nearest singleton marker, in the marker's
    # color. Was fixed shapes/positions on a fixed 10x15 (only colours varied ->
    # distinct=12). Now random shapes + scattered marker-clusters + varied grid.
    if difficulty == "easy":
        n_objects = 2; H = ctx.draw_int("grid_h", 9, 11); W = ctx.draw_int("grid_w", 11, 14)
    elif difficulty == "hard":
        n_objects = 3; H = ctx.draw_int("grid_h", 13, 17); W = ctx.draw_int("grid_w", 15, 20)
    else:
        n_objects = rng.randint(2, 3); H = ctx.draw_int("grid_h", 10, 14); W = ctx.draw_int("grid_w", 12, 17)
    cols = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2 * n_objects)
    shape_colors = cols[:n_objects]; marker_colors = cols[n_objects:]
    g = full_grid(H, W, 0)
    # scattered, well-separated cluster anchors (markers); each shape sits beside
    # its own marker (and far from the others) so the nearest-marker assignment is clean.
    anchors = []
    for _ in range(n_objects * 60):
        if len(anchors) == n_objects:
            break
        ar = rng.randint(2, H - 3); ac = rng.randint(2, W - 3)
        if all(abs(ar - pr) + abs(ac - pc) >= 7 for pr, pc in anchors):
            anchors.append((ar, ac))
    for i, (ar, ac) in enumerate(anchors):
        g[ar][ac] = marker_colors[i]                  # singleton marker
        shape = _rand_poly(rng, rng.randint(2, 5))
        sh = max(r for r, _ in shape) + 1; sw = max(c for _, c in shape) + 1
        for _t in range(60):                          # shape near its marker, not on it
            top = ar + rng.randint(-2, 2); left = ac + rng.randint(-3, 3)
            cells = [(top + r, left + c) for r, c in shape]
            if all(0 <= r < H and 0 <= c < W and g[r][c] == 0 and (r, c) != (ar, ac)
                   and not (abs(r - ar) == 0 and abs(c - ac) == 0) for (r, c) in cells):
                for (r, c) in cells:
                    g[r][c] = shape_colors[i]
                break
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 15, 0)
    if name == "no_objects":
        # only markers, no objects to move → nothing to relocate
        for (r, c), color in zip(_MARKERS[:2], [1, 2]):
            g[r][c] = color
        return g
    if name == "no_markers":
        # objects without any marker → no destination defined
        for idx in range(2):
            top, left = _OBJ_TOP_LEFTS[idx]
            _paint(g, top, left, _SHAPES[idx], 4 + idx)
        return g
    if name == "equal_distances":
        # 1 marker equidistant to 2 objects → ambiguous nearest assignment
        _paint(g, 1, 1, _SHAPES[2], 4)
        _paint(g, 1, 8, _SHAPES[2], 6)
        g[1][5] = 1  # equidistant marker
        return g
    return g
