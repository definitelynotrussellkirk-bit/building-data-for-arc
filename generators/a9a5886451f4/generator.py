"""Generator for arc_puzzle_bank_seventeenth21:M118 — sort objects by size and pack.

Rule: find the non-background objects, normalize each to its bounding-box
origin, sort by descending object area (stable scan-order tie break), and
pack the shapes left-to-right with a one-column gap.

Combinatorial axes (8): grid_h, grid_w, n_objects, object_sizes,
palette_kind, palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_objects, single_object, tied_sizes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9a5886451f4"
VERSION = "2.0.0"  # semantic fix: previous gen made 5-6 9-separated panels, but canonical rule packs ordinary colored objects sorted by size; now generate two separated objects matching the canonical object-count distribution.
TASK_ID = "a9a5886451f4"

SUMMARY = (
    "0-bg grid with two separated colored polyomino objects of distinct "
    "areas. Rule: extract the non-bg objects, normalize each shape to its "
    "bbox origin, sort objects by descending area (scan-order tie break), "
    "and pack the normalized shapes horizontally with one blank column gap."
)

INVARIANTS = [
    "background is 0",
    "exactly two separated non-background objects in normal instances",
    "the two objects have distinct areas, making the size sort unambiguous",
    "no color-9 divider columns or panel structure are present",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_objects", "single_object", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":        {"type": "int", "default": "rng 6..10", "valid": "5..14"},
    "grid_w":        {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "n_objects":     {"type": "int", "default": "2", "valid": "2..3"},
    "object_sizes":  {"type": "str", "default": "distinct 3..6", "valid": "distinct"},
    "palette_kind":  {"type": "str", "default": "rng helpful",
                      "valid": "default|warm|cool|varied"},
    "palette_size":  {"type": "int", "default": "2", "valid": "2..4"},
    "position_bias": {"type": "str", "default": "separated_free",
                      "valid": "separated_free"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..4"},
    "texture":       {"type": "str", "default": "alias for palette_kind",
                      "valid": "default|warm|cool|varied|no_objects|single_object|tied_sizes"},
}


def _rand_poly(rng, k):
    """Random 4-connected polyomino of k cells, normalized to (0, 0)."""
    cells = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        cells.add((r + dr, c + dc))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _free(g, cells, r0, c0):
    h, w = len(g), len(g[0])
    abs_cells = [(r0 + r, c0 + c) for r, c in cells]
    if any(r < 0 or c < 0 or r >= h or c >= w for r, c in abs_cells):
        return False
    rs = [r for r, _ in abs_cells]
    cs = [c for _, c in abs_cells]
    for r in range(max(0, min(rs) - 1), min(h, max(rs) + 2)):
        for c in range(max(0, min(cs) - 1), min(w, max(cs) + 2)):
            if g[r][c] != 0:
                return False
    return True


def _paint(g, cells, r0, c0, color):
    for r, c in cells:
        g[r0 + r][c0 + c] = color


def _place_shape(g, cells, color, rng):
    h, w = len(g), len(g[0])
    _r0, _c0, r1, c1 = _bbox(cells)
    sh, sw = r1 + 1, c1 + 1
    for _ in range(200):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        if _free(g, cells, r0, c0):
            _paint(g, cells, r0, c0, color)
            return True
    return False


def _guaranteed_two_object_grid(h, w, shapes, colors):
    """Deterministic fallback with one object near each side."""
    h = max(h, 7)
    w = max(w, 10)
    g = full_grid(h, w, 0)
    _paint(g, shapes[0], 1, 1, colors[0])
    r2 = min(h - max(r for r, _ in shapes[1]) - 1, 3)
    c2 = w - max(c for _, c in shapes[1]) - 2
    _paint(g, shapes[1], r2, c2, colors[1])
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        sizes = [3, 4]
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 14)
        sizes = sorted(rng.sample([3, 4, 5, 6], 2), reverse=True)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 9, 12)
        sizes = sorted(rng.sample([3, 4, 5, 6], 2), reverse=True)

    colors = list(ctx.draw_distinct_colors("colors", n=2, exclude={0}))
    shapes = [_rand_poly(rng, k) for k in sizes]
    g = full_grid(h, w, 0)
    for cells, color in zip(shapes, colors):
        if not _place_shape(g, cells, color, rng):
            return _guaranteed_two_object_grid(h, w, shapes, colors)
    return g


def _components(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def _full_nine_columns(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    return [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]


def self_check(grid, *, difficulty=None, meta=None):
    """Normal instances are two ordinary objects with distinct sizes."""
    if not grid or not grid[0] or len({len(row) for row in grid}) != 1:
        return ["grid must be a nonempty rectangle"]
    if (meta or {}).get("texture") in DEGENERATE_TEXTURES:
        return []
    msgs = []
    comps = _components(grid)
    if len(comps) != 2:
        msgs.append(f"expected exactly two non-bg objects, found {len(comps)}")
    sizes = [len(cells) for _color, cells in comps]
    if len(set(sizes)) != len(sizes):
        msgs.append(f"object areas must be distinct; got {sorted(sizes, reverse=True)}")
    divs = _full_nine_columns(grid)
    if divs:
        msgs.append(f"unexpected full-height color-9 divider columns: {divs}")
    return msgs


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 9, 0)
    if name == "no_objects":
        return g
    if name == "single_object":
        for r, c in [(1, 1), (2, 1), (2, 2), (3, 2)]:
            g[r][c] = 4
        return g
    if name == "tied_sizes":
        for r, c in [(1, 1), (2, 1), (2, 2)]:
            g[r][c] = 4
        for r, c in [(1, 6), (2, 6), (2, 5)]:
            g[r][c] = 6
        return g
    return g
