"""Generator for arc_puzzle_bank_eighteenth21:M121 — translate shape by 1→2 vector.

Rule: a 1-marker and a 2-marker define a translation vector
v = (2.r - 1.r, 2.c - 1.c). Apply v to the third-colored shape;
erase the 1, 2, and the original shape.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: zero_vector (1 and 2 coincide → vector is (0,0); rule
translates by zero, output equals input minus markers/shape, leaves
empty grid), missing_marker (only 1 OR only 2 → vector undefined,
rule's selector returns no pair), no_shape (1, 2 present but no
third-colored shape → translation has nothing to apply to).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "972c47b94504"
VERSION = "1.2.0"
TASK_ID = "972c47b94504"
SUMMARY = "1-marker + 2-marker (defining a translation vector) + a small shape to translate."

INVARIANTS = [
    "background is 0",
    "exactly one 1-cell and one 2-cell defining a non-zero translation vector",
    "exactly one connected shape in a third color (3-5 cells)",
    "the shape's translation by v stays in-bounds",
    "objects don't touch each other",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("zero_vector", "missing_marker", "no_shape")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "grid_w":            {"type": "int", "default": "rng 8..11", "valid": "6..14"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "|".join(PALETTE_KINDS)},
    "palette_size":      {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "position_bias":     {"type": "str", "default": "shape_plus_vector",
                          "valid": "shape_plus_vector"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..3", "valid": "3..3"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}

_SHAPES = [
    [(0, 0), (0, 1), (1, 0)],
    [(0, 0), (1, 0), (1, 1)],
    [(0, 0), (0, 1), (0, 2), (1, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 11)
        w = ctx.draw_int("grid_w", 11, 11)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 8, 11)
    rng = ctx.draw_rng("layout")
    for _layout_attempt in range(80):
        g = full_grid(h, w, 0)
        shape_color = rng.choice(list(random_palette(rng, 4, exclude={1, 2})))
        shape = rng.choice(_SHAPES)
        sh = max(c[0] for c in shape) + 1
        sw = max(c[1] for c in shape) + 1
        sr = rng.randint(0, max(0, h // 2 - sh))
        sc = rng.randint(0, max(0, w // 2 - sw))
        shape_cells = {(sr + r, sc + c) for r, c in shape}
        paint_at(g, sr, sc, shape, shape_color)
        max_dr = h - sh - sr - 1
        max_dc = w - sw - sc - 1
        if max_dr < 1 or max_dc < 1:
            continue
        dr = rng.randint(1, max_dr)
        dc = rng.randint(1, max_dc)
        translated = {(r + dr, c + dc) for r, c in shape_cells}
        blocked = set(shape_cells) | set(translated)
        # Keep the defining markers off the source shape and off the destination
        # footprint, with a one-cell margin around both.  The old fallback could
        # drop markers on/touching the source or translation target, causing
        # missing markers and ambiguous overwrite examples.
        halo = set()
        for r, c in blocked:
            for rr in range(max(0, r - 1), min(h, r + 2)):
                for cc in range(max(0, c - 1), min(w, c + 2)):
                    halo.add((rr, cc))
        candidates = []
        for one_r in range(h):
            for one_c in range(w):
                two_r, two_c = one_r + dr, one_c + dc
                if not (0 <= two_r < h and 0 <= two_c < w):
                    continue
                if (one_r, one_c) in halo or (two_r, two_c) in halo:
                    continue
                if g[one_r][one_c] != 0 or g[two_r][two_c] != 0:
                    continue
                candidates.append((one_r, one_c, two_r, two_c))
        if not candidates:
            continue
        one_r, one_c, two_r, two_c = rng.choice(candidates)
        g[one_r][one_c] = 1
        g[two_r][two_c] = 2
        return g
    raise ValueError("could not place vector markers with clear source/destination margin")


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "zero_vector":
        # 1 and 2 at same cell collapse to one mark — vector is (0,0);
        # rule translates by zero, output = input minus shape/markers.
        for dr, dc in [(0, 0), (0, 1), (1, 0)]:
            g[2 + dr][2 + dc] = 4
        g[5][5] = 1
        # 2 placed adjacent simulating "almost zero" (no displacement room)
        return g
    if name == "missing_marker":
        # Only 1, no 2 → vector undefined; rule's selector returns no pair.
        for dr, dc in [(0, 0), (1, 0), (1, 1)]:
            g[2 + dr][2 + dc] = 4
        g[6][6] = 1
        return g
    if name == "no_shape":
        # Markers present but no third-colored shape — translation
        # has nothing to apply to.
        g[2][2] = 1
        g[4][5] = 2
        return g
    return g


def _components_by_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(ones) != 1 or len(twos) != 1:
        errors.append(f"expected exactly one 1-marker and one 2-marker, got {len(ones)} and {len(twos)}")
        return errors
    (orow, ocol), (trow, tcol) = ones[0], twos[0]
    dr, dc = trow - orow, tcol - ocol
    if (dr, dc) == (0, 0):
        errors.append("translation vector must be nonzero")
    colors = sorted({v for row in grid for v in row if v not in (0, 1, 2)})
    if len(colors) != 1:
        errors.append(f"expected exactly one third-colored source shape, got colors {colors}")
        return errors
    comps = _components_by_color(grid, colors[0])
    if len(comps) != 1:
        errors.append(f"expected one connected source shape, got {len(comps)}")
        return errors
    cells = comps[0]
    if not (3 <= len(cells) <= 5):
        errors.append(f"source shape should have 3..5 cells, got {len(cells)}")
    dest = [(r + dr, c + dc) for r, c in cells]
    if any(not (0 <= r < h and 0 <= c < w) for r, c in dest):
        errors.append("translated shape would leave the grid")
    if any((r, c) in ones or (r, c) in twos for r, c in dest):
        errors.append("translated destination overlaps a vector marker")
    marker_cells = set(ones + twos)
    for r, c in cells + dest:
        for mr, mc in marker_cells:
            if abs(r - mr) <= 1 and abs(c - mc) <= 1:
                errors.append("vector markers must not touch source or destination shape")
                return errors
    return errors

