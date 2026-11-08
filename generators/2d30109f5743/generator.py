"""Generator for 3cb9777539c7:E147 -- extract the largest color-6 shape.

Rule: among the color-6 objects, take the largest (by cell count), crop to
its bounding box, and recolor it to 8. The output is just that shape.

This generator scatters several color-6 polyominoes of distinct sizes so the
largest is unambiguous.

Combinatorial axes: grid size, the shapes/sizes of the color-6 objects and
their positions.
Degenerates: one_shape, two_shapes, single_cell.

NOTE: the output is the cropped largest shape, so its SIZE is bounded by the
shape; distinct INPUTS are large and distinct OUTPUTS track the variety of
the largest shape.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d30109f5743"
VERSION = "2.0.1"  # diversity: distinct-size color-6 shapes -> extract largest (was fixed ~27)
TASK_ID = "2d30109f5743"
SUMMARY = (
    "0-bg grid (size varies) with several color-6 shapes of distinct sizes. "
    "Rule: extract the largest, crop to its bbox, recolor to 8. The grid "
    "size, shape forms/sizes and positions vary freely (was a fixed setup, "
    "~27 distinct). Output is the cropped largest shape, so its size is "
    "bounded; inputs are large."
)

INVARIANTS = [
    "all objects are color 6; sizes are distinct so the largest is unique",
    "the output is the largest object cropped to its bbox, recolored 8",
    "shapes are separated so component counts are unambiguous",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("one_shape", "two_shapes", "single_cell")
HELPFUL_TEXTURES = PALETTE_KINDS

_CARD = [(-1, 0), (1, 0), (0, -1), (0, 1)]

AXES = {
    "grid_h":         {"type": "int", "default": "varies", "valid": "12..24"},
    "grid_w":         {"type": "int", "default": "varies", "valid": "12..24"},
    "n_shapes":       {"type": "int", "default": "varies", "valid": "2..5"},
    "max_size":       {"type": "int", "default": "varies", "valid": "6..14"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered", "valid": "scattered"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|warm|cool|varied|one_shape|two_shapes|single_cell"},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return [(r - mr, c - mc) for r, c in cells]


def _poly(rng, size):
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(list(cells))
        dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _reserve(occ, top, left, sh, sw, h, w, margin=1):
    for r in range(top - margin, top + sh + margin):
        for c in range(left - margin, left + sw + margin):
            if 0 <= r < h and 0 <= c < w and occ[r][c]:
                return False
    for r in range(top, top + sh):
        for c in range(left, left + sw):
            occ[r][c] = True
    return True


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: has color-6 cells with at least 2 distinct 4-connected components."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return []
    h, w = len(grid), len(grid[0])
    sixes = set((r, c) for r in range(h) for c in range(w) if grid[r][c] == 6)
    if not sixes:
        return ["no color-6 cells found"]
    visited = set()
    n_components = 0
    for start in sixes:
        if start in visited:
            continue
        n_components += 1
        queue = [start]
        while queue:
            cell = queue.pop()
            if cell in visited:
                continue
            visited.add(cell)
            r, c = cell
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nb = (r + dr, c + dc)
                if nb in sixes and nb not in visited:
                    queue.append(nb)
    if n_components < 2:
        return [f"expected >=2 color-6 components, got {n_components}"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)

    if difficulty == "easy":
        hr, wr, nr, mx = (12, 15), (12, 16), (2, 3), (6, 9)
    elif difficulty == "hard":
        hr, wr, nr, mx = (18, 24), (18, 24), (4, 5), (11, 14)
    else:
        hr, wr, nr, mx = (14, 19), (14, 20), (3, 4), (8, 12)

    for _attempt in range(40):
        n = rng.randint(*nr)
        big = rng.randint(*mx)
        # n distinct sizes, the largest unique
        sizes = set([big])
        while len(sizes) < n:
            sizes.add(rng.randint(2, big - 1))
        sizes = sorted(sizes, reverse=True)[:n]
        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]
        placed = 0
        for sz in sizes:
            shape = _poly(rng, sz)
            sh = max(r for r, c in shape) + 1; sw = max(c for r, c in shape) + 1
            if sh > h or sw > w:
                continue
            ok = False
            for _t in range(30):
                top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
                if _reserve(occ, top, left, sh, sw, h, w):
                    for (r, c) in shape:
                        g[top + r][left + c] = 6
                    placed += 1; ok = True; break
            if not ok and sz == sizes[0]:
                placed = 0; break    # must place the largest
        if placed >= 2:
            return g

    return g   # fallback (rare)


def _draw_from_degenerate(name, rng):
    h, w = 12, 14
    g = full_grid(h, w, 0)
    for (r, c) in [(2, 2), (2, 3), (3, 2), (3, 3), (4, 2)]:
        g[r][c] = 6
    if name == "one_shape":
        return g
    if name == "single_cell":
        g2 = full_grid(h, w, 0); g2[5][5] = 6
        for (r, c) in [(2, 2), (2, 3), (3, 2)]:
            g2[r][c] = 6
        return g2
    g[8][8] = 6; g[8][9] = 6
    return g
