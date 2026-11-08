"""Generator for arc_puzzle_bank_eleventh21:E73.

Rule: fill a zero center surrounded by four same-color diagonal cells.

Combinatorial axes (8): grid_h, grid_w, palette_kind, motifs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_xs, mixed_corner_colors, center_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "63d542bfcb82"
VERSION = "1.3.0"
TASK_ID = "63d542bfcb82"
SUMMARY = "Fill a zero center surrounded by four same-color diagonal cells."

INVARIANTS = [
    "background is 0",
    "each active center has four same-color diagonal neighbors",
    "active centers are initially zero",
    "X motifs are isolated",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_xs", "mixed_corner_colors", "center_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "motifs":         {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spaced_xs",
                       "valid": "spaced_xs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _clear(g, r, c):
    h, w = len(g), len(g[0])
    for rr in range(max(0, r - 2), min(h, r + 3)):
        for cc in range(max(0, c - 2), min(w, c + 3)):
            if g[rr][cc] != 0:
                return False
    return True


def _choose_centers(h, w, target, rng):
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    for _attempt in range(50):
        g = full_grid(h, w, 0)
        rng.shuffle(candidates)
        out = []
        for r, c in candidates:
            if len(out) >= target:
                return out
            if not _clear(g, r, c):
                continue
            out.append((r, c))
            for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                g[r + dr][c + dc] = 1
    fallback = [(1, 1), (1, 5), (5, 1), (5, 5)]
    valid = [(r, c) for r, c in fallback if 1 <= r < h - 1 and 1 <= c < w - 1]
    if len(valid) >= target:
        return valid[:target]
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 7)
        w = ctx.draw_int("grid_w", 8, 8)
        target = ctx.draw_int("motifs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        target = ctx.draw_int("motifs", 3, 3)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        target = ctx.draw_int("motifs", 2, 3)
    rng = ctx.draw_rng("layout")
    centers = _choose_centers(h, w, target, rng)
    if centers is None:
        raise ValueError("could not place isolated X motifs")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], len(centers))
    for (r, c), color in zip(centers, colors):
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            g[r + dr][c + dc] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_xs":
        # blank grid → no diagonal-X patterns to detect, rule is identity
        return g
    if name == "mixed_corner_colors":
        # 4 diagonal corners with mixed colors → predicate "all same color" fails
        for (r, c, col) in [(2, 2, 4), (2, 4, 6), (4, 2, 4), (4, 4, 4)]: g[r][c] = col
        return g
    if name == "center_filled":
        # center already non-zero → predicate "center is 0" fails, rule does nothing
        for (r, c) in [(2, 2), (2, 4), (4, 2), (4, 4)]: g[r][c] = 4
        g[3][3] = 8   # center already filled
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    centers = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] != 0:
                continue
            vals = [grid[r - 1][c - 1], grid[r - 1][c + 1],
                    grid[r + 1][c - 1], grid[r + 1][c + 1]]
            if vals[0] != 0 and all(v == vals[0] for v in vals):
                centers.append((r, c))
    want = 3 if difficulty == "hard" else 2
    if len(centers) < want:
        errors.append("too few active diagonal-X motifs")
    for i, a in enumerate(centers):
        for b in centers[i + 1:]:
            if abs(a[0] - b[0]) <= 2 and abs(a[1] - b[1]) <= 2:
                errors.append("X motifs are not isolated")
    return errors
