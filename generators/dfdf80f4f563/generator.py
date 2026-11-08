"""Generator for arc_puzzle_bank_fifth21:E30.

Rule: each isolated T-shape's degree-3 center cell is highlighted.

Combinatorial axes (8): grid_h, grid_w, palette_kind, t_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_t_shapes, plus_instead_of_t, t_shapes_touching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dfdf80f4f563"
VERSION = "1.3.0"  # clean (T-shape center with 3 same neighbors -> 8) but small (7x7-9x10, 2-3 shapes). Widen grids (up to 14x16) and t_shapes (3-5 default, 5-8 hard).
TASK_ID = "dfdf80f4f563"

SUMMARY = "Place isolated T-shapes whose degree-3 centers are highlighted."

INVARIANTS = [
    "background is 0",
    "active objects are isolated same-color T-shapes",
    "each T center has exactly three cardinal same-color neighbors",
    "T footprints do not touch",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_t_shapes", "plus_instead_of_t", "t_shapes_touching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "t_shapes":       {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_t_shapes",
                       "valid": "spaced_t_shapes"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 9)
        target = ctx.draw_int("t_shapes", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        target = ctx.draw_int("t_shapes", 5, 8)
    else:
        h = ctx.draw_int("grid_h", 8, 11)
        w = ctx.draw_int("grid_w", 9, 12)
        target = ctx.draw_int("t_shapes", 3, 5)
    rng = ctx.draw_rng("layout")
    return _draw_t_layout(h, w, target, rng)


def _t_cells(r, c, missing):
    arms = [d for d in _DIRS if d != missing]
    return {(r, c)} | {(r + dr, c + dc) for dr, dc in arms}


def _guard_for(cells, h, w):
    guard = set(cells)
    for r, c in list(cells):
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                guard.add((nr, nc))
    return guard


def _try_place_t(g, reserved, r, c, missing, color):
    h, w = len(g), len(g[0])
    cells = _t_cells(r, c, missing)
    if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in cells):
        return False
    guard = _guard_for(cells, h, w)
    if guard & reserved:
        return False
    for rr, cc in cells:
        g[rr][cc] = color
    reserved.update(guard)
    return True


def _draw_t_layout(h, w, target, rng):
    colors = [1, 2, 3, 4, 5, 6, 7, 9]
    # If the requested hard count does not fit a small random canvas, grow a
    # deterministic fallback canvas rather than silently emitting too few T's.
    for grow in range(4):
        hh = max(h, h + grow * 2, 5)
        ww = max(w, w + grow * 2, 5)
        g = full_grid(hh, ww, 0)
        reserved: set[tuple[int, int]] = set()
        placed = 0
        for _ in range(1600):
            if placed >= target:
                return g
            r = rng.randint(1, hh - 2)
            c = rng.randint(1, ww - 2)
            if _try_place_t(g, reserved, r, c, rng.choice(_DIRS), rng.choice(colors)):
                placed += 1
        for r in range(1, hh - 1):
            for c in range(1, ww - 1):
                for missing in _DIRS:
                    if placed >= target:
                        return g
                    if _try_place_t(g, reserved, r, c, missing, colors[placed % len(colors)]):
                        placed += 1
    raise ValueError(f"could not place {target} isolated T-shapes")



def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    expected = {"easy": (2, 3), "hard": (5, 8)}.get(difficulty, (3, 5))
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            v = grid[r][c]
            if v == 0:
                continue
            same = [(r + dr, c + dc) for dr, dc in _DIRS if grid[r + dr][c + dc] == v]
            if len(same) == 3:
                centers.append((r, c, v))
    if not (expected[0] <= len(centers) <= expected[1]):
        errors.append(f"expected {expected[0]}-{expected[1]} T centers, got {len(centers)}")
    # Every non-zero cell should belong to exactly one highlighted T footprint.
    covered = set()
    for r, c, v in centers:
        cells = {(r, c)} | {(rr, cc) for rr, cc in ((r + dr, c + dc) for dr, dc in _DIRS) if grid[rr][cc] == v}
        if len(cells) != 4:
            errors.append(f"center {(r, c)} has malformed T footprint")
        covered |= cells
    nz = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    if nz - covered:
        errors.append(f"{len(nz - covered)} nonzero cells are not in any T footprint")
    return errors

def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_t_shapes":
        # blank → no T-shapes, rule has no center to highlight
        return g
    if name == "plus_instead_of_t":
        # full plus shape (degree-4 center) → predicate "exactly 3 neighbors" fails
        for (r, c) in [(2, 3), (1, 3), (3, 3), (2, 2), (2, 4)]: g[r][c] = 4
        for (r, c) in [(5, 6), (4, 6), (6, 6), (5, 5), (5, 7)]: g[r][c] = 6
        return g
    if name == "t_shapes_touching":
        # adjacent T-shapes → centers have >3 same-color neighbors via merge, predicate fails
        for (r, c) in [(2, 3), (1, 3), (3, 3), (2, 2)]: g[r][c] = 4  # T missing right arm
        for (r, c) in [(2, 4), (1, 4), (3, 4)]: g[r][c] = 4  # second T touching, same color
        return g
    return g
