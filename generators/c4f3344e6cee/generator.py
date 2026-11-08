"""Generator for d22278a0.

Rule: voronoi-style fill where parity of dist works; for each cell,
find nearest marker by Chebyshev distance.

Combinatorial axes (8): grid_h/w, n_markers, palette_kind, marker_position,
anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: no_markers, full_grid, single_cell.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c4f3344e6cee"
VERSION = "1.1.1"
TASK_ID = "c4f3344e6cee"
SUMMARY = "Sparse single-cell markers (1-3) at distinct corners or edges of grid."

INVARIANTS = [
    "1-3 single non-zero cells",
    "markers at distinct positions, each at corner or near-corner",
]

POSITION_BIASES = ("corners", "edges", "scattered", "rng")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_markers", "full_grid", "single_cell")
HELPFUL_TEXTURES = POSITION_BIASES

AXES = {
    "grid_h":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "grid_w":         {"type": "int", "default": "rng 11..14", "valid": "9..18"},
    "n_markers":      {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "palette_kind":   {"type": "str", "default": "rng",
                       "valid": "|".join(PALETTE_KINDS)},
    "marker_position":{"type": "str", "default": "rng helpful",
                       "valid": "|".join(POSITION_BIASES)},
    "anchor_corner":  {"type": "bool", "default": "true",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "rng 1..3", "valid": "1..4"},
    "texture":        {"type": "str", "default": "alias for marker_position",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h_lo, h_hi = 9, 11
        nm_lo, nm_hi = 1, 2
    elif difficulty == "hard":
        h_lo, h_hi = 14, 18
        nm_lo, nm_hi = 3, 4
    else:
        h_lo, h_hi = 11, 14
        nm_lo, nm_hi = 1, 3
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    g = full_grid(h, w, 0)
    n_markers = int(overrides.get("n_markers",
                                  ctx.draw_int("n_markers", nm_lo, nm_hi)))
    n_markers = max(1, min(4, n_markers))
    palette_kind = overrides.get("palette_kind",
                                 ctx.draw_choice("palette_kind",
                                                 list(PALETTE_KINDS)))
    pal = _build_palette(palette_kind, n_markers, rng)
    bias = (overrides.get("texture") or
            overrides.get("marker_position")
            or ctx.draw_choice("marker_position", list(POSITION_BIASES)))
    if bias == "edges":
        candidates = ([(0, c) for c in range(w)] +
                      [(h - 1, c) for c in range(w)] +
                      [(r, 0) for r in range(1, h - 1)] +
                      [(r, w - 1) for r in range(1, h - 1)])
    elif bias == "corners":
        candidates = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    elif bias == "scattered":
        candidates = [(r, c) for r in range(h) for c in range(w)]
    else:
        candidates = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    chosen = rng.sample(candidates, min(n_markers, len(candidates)))
    for (r, c), color in zip(chosen, pal):
        g[r][c] = color
    return g


def _build_palette(kind, n, rng):
    if kind == "warm":
        pool = [2, 3, 4, 6, 9]
    elif kind == "cool":
        pool = [1, 5, 7, 8]
    elif kind == "primary":
        pool = [1, 2, 3, 4]
    else:
        pool = [1, 2, 3, 4, 6, 7, 8, 9]
    rng.shuffle(pool)
    if len(pool) < n:
        for c in [1, 2, 3, 4, 5, 6, 7, 8, 9]:
            if c not in pool:
                pool.append(c)
            if len(pool) >= n:
                break
    return pool[:n]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """1-3 single nonzero marker cells; grid is mostly background."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    nonzero = sum(grid[r][c] != 0 for r in range(h) for c in range(w))
    if nonzero == 0:
        errors.append("no marker cells found")
    elif nonzero > 4:
        errors.append(f"expected 1-4 marker cells, found {nonzero}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 12, 12
    g = full_grid(h, w, 0)
    if name == "no_markers":
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 2
        return g
    if name == "single_cell":
        g[h // 2][w // 2] = 2
        return g
    return g
